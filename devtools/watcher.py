"""
watcher.py

Monitor de arquivos do projeto.

Responsável por:

- Detectar alterações
- Ignorar arquivos desnecessários
- Disparar eventos
- Integrar com reload automático
"""


import time
from pathlib import Path
from threading import Thread


from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


from devtools.config import CONFIG
from devtools.logger import Logger
from devtools.events import EVENTS



class ChangeHandler(
    FileSystemEventHandler
):


    def __init__(
        self,
        watcher
    ):

        super().__init__()

        self.watcher = watcher



    # =====================================================
    # Alteração detectada
    # =====================================================


    def on_modified(
        self,
        event
    ):


        if event.is_directory:

            return



        self.watcher.file_changed(
            Path(event.src_path)
        )



    # =====================================================
    # Arquivo criado
    # =====================================================


    def on_created(
        self,
        event
    ):


        if event.is_directory:

            return



        self.watcher.file_changed(
            Path(event.src_path)
        )



class FileWatcher:



    def __init__(
        self,
        runner
    ):


        self.runner = runner


        self.observer = None


        self.running = False


        self.last_changes = {}



    # =====================================================
    # Iniciar
    # =====================================================


    def start(self):


        if self.running:

            return



        self.observer = Observer()



        handler = ChangeHandler(
            self
        )



        self.observer.schedule(

            handler,

            str(
                self.runner.project_root
            ),

            recursive=CONFIG.recursive

        )



        self.observer.start()



        self.running = True



        self.runner.state.watcher_running = True



        Logger.success(
            "Watcher iniciado."
        )



    # =====================================================
    # Parar
    # =====================================================


    def stop(self):


        if not self.running:

            return



        self.observer.stop()


        self.observer.join()



        self.running = False



        self.runner.state.watcher_running = False



        Logger.info(
            "Watcher parado."
        )



    # =====================================================
    # Arquivo mudou
    # =====================================================


    def file_changed(
        self,
        file: Path
    ):


        if self.ignore(file):

            return



        now = time.time()



        previous = self.last_changes.get(
            file,
            0
        )



        if (
            now - previous
            <
            CONFIG.debounce
        ):

            return



        self.last_changes[file] = now



        Logger.info(
            f"Alteração detectada: {file.name}"
        )



        relative = file.relative_to(
            self.runner.project_root
        )



        self.runner.state.register_reload(
            relative
        )



        EVENTS.emit(
            "file_changed",
            relative
        )



        if CONFIG.auto_restart:


            self.runner.restart(
                relative
            )



    # =====================================================
    # Ignorar arquivos
    # =====================================================


    def ignore(
        self,
        file: Path
    ):


        if not CONFIG.is_valid_extension(
            file.suffix
        ):

            return True



        for folder in file.parts:


            if CONFIG.is_ignored_directory(
                folder
            ):

                return True



        if CONFIG.is_ignored_file(
            file.name
        ):

            return True



        return False