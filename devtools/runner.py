"""
runner.py

Controlador principal do ambiente.

Responsável por iniciar
e conectar todos os sistemas.
"""


import time
from pathlib import Path


from devtools.config import CONFIG
from devtools.state import DevelopmentState
from devtools.logger import Logger
from devtools.events import EVENTS

from devtools.process import ProcessManager
from devtools.watcher import FileWatcher
from devtools.hotreload import HotReloadManager
from devtools.plugins import PluginManager
from devtools.profiler import Profiler
from devtools.commands import CommandManager
from devtools.console import DevelopmentConsole



class DevelopmentRunner:


    def __init__(self):


        self.project_root = (
            CONFIG.project_root
        )


        self.state = DevelopmentState()



        self.state.project_root = (
            self.project_root
        )



        self.main_file = (
            self.project_root
            /
            CONFIG.main_file
        )



        self.process = ProcessManager(

            self.main_file,

            self.state

        )



        self.profiler = Profiler()



        self.plugins = PluginManager(

            self.project_root

        )



        self.watcher = FileWatcher(

            self

        )



        self.hotreload = HotReloadManager(

            self

        )



        self.commands = CommandManager(

            self

        )



        self.console = DevelopmentConsole(

            self.commands

        )



        self.running = False



    # =====================================================
    # Inicialização
    # =====================================================


    def start(self):


        Logger.info(
            "Inicializando ambiente..."
        )


        self.running = True



        self.profiler.start()



        self.setup_events()



        self.commands.register_default()



        self.plugins.load_all()



        self.hotreload.load_existing_kv()



        self.process.start()



        self.watcher.start()



        self.console.start()

        self.profiler.finish_startup(
            self.state
        )

        EVENTS.emit(
            "app_started"
        )

        Logger.success(
            "Ambiente iniciado."
        )

        try:

            while self.process.running():

                time.sleep(0.2)

        except KeyboardInterrupt:

            pass

        finally:

            self.shutdown()



    # =====================================================
    # Eventos
    # =====================================================


    def setup_events(self):


        EVENTS.on(

            "file_changed",

            self.on_file_changed

        )



    def on_file_changed(
        self,
        file
    ):


        path = Path(file)



        if path.suffix == ".kv":


            self.hotreload.changed(
                path
            )



    # =====================================================
    # Reinício
    # =====================================================


    def restart(
        self,
        reason=None
    ):


        Logger.warning(
            f"Restart solicitado: {reason}"
        )


        self.process.restart()



    # =====================================================
    # Encerrar
    # =====================================================


    def shutdown(self):


        Logger.info(
            "Encerrando ambiente..."
        )


        self.running = False



        self.watcher.stop()



        self.console.stop()



        self.process.stop()



        EVENTS.emit(
            "shutdown"
        )