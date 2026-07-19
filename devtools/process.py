"""Execução e encerramento confiável do processo da aplicação Kivy."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from threading import RLock, Thread

from devtools.logger import Logger


class ProcessManager:
    def __init__(self, main_file: Path, project_root: Path, state) -> None:
        self.main_file = Path(main_file).resolve()
        self.project_root = Path(project_root).resolve()
        self.state = state
        self.process: subprocess.Popen[str] | None = None
        self._lock = RLock()
        self._stdout_thread: Thread | None = None

    def start(self) -> bool:
        with self._lock:
            if self.running():
                return False
            Logger.info(f"Iniciando {self.main_file.name}")
            environment = os.environ.copy()
            environment["PYTHONUNBUFFERED"] = "1"
            try:
                process = subprocess.Popen(
                    [sys.executable, "-u", str(self.main_file)],
                    cwd=str(self.project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    env=environment,
                )
            except OSError as error:
                Logger.error(f"Não foi possível iniciar a aplicação: {error}")
                return False
            self.process = process
            self.state.register_process(process.pid)
            self._stdout_thread = Thread(
                target=self._read_output, args=(process,), name="pm-app-output", daemon=True
            )
            self._stdout_thread.start()
            Logger.success(f"Aplicação iniciada | PID: {process.pid}")
            return True

    def _read_output(self, process: subprocess.Popen[str]) -> None:
        stream = process.stdout
        if stream is None:
            return
        try:
            for line in iter(stream.readline, ""):
                print(line.rstrip(), flush=True)
        except (OSError, ValueError) as error:
            Logger.debug(f"Leitura da saída encerrada: {error}")
        finally:
            stream.close()
            process.wait()
            self.state.stop_process(process.pid)

    def running(self) -> bool:
        with self._lock:
            return self.process is not None and self.process.poll() is None

    def stop(self) -> None:
        with self._lock:
            process = self.process
            self.process = None
        if process is None:
            return
        if process.poll() is None:
            Logger.info("Encerrando aplicação...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                Logger.warning("A aplicação não encerrou a tempo; finalizando processo.")
                process.kill()
                process.wait(timeout=5)
        self.state.stop_process(process.pid)

    def restart(self) -> bool:
        with self._lock:
            self.stop()
            self.state.register_restart()
            return self.start()
