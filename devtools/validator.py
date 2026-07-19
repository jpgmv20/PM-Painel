"""Valida os pré-requisitos antes de abrir o ambiente."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from devtools.config import CONFIG


class ProjectValidator:
    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root).resolve()

    def validate(self) -> tuple[bool, str | None]:
        if not self.project_root.is_dir():
            return False, f"Pasta do projeto não encontrada: {self.project_root}"
        if not CONFIG.main_path.is_file():
            return False, f"Arquivo principal não encontrado: {CONFIG.main_path.name}"
        if importlib.util.find_spec("kivy") is None:
            return False, "Kivy não está instalado no ambiente Python atual."
        return True, None
