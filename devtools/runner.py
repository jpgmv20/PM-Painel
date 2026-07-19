"""Coordenador do processo Kivy, watcher, plugins e console."""

from __future__ import annotations

from pathlib import Path
from threading import RLock, Timer
from time import sleep

from devtools.commands import CommandManager
from devtools.config import CONFIG
from devtools.console import DevelopmentConsole
from devtools.events import EVENTS
from devtools.hotreload import HotReloadManager
from devtools.logger import Logger
from devtools.plugins import PluginManager
from devtools.process import ProcessManager
from devtools.profiler import Profiler
from devtools.state import DevelopmentState
from devtools.validator import ProjectValidator
from devtools.watcher import FileWatcher


class DevelopmentRunner:
    def __init__(self) -> None:
        self.project_root = CONFIG.project_root.resolve()
        self.main_file = CONFIG.main_path.resolve()
        self.running = False
        self._shutdown_lock = RLock()
        self._restart_lock = RLock()
        self._restart_timer: Timer | None = None
        self._pending_file: Path | None = None
        self.state = DevelopmentState()
        self.state.project_root = self.project_root
        self.state.main_file = self.main_file
        self.validator = ProjectValidator(self.project_root)
        self.profiler = Profiler()
        self.process = ProcessManager(self.main_file, self.project_root, self.state)
        self.watcher = FileWatcher(self.project_root)
        self.plugins = PluginManager(self.project_root, self)
        self.hotreload = HotReloadManager(self)
        self.commands = CommandManager(self)
        self.console = DevelopmentConsole(self.commands)

    def start(self) -> bool:
        ok, error = self.validator.validate()
        if not ok:
            Logger.error(error or "Projeto inválido.")
            return False
        self.running = True
        self.profiler.start()
        self.commands.register_default()
        self.plugins.load_all()
        self.hotreload.start()
        if not self.process.start():
            self.shutdown()
            return False
        self.watcher.start()
        self.console.start()
        self.profiler.finish_startup(self.state)
        EVENTS.emit("app_started", self)
        Logger.success("Ambiente iniciado.")
        self._loop()
        return True

    def _loop(self) -> None:
        try:
            while self.running:
                if not self.process.running() and not self._restart_pending():
                    Logger.warning("A aplicação foi encerrada.")
                    break
                sleep(0.2)
        except KeyboardInterrupt:
            Logger.info("Interrupção recebida.")
        finally:
            self.shutdown()

    def request_restart(self, file: Path | None, reason: str, delay: float | None = None) -> None:
        if not self.running:
            return
        if file is not None:
            self.state.register_file_change(file)
        EVENTS.emit("before_reload", file, reason)
        with self._restart_lock:
            self._pending_file = file
            if self._restart_timer is not None:
                self._restart_timer.cancel()
            wait = CONFIG.restart_delay if delay is None else max(0, delay)
            self._restart_timer = Timer(wait, self._restart_application, args=(reason,))
            self._restart_timer.daemon = True
            self._restart_timer.start()
        Logger.info(f"Recarga agendada: {reason}")

    def _restart_application(self, reason: str) -> None:
        with self._restart_lock:
            self._restart_timer = None
            file = self._pending_file
            self._pending_file = None
        if not self.running:
            return
        Logger.info(f"Reiniciando aplicação ({reason}).")
        if self.process.restart():
            self.state.register_hot_reload()
            EVENTS.emit("after_reload", file, reason)

    def _restart_pending(self) -> bool:
        with self._restart_lock:
            return self._restart_timer is not None

    def shutdown(self) -> None:
        with self._shutdown_lock:
            if not self.running:
                return
            self.running = False
            with self._restart_lock:
                if self._restart_timer is not None:
                    self._restart_timer.cancel()
                    self._restart_timer = None
            Logger.info("Encerrando ambiente...")
            self.watcher.stop()
            self.console.stop()
            EVENTS.emit("shutdown")
            self.plugins.unload_all(run_shutdown=False)
            self.process.stop()
            EVENTS.clear()
            Logger.success("Ambiente encerrado.")
