"""Console opcional que não interfere em execuções sem terminal interativo."""

from __future__ import annotations

import sys
from threading import Thread

from devtools.config import CONFIG
from devtools.logger import Logger


class DevelopmentConsole:
    def __init__(self, commands) -> None:
        self.commands = commands
        self.running = False
        self.thread: Thread | None = None

    def start(self) -> bool:
        if not CONFIG.enable_console or not sys.stdin or not sys.stdin.isatty():
            Logger.debug("Console interativo indisponível nesta execução.")
            return False
        if self.running:
            return False
        self.running = True
        self.thread = Thread(target=self._loop, name="pm-dev-console", daemon=True)
        self.thread.start()
        Logger.success("Console iniciado. Digite 'help' para ver os comandos.")
        return True

    def _loop(self) -> None:
        while self.running:
            try:
                command = input(CONFIG.console_prompt)
            except (EOFError, KeyboardInterrupt):
                break
            self.commands.execute(command)
        self.running = False

    def stop(self) -> None:
        self.running = False
