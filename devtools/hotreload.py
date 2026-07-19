"""Recarga do painel por reinício controlado do processo Kivy.

Kivy executa a interface em outro processo quando iniciado por ``dev.py``.
Por isso, recarregar um arquivo KV no processo do DevTools não atualiza a janela.
O mecanismo correto é reiniciar somente a aplicação após uma breve espera.
"""

from __future__ import annotations

from pathlib import Path

from devtools.config import CONFIG
from devtools.events import EVENTS
from devtools.logger import Logger


class HotReloadManager:
    def __init__(self, runner) -> None:
        self.runner = runner

    def start(self) -> None:
        EVENTS.on("file_changed", self.on_file_changed)
        Logger.success("Recarga automática pronta (reinício ao salvar arquivos).")

    def on_file_changed(self, path: Path, event_type: str = "modified") -> None:
        path = Path(path)
        if not CONFIG.should_watch(path.relative_to(self.runner.project_root)):
            return
        if self._is_plugin(path):
            self.runner.plugins.reload_file(path)
        self.runner.request_restart(path, f"{event_type}: {path.name}")

    def reload_now(self) -> None:
        self.runner.request_restart(None, "reinício solicitado pelo console", delay=0)

    def _is_plugin(self, path: Path) -> bool:
        try:
            return path.parent.resolve() == CONFIG.plugins_path.resolve() and path.suffix == ".py"
        except OSError:
            return False
