"""Observa mudanças de arquivo e as normaliza antes de emitir eventos."""

from __future__ import annotations

from pathlib import Path
from threading import RLock
from time import monotonic

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from devtools.config import CONFIG
from devtools.events import EVENTS
from devtools.logger import Logger


class ProjectWatcher(FileSystemEventHandler):
    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self.project_root = project_root.resolve()
        self._last_event: dict[Path, float] = {}
        self._lock = RLock()

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory or event.event_type not in {"modified", "created", "moved", "deleted"}:
            return
        raw_path = getattr(event, "dest_path", None) if event.event_type == "moved" else event.src_path
        path = Path(raw_path).resolve(strict=False)
        if not self._should_handle(path):
            return
        now = monotonic()
        with self._lock:
            previous = self._last_event.get(path)
            if previous is not None and now - previous < CONFIG.debounce_time:
                return
            self._last_event[path] = now
        EVENTS.emit("file_changed", path, event.event_type)

    def _should_handle(self, path: Path) -> bool:
        try:
            relative = path.relative_to(self.project_root)
        except ValueError:
            return False
        return CONFIG.should_watch(relative)


class FileWatcher:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.observer: Observer | None = None
        self.running = False

    def start(self) -> bool:
        if self.running:
            return False
        observer = Observer()
        observer.schedule(ProjectWatcher(self.project_root), str(self.project_root), recursive=True)
        try:
            observer.start()
        except OSError as error:
            Logger.error(f"Não foi possível iniciar o watcher: {error}")
            return False
        self.observer = observer
        self.running = True
        Logger.success("Watcher iniciado.")
        return True

    def stop(self) -> None:
        if not self.running or self.observer is None:
            return
        observer = self.observer
        self.running = False
        self.observer = None
        observer.stop()
        observer.join(timeout=3)
        Logger.success("Watcher encerrado.")
