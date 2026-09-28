"""Catálogo local de extensões submetidas, aprovadas e instaladas."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4


class ExtensionsService:
    """Mantém extensões na pasta de dados do usuário, fora do repositório."""

    MAX_SIZE = 2 * 1024 * 1024

    def __init__(self, path: str | Path | None = None) -> None:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        self.root = Path(path).parent if path else base / "PM-Painel"
        self.path = Path(path) if path else self.root / "extensions.json"
        self.inbox = self.root / "extensions" / "catalog"
        self.installed_dir = self.root / "extensions" / "installed"
        self._items: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            values = payload.get("extensions", []) if isinstance(payload, dict) else []
            self._items = [item for item in values if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError, TypeError):
            self._items = []

    def list_extensions(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._items]

    def submit(
        self,
        name: str,
        version: str,
        description: str,
        source: str | Path,
        author: str,
        requires_network: bool = False,
    ) -> dict[str, Any]:
        source_path = Path(source)
        if source_path.suffix.casefold() != ".py" or not source_path.is_file():
            raise ValueError("Selecione um arquivo de extensão Python (.py).")
        if source_path.stat().st_size > self.MAX_SIZE:
            raise ValueError("A extensão deve ter no máximo 2 MB.")
        if not name.strip() or not version.strip():
            raise ValueError("Informe o nome e a versão da extensão.")
        ident = uuid4().hex
        self.inbox.mkdir(parents=True, exist_ok=True)
        destination = self.inbox / f"{ident}_{source_path.name}"
        shutil.copy2(source_path, destination)
        item = {
            "id": ident,
            "name": name.strip(),
            "version": version.strip(),
            "description": description.strip(),
            "author": author.strip() or "Usuário",
            "source_path": str(destination),
            "installed_path": "",
            "status": "pendente",
            "requires_network": bool(requires_network),
        }
        self._items.append(item)
        self._persist()
        return dict(item)

    def approve(self, extension_id: str, reviewer: str) -> dict[str, Any]:
        item = self._find(extension_id)
        if item["status"] != "pendente":
            raise ValueError("Esta extensão não está aguardando aprovação.")
        item["status"] = "aprovada"
        item["approved_by"] = reviewer
        self._persist()
        return dict(item)

    def install(self, extension_id: str, *, online: bool) -> dict[str, Any]:
        item = self._find(extension_id)
        if item["status"] not in {"aprovada", "instalada"}:
            raise ValueError("A extensão precisa ser aprovada por um professor ou moderador.")
        if item.get("requires_network", False) and not online:
            raise ConnectionError("Conecte-se à internet para instalar uma extensão do catálogo.")
        source = Path(item["source_path"])
        if not source.is_file():
            raise FileNotFoundError("O arquivo desta extensão não está disponível no catálogo local.")
        self.installed_dir.mkdir(parents=True, exist_ok=True)
        destination = self.installed_dir / f"{item['id']}_{source.name.split('_', 1)[-1]}"
        shutil.copy2(source, destination)
        item["installed_path"] = str(destination)
        item["status"] = "instalada"
        self._persist()
        return dict(item)

    def execute(self, extension_id: str) -> int:
        item = self._find(extension_id)
        if item["status"] != "instalada":
            raise ValueError("Instale a extensão antes de executá-la.")
        script = Path(item.get("installed_path") or "")
        if not script.is_file():
            raise FileNotFoundError("O arquivo instalado não está mais disponível.")
        process = subprocess.Popen(
            [sys.executable, "-I", str(script)],
            cwd=str(script.parent),
            shell=False,
        )
        return process.pid

    def _find(self, extension_id: str) -> dict[str, Any]:
        item = next((entry for entry in self._items if entry.get("id") == extension_id), None)
        if item is None:
            raise KeyError("Extensão não encontrada.")
        return item

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"versao": 1, "extensions": self._items}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)
