"""
hotreload.py

Hot Reload para arquivos .kv do projeto.
"""

from pathlib import Path

from kivy.lang import Builder

from devtools.config import CONFIG
from devtools.events import EVENTS
from devtools.logger import Logger
from devtools.widgets import WIDGETS


class HotReloadManager:

    def __init__(self, runner):

        self.runner = runner

        self.loaded_files = set()

        self.project_root = self.runner.project_root.resolve()

    # =====================================================
    # Descoberta dos arquivos KV
    # =====================================================

    def discover_kv_files(self):

        kv_files = []

        for file in self.project_root.rglob("*.kv"):

            if self.ignore(file):
                continue

            kv_files.append(file)

        return sorted(kv_files)

    # =====================================================
    # Ignorar arquivos externos
    # =====================================================

    def ignore(self, file: Path):

        try:
            relative = file.resolve().relative_to(
                self.project_root
            )

        except ValueError:
            return True

        for part in relative.parts:

            if CONFIG.is_ignored_directory(part):
                return True

        return False

    # =====================================================
    # Carregamento inicial
    # =====================================================

    def load_existing_kv(self):

        Logger.info("Procurando arquivos KV...")

        files = self.discover_kv_files()

        if not files:

            Logger.warning(
                "Nenhum arquivo .kv encontrado."
            )

            return

        for file in files:

            self.load_file(file)

        Logger.success(
            f"{len(files)} arquivo(s) KV carregado(s)."
        )

    # =====================================================
    # Carregar arquivo
    # =====================================================

    def load_file(self, file: Path):

        file = file.resolve()

        if file in self.loaded_files:
            return

        try:

            Builder.load_file(str(file))

            self.loaded_files.add(file)

            Logger.success(
                f"Carregado: {file.relative_to(self.project_root)}"
            )

        except Exception as error:

            Logger.error(
                f"Erro carregando {file.name}\n{error}"
            )

    # =====================================================
    # Reload
    # =====================================================

    def reload_file(self, file: Path):

        file = file.resolve()

        Logger.info(
            f"Hot Reload -> {file.relative_to(self.project_root)}"
        )

        try:

            try:
                Builder.unload_file(str(file))
            except Exception:
                pass

            Builder.load_file(str(file))

            WIDGETS.reload()

            EVENTS.emit(
                "after_reload",
                file
            )

            Logger.success(
                "Hot Reload concluído."
            )

        except Exception as error:

            Logger.error(
                f"Erro durante Hot Reload\n{error}"
            )

    # =====================================================
    # Evento
    # =====================================================

    def changed(self, file):

        file = Path(file).resolve()

        if file.suffix != ".kv":
            return

        if self.ignore(file):
            return

        EVENTS.emit(
            "before_reload",
            file
        )

        self.reload_file(file)