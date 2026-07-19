"""
plugins.py

Sistema de plugins do framework.

Responsável por:

- Descobrir plugins
- Carregar plugins automaticamente
- Registrar plugins ativos
- Integrar com eventos
"""


import importlib.util

from pathlib import Path


from devtools.logger import Logger
from devtools.config import CONFIG



class PluginManager:


    def __init__(
        self,
        project_root
    ):


        self.project_root = project_root


        self.plugins_directory = (
            project_root
            /
            "plugins"
        )


        self.loaded_plugins = {}



    # =====================================================
    # Procurar plugins
    # =====================================================


    def discover(self):


        if not CONFIG.enable_plugins:


            Logger.warning(
                "Plugins desativados."
            )


            return []



        if not self.plugins_directory.exists():


            self.plugins_directory.mkdir(
                exist_ok=True
            )


            return []



        return list(
            self.plugins_directory.glob(
                "*.py"
            )
        )



    # =====================================================
    # Carregar todos
    # =====================================================


    def load_all(self):


        plugins = self.discover()



        for plugin in plugins:


            if plugin.name.startswith(
                "_"
            ):

                continue



            self.load(
                plugin
            )



    # =====================================================
    # Carregar plugin
    # =====================================================


    def load(
        self,
        file: Path
    ):


        try:


            module_name = (
                f"plugin_{file.stem}"
            )



            spec = importlib.util.spec_from_file_location(

                module_name,

                file

            )


            if not spec or not spec.loader:


                return



            module = importlib.util.module_from_spec(
                spec
            )


            spec.loader.exec_module(
                module
            )



            self.loaded_plugins[
                file.stem
            ] = module



            Logger.success(
                f"Plugin carregado: {file.stem}"
            )



        except Exception as error:


            Logger.error(
                f"Erro carregando plugin {file.name}: {error}"
            )



    # =====================================================
    # Descarregar
    # =====================================================


    def unload(
        self,
        name
    ):


        if name in self.loaded_plugins:


            del self.loaded_plugins[name]


            Logger.info(
                f"Plugin removido: {name}"
            )



    # =====================================================
    # Recarregar
    # =====================================================


    def reload(
        self,
        name
    ):


        if name not in self.loaded_plugins:


            return



        module = self.loaded_plugins[name]


        file = Path(
            module.__file__
        )



        self.unload(
            name
        )


        self.load(
            file
        )



    # =====================================================
    # Informações
    # =====================================================


    def list(self):


        return list(
            self.loaded_plugins.keys()
        )