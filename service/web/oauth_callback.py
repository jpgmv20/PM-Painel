"""Servidor local que recebe o retorno do Google sem abrir o navegador padrão."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Thread
from typing import Optional
from urllib.parse import parse_qs, urlparse


class OAuthCallbackServer:
    """Aguarda uma única resposta OAuth no endereço de retorno local."""

    def __init__(self) -> None:
        self._completed = Event()
        self._authorization_response: Optional[str] = None
        self._error: Optional[str] = None
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._create_handler())
        self._thread = Thread(target=self._server.serve_forever, daemon=True)

    @property
    def redirect_uri(self) -> str:
        """URL local registrada no pedido de autorização."""
        host, port = self._server.server_address
        # O cliente OAuth instalado foi cadastrado para localhost, não 127.0.0.1.
        return f"http://localhost:{port}/oauth2/callback"

    def __enter__(self) -> "OAuthCallbackServer":
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)

    def wait_for_response(self, timeout: float = 600) -> str:
        """Entrega a URL completa recebida depois que o usuário autoriza o acesso."""
        if not self._completed.wait(timeout):
            raise TimeoutError("O tempo para concluir o login expirou.")
        if self._error:
            raise RuntimeError(self._error)
        if self._authorization_response is None:
            raise RuntimeError("O retorno do Google não trouxe os dados de autorização.")
        return self._authorization_response

    def _create_handler(self) -> type[BaseHTTPRequestHandler]:
        callback_server = self

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - exigido pela biblioteca padrão
                query = parse_qs(urlparse(self.path).query)
                if query.get("error"):
                    message = "O login foi cancelado ou não foi autorizado."
                    callback_server._error = message
                    callback_server._completed.set()
                else:
                    callback_server._authorization_response = (
                        f"{callback_server.redirect_uri}{self.path.partition('?')[1]}"
                        f"{self.path.partition('?')[2]}"
                    )
                    callback_server._completed.set()
                    message = "Login concluído. Você já pode voltar ao PM-Painel."

                body = (
                    "<html><body style='font-family:Segoe UI;text-align:center;padding:64px'>"
                    f"<h2>{message}</h2></body></html>"
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format: str, *_args: object) -> None:
                """Evita que mensagens do servidor apareçam no terminal do painel."""

        return CallbackHandler
