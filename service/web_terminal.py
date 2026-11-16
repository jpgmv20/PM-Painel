"""Janela xterm.js local e protegida para os laboratórios Docker."""
from __future__ import annotations

import atexit
import asyncio
import hmac
import json
import mimetypes
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from websockets.asyncio.server import serve

from service.network_lab_docker import DockerLabError


class TerminalWebServer:
    """Serve a UI local e cria uma sessão TTY isolada por painel de terminal."""

    def __init__(self, docker_lab):
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        self.assets = (base / "assets" / "web-terminal").resolve()
        self.token = secrets.token_urlsafe(32)
        self.http_port = 0
        self.websocket_port = 0
        self.url = ""
        self._docker_lab = docker_lab
        self._docker_lab_lock = threading.Lock()
        self._http_server = None
        self._http_thread = None
        self._loop = None
        self._websocket_server = None
        self._websocket_thread = None
        self._ready = threading.Event()
        self._startup_error = None
        self._started = False
        self._stopped = False

    def set_docker_lab(self, docker_lab):
        """Permite reutilizar a janela e o servidor ao reabrir a atividade."""
        with self._docker_lab_lock:
            self._docker_lab = docker_lab

    def start(self):
        if self._started:
            return self.url
        if not (self.assets / "index.html").is_file():
            raise RuntimeError("A interface xterm.js não foi incluída nesta instalação.")

        handler = self._make_http_handler()
        self._http_server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self._http_server.daemon_threads = True
        self._http_server.block_on_close = False
        self.http_port = self._http_server.server_address[1]
        self._http_thread = threading.Thread(
            target=self._http_server.serve_forever,
            name="pm-painel-terminal-http",
            daemon=True,
        )
        self._http_thread.start()

        self._websocket_thread = threading.Thread(
            target=self._run_websocket_server,
            name="pm-painel-terminal-ws",
            daemon=True,
        )
        self._websocket_thread.start()
        if not self._ready.wait(5):
            self.stop()
            raise RuntimeError("O servidor do terminal não iniciou a tempo.")
        if self._startup_error:
            self.stop()
            raise RuntimeError(f"Não foi possível iniciar o terminal web: {self._startup_error}")

        self.url = (
            f"http://127.0.0.1:{self.http_port}/{self.token}/"
            f"?ws_port={self.websocket_port}"
        )
        self._started = True
        atexit.register(self.stop)
        return self.url

    def stop(self):
        if self._stopped:
            return
        self._stopped = True

        if self._loop is not None and self._websocket_server is not None:
            async def close_websockets():
                self._websocket_server.close()
                await self._websocket_server.wait_closed()

            try:
                future = asyncio.run_coroutine_threadsafe(close_websockets(), self._loop)
                future.result(timeout=4)
            except Exception:
                pass
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._websocket_thread is not None:
            self._websocket_thread.join(timeout=2)

        if self._http_server is not None:
            self._http_server.shutdown()
            self._http_server.server_close()
        if self._http_thread is not None:
            self._http_thread.join(timeout=2)

        with self._docker_lab_lock:
            docker_lab = self._docker_lab
        if docker_lab is not None:
            docker_lab.close_terminals()

    def _make_http_handler(self):
        assets = self.assets
        token = self.token
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                return

            def do_GET(self):
                request = urlsplit(self.path)
                prefix = f"/{token}/"
                if not request.path.startswith(prefix):
                    self.send_error(404)
                    return
                relative = unquote(request.path[len(prefix):]) or "index.html"
                target = (assets / relative).resolve()
                try:
                    target.relative_to(assets)
                except ValueError:
                    self.send_error(404)
                    return
                if not target.is_file():
                    self.send_error(404)
                    return
                payload = target.read_bytes()
                content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                    f"connect-src 'self' ws://127.0.0.1:{owner.websocket_port}; "
                    "img-src 'self' data:; font-src 'self' data:",
                )
                self.end_headers()
                self.wfile.write(payload)

        return Handler

    def _run_websocket_server(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            async def start_server():
                origin = f"http://127.0.0.1:{self.http_port}"
                self._websocket_server = await serve(
                    self._handle_connection,
                    "127.0.0.1",
                    0,
                    origins=[origin],
                    compression=None,
                    max_size=1_048_576,
                    ping_interval=20,
                    ping_timeout=20,
                )
                self.websocket_port = self._websocket_server.sockets[0].getsockname()[1]

            self._loop.run_until_complete(start_server())
            self._ready.set()
            self._loop.run_forever()
        except Exception as error:
            self._startup_error = error
            self._ready.set()
        finally:
            if self._loop.is_running():
                self._loop.stop()
            try:
                self._loop.close()
            except Exception:
                pass

    async def _handle_connection(self, websocket):
        request = getattr(websocket, "request", None)
        request_path = getattr(request, "path", "")
        query = parse_qs(urlsplit(request_path).query)
        supplied_token = (query.get("token") or [""])[0]
        if not hmac.compare_digest(supplied_token, self.token):
            await websocket.close(code=1008, reason="Token inválido")
            return

        loop = asyncio.get_running_loop()
        output_queue = asyncio.Queue()
        send_lock = asyncio.Lock()
        session = None
        output_task = None

        async def send(payload):
            async with send_lock:
                await websocket.send(json.dumps(payload, ensure_ascii=False))

        async def forward_output():
            while True:
                chunk = await output_queue.get()
                if chunk is None:
                    await send({"type": "closed"})
                    await websocket.close(code=1000, reason="Sessão de terminal encerrada")
                    return
                await send({"type": "output", "data": chunk.decode("utf-8", errors="replace")})

        try:
            async for raw_message in websocket:
                try:
                    message = json.loads(raw_message)
                except (TypeError, ValueError):
                    await send({"type": "error", "message": "Mensagem inválida."})
                    continue

                action = message.get("type")
                if action == "open" and session is None:
                    key = str(message.get("terminal", ""))
                    if key not in {"A", "B"}:
                        await send({"type": "error", "message": "Terminal desconhecido."})
                        await websocket.close(code=1008, reason="Terminal desconhecido")
                        return
                    with self._docker_lab_lock:
                        docker_lab = self._docker_lab
                    try:
                        session = docker_lab.abrir_terminal(
                            key,
                            cols=docker_lab._limitar_colunas(message.get("cols", 100)),
                            rows=docker_lab._limitar_linhas(message.get("rows", 28)),
                        )
                    except (DockerLabError, TypeError, ValueError) as error:
                        await send({"type": "error", "message": str(error)})
                        await websocket.close(code=1011, reason="Não foi possível abrir o Bash")
                        return

                    await send({"type": "ready", "terminal": key})

                    def receive_output():
                        try:
                            while True:
                                chunk = session.read()
                                if not chunk:
                                    break
                                loop.call_soon_threadsafe(output_queue.put_nowait, chunk)
                        except Exception:
                            pass
                        finally:
                            try:
                                loop.call_soon_threadsafe(output_queue.put_nowait, None)
                            except RuntimeError:
                                pass

                    threading.Thread(
                        target=receive_output,
                        name=f"pm-painel-xterm-{key.lower()}",
                        daemon=True,
                    ).start()
                    output_task = asyncio.create_task(forward_output())
                elif action == "input" and session is not None:
                    data = message.get("data", "")
                    if isinstance(data, str) and len(data) <= 262_144:
                        try:
                            session.write(data.encode("utf-8"))
                        except (DockerLabError, OSError):
                            await send({"type": "error", "message": "A sessão perdeu a conexão com o container."})
                            await websocket.close(code=1011, reason="Conexão Docker encerrada")
                            return
                elif action == "resize" and session is not None:
                    try:
                        cols = int(message.get("cols", 100))
                        rows = int(message.get("rows", 28))
                        session.resize(
                            docker_lab._limitar_colunas(cols),
                            docker_lab._limitar_linhas(rows),
                        )
                    except Exception:
                        # Um redimensionamento não deve derrubar um terminal ativo.
                        pass
        except Exception:
            pass
        finally:
            if session is not None:
                try:
                    session.close()
                except Exception:
                    pass
            if output_task is not None:
                output_task.cancel()
                await asyncio.gather(output_task, return_exceptions=True)
