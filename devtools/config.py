"""Configuração central do ambiente de desenvolvimento."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def _project_root() -> Path:
    """Retorna a pasta do projeto, independentemente do diretório do terminal."""
    return Path(__file__).resolve().parent.parent


@dataclass(slots=True)
class DevelopmentConfig:
    """Opções usadas por ``python dev.py``."""

    project_root: Path = field(default_factory=_project_root)
    main_file: str = "main.py"

    debounce_time: float = 0.35
    restart_delay: float = 0.15
    watch_extensions: tuple[str, ...] = (
        ".py", ".kv", ".json", ".yaml", ".yml", ".ini", ".toml",
    )
    ignored_directories: tuple[str, ...] = (
        ".git", ".idea", ".vscode", ".pytest_cache", ".mypy_cache",
        "__pycache__", "build", "dist", ".venv", "venv", "kivy_venv",
        "site-packages", "logs", ".pm_logs",
    )

    enable_console: bool = True
    console_prompt: str = "PM> "
    enable_plugins: bool = True
    plugins_directory: str = "plugins"
    enable_debug: bool = True
    save_logs: bool = True
    log_directory: str = "logs"

    @property
    def main_path(self) -> Path:
        return self.project_root / self.main_file

    @property
    def plugins_path(self) -> Path:
        return self.project_root / self.plugins_directory

    @property
    def logs_path(self) -> Path:
        return self.project_root / self.log_directory

    def is_ignored_directory(self, name: str) -> bool:
        return name.casefold() in {item.casefold() for item in self.ignored_directories}

    def should_watch(self, path: Path) -> bool:
        """Informa se um caminho relativo ao projeto deve disparar uma recarga."""
        if path.suffix.casefold() not in self.watch_extensions:
            return False
        return not any(self.is_ignored_directory(part) for part in path.parts)


CONFIG = DevelopmentConfig()
