"""Small connectivity check shared by features that need the internet."""

from __future__ import annotations

import socket
import threading
import time


class InternetService:
    """Checks internet reachability without blocking the interface for long."""

    def __init__(self, cache_seconds: float = 4.0) -> None:
        self._cache_seconds = cache_seconds
        self._last_checked = 0.0
        self._last_result = False
        self._lock = threading.Lock()

    def online(self, *, refresh: bool = False) -> bool:
        with self._lock:
            now = time.monotonic()
            if not refresh and now - self._last_checked < self._cache_seconds:
                return self._last_result
            try:
                with socket.create_connection(("8.8.8.8", 53), timeout=0.8):
                    result = True
            except OSError:
                result = False
            self._last_checked = time.monotonic()
            self._last_result = result
            return result

    def require_online(self, *, offline_mode: bool = False, action: str = "Esta ação") -> None:
        if offline_mode or not self.online(refresh=True):
            raise ConnectionError(
                f"{action} precisa de conexão com a internet. "
                "Desative o modo offline e tente novamente quando estiver conectado."
            )
