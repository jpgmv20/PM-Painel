"""Registro simples, seguro para threads e legível no terminal."""

from __future__ import annotations

from collections import deque
from datetime import datetime
from pathlib import Path
from threading import RLock

from devtools.config import CONFIG


class Logger:
    _lock = RLock()
    _history: deque[str] = deque(maxlen=500)
    _log_file: Path | None = None

    @classmethod
    def setup(cls) -> None:
        if not CONFIG.save_logs:
            return
        CONFIG.logs_path.mkdir(parents=True, exist_ok=True)
        cls._log_file = CONFIG.logs_path / f"{datetime.now():%Y-%m-%d_%H-%M-%S}.log"

    @classmethod
    def _write(cls, level: str, message: object) -> None:
        line = f"[{datetime.now():%d/%m/%Y %H:%M:%S}] [{level}] {message}"
        with cls._lock:
            print(line, flush=True)
            cls._history.append(line)
            if cls._log_file is not None:
                try:
                    with cls._log_file.open("a", encoding="utf-8") as log_file:
                        log_file.write(f"{line}\n")
                except OSError as error:
                    print(f"[LOGGER] Não foi possível gravar o log: {error}", flush=True)

    @classmethod
    def debug(cls, message: object) -> None:
        if CONFIG.enable_debug:
            cls._write("DEBUG", message)

    @classmethod
    def info(cls, message: object) -> None:
        cls._write("INFO", message)

    @classmethod
    def success(cls, message: object) -> None:
        cls._write("SUCCESS", message)

    @classmethod
    def warning(cls, message: object) -> None:
        cls._write("WARNING", message)

    @classmethod
    def error(cls, message: object) -> None:
        cls._write("ERROR", message)

    @classmethod
    def banner(cls) -> None:
        print("\n" + "=" * 60)
        print("                 PM-PAINEL DEV")
        print("          Ambiente de desenvolvimento Kivy")
        print("=" * 60 + "\n", flush=True)

    @classmethod
    def box(cls, title: str, *lines: object) -> None:
        width = 60
        print("\n" + "=" * width)
        print(title.center(width))
        print("=" * width)
        for line in lines:
            print(line)
        print("=" * width + "\n", flush=True)

    @classmethod
    def last(cls, amount: int = 20) -> list[str]:
        with cls._lock:
            return list(cls._history)[-max(0, amount):]
