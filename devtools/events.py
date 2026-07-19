"""Barramento de eventos isolado para o processo do DevTools."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from threading import RLock

from devtools.logger import Logger


class EventBus:
    def __init__(self) -> None:
        self._listeners: defaultdict[str, list[Callable]] = defaultdict(list)
        self._lock = RLock()

    def on(self, event_name: str, callback: Callable) -> Callable:
        with self._lock:
            if callback not in self._listeners[event_name]:
                self._listeners[event_name].append(callback)
                Logger.debug(f"Listener registrado: {event_name}")
        return callback

    def off(self, event_name: str, callback: Callable) -> None:
        with self._lock:
            listeners = self._listeners.get(event_name, [])
            if callback in listeners:
                listeners.remove(callback)
            if not listeners:
                self._listeners.pop(event_name, None)

    def emit(self, event_name: str, *args: object, **kwargs: object) -> None:
        Logger.debug(f"Evento emitido: {event_name}")
        with self._lock:
            callbacks = tuple(self._listeners.get(event_name, ()))
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as error:  # Um plugin não pode derrubar o ambiente.
                Logger.error(f"Erro no listener '{event_name}': {error}")

    def clear(self) -> None:
        with self._lock:
            self._listeners.clear()

    def remove_module_listeners(self, module_name: str) -> None:
        """Remove callbacks criados por um plugin que será descarregado."""
        with self._lock:
            for event_name, callbacks in tuple(self._listeners.items()):
                kept = [
                    callback
                    for callback in callbacks
                    if getattr(callback, "__module__", None) != module_name
                ]
                if kept:
                    self._listeners[event_name] = kept
                else:
                    self._listeners.pop(event_name, None)

    def listener_count(self, event_name: str | None = None) -> int:
        with self._lock:
            if event_name is None:
                return sum(map(len, self._listeners.values()))
            return len(self._listeners.get(event_name, ()))


EVENTS = EventBus()
