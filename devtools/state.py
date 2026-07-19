"""Estado e métricas compartilhados pelo ambiente de desenvolvimento."""

from __future__ import annotations

from pathlib import Path
from threading import RLock
from time import time


class DevelopmentState:
    def __init__(self) -> None:
        self._lock = RLock()
        self.project_root: Path | None = None
        self.main_file: Path | None = None
        self.process_id: int | None = None
        self.process_running = False
        self.process_start_time: float | None = None
        self.process_restart_count = 0
        self.hot_reload_count = 0
        self.files_changed = 0
        self.last_changed_file: Path | None = None
        self.startup_time = 0.0

    def register_process(self, pid: int) -> None:
        with self._lock:
            self.process_id = pid
            self.process_running = True
            self.process_start_time = time()

    def stop_process(self, pid: int | None = None) -> None:
        with self._lock:
            if pid is not None and pid != self.process_id:
                return
            self.process_running = False
            self.process_id = None
            self.process_start_time = None

    def register_restart(self) -> None:
        with self._lock:
            self.process_restart_count += 1

    def register_file_change(self, file: Path) -> None:
        with self._lock:
            self.files_changed += 1
            self.last_changed_file = Path(file)

    def register_hot_reload(self) -> None:
        with self._lock:
            self.hot_reload_count += 1

    def register_startup(self, seconds: float) -> None:
        with self._lock:
            self.startup_time = seconds

    @property
    def uptime(self) -> float:
        with self._lock:
            return 0.0 if self.process_start_time is None else time() - self.process_start_time

    def as_dict(self) -> dict[str, object]:
        with self._lock:
            return {
                "pid": self.process_id,
                "running": self.process_running,
                "uptime": self.uptime,
                "startup_time": self.startup_time,
                "restarts": self.process_restart_count,
                "reloads": self.hot_reload_count,
                "files_changed": self.files_changed,
                "last_file": str(self.last_changed_file) if self.last_changed_file else None,
            }
