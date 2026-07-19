"""
config.py

Configurações globais do ambiente de desenvolvimento.
"""

from dataclasses import dataclass
from pathlib import Path



@dataclass(slots=True)
class DevelopmentConfig:


    # =====================================================
    # Projeto
    # =====================================================

    project_name: str = "PM-Painel"

    main_file: str = "main.py"

    project_root: Path = Path.cwd()



    # =====================================================
    # Watcher
    # =====================================================

    recursive: bool = True

    debounce: float = 0.60



    # =====================================================
    # Arquivos monitorados
    # =====================================================

    watched_extensions: tuple[str, ...] = (

        ".py",

        ".kv",

        ".json",

        ".yaml",

        ".yml",

        ".ini",

        ".cfg",

        ".txt",

        ".toml",

        ".env",

    )



    # =====================================================
    # Pastas ignoradas
    # =====================================================

    ignored_directories: tuple[str, ...] = (

        "__pycache__",

        ".git",

        ".github",

        ".idea",

        ".vscode",

        ".venv",

        "venv",

        "kivy_venv",

        ".pytest_cache",

        ".mypy_cache",

        ".ruff_cache",

        "build",

        "dist",

        "site-packages",

    )



    # =====================================================
    # Arquivos ignorados
    # =====================================================

    ignored_files: tuple[str, ...] = (

        ".DS_Store",

        "Thumbs.db",

    )



    # =====================================================
    # Processo
    # =====================================================

    restart_delay: float = 0.20

    process_timeout: float = 3.0



    # =====================================================
    # Terminal
    # =====================================================

    clear_console: bool = True

    show_banner: bool = True

    colored_logs: bool = True



    # =====================================================
    # Desenvolvimento
    # =====================================================

    debug: bool = True

    auto_restart: bool = True

    hot_reload: bool = True

    validate_before_restart: bool = True



    # =====================================================
    # Recursos avançados
    # =====================================================

    profile_startup: bool = True

    profile_memory: bool = False

    profile_cpu: bool = False


    enable_plugins: bool = True

    enable_terminal_commands: bool = True



    # =====================================================
    # Funções auxiliares
    # =====================================================

    def is_valid_extension(
        self,
        suffix: str
    ) -> bool:


        return (
            suffix.lower()
            in
            self.watched_extensions
        )



    def is_ignored_directory(
        self,
        name: str
    ) -> bool:


        return (
            name
            in
            self.ignored_directories
        )



    def is_ignored_file(
        self,
        name: str
    ) -> bool:


        return (
            name
            in
            self.ignored_files
        )



# Instância global

CONFIG = DevelopmentConfig()