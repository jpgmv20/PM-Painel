"""
state.py

Estado global do ambiente de desenvolvimento.

Todos os módulos compartilham
essas informações através deste objeto.
"""


from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path



@dataclass
class DevelopmentState:


    # =====================================================
    # Projeto
    # =====================================================

    project_root: Path | None = None

    main_file: Path | None = None



    # =====================================================
    # Processo
    # =====================================================

    process_id: int | None = None

    process_running: bool = False

    process_start_time: datetime | None = None


    process_restart_count: int = 0



    # =====================================================
    # Watcher
    # =====================================================

    watcher_running: bool = False


    watcher_reload_count: int = 0


    watcher_last_reload: datetime | None = None



    # =====================================================
    # Arquivos alterados
    # =====================================================

    last_changed_file: Path | None = None


    changed_files: list[Path] = field(
        default_factory=list
    )



    # =====================================================
    # Validação
    # =====================================================

    validation_success: bool = True


    last_validation_error: str | None = None



    # =====================================================
    # Performance
    # =====================================================

    last_boot_time: float = 0.0


    average_boot_time: float = 0.0


    max_boot_time: float = 0.0


    min_boot_time: float = 999999.0



    # =====================================================
    # Erros
    # =====================================================

    last_exception: Exception | None = None


    exception_count: int = 0



    # =====================================================
    # Registro de reload
    # =====================================================

    def register_reload(
        self,
        file
    ):


        self.watcher_reload_count += 1


        self.last_changed_file = file


        self.watcher_last_reload = datetime.now()



        self.changed_files.append(
            file
        )



        if len(self.changed_files) > 100:

            self.changed_files.pop(0)



    # =====================================================
    # Processo
    # =====================================================

    def register_process(
        self,
        pid: int
    ):


        self.process_running = True


        self.process_id = pid


        self.process_start_time = datetime.now()



    def stop_process(self):


        self.process_running = False


        self.process_id = None



    def register_restart(self):


        self.process_restart_count += 1



    # =====================================================
    # Performance
    # =====================================================

    def register_boot_time(
        self,
        seconds: float
    ):


        self.last_boot_time = seconds



        if seconds > self.max_boot_time:

            self.max_boot_time = seconds



        if seconds < self.min_boot_time:

            self.min_boot_time = seconds



        count = self.process_restart_count



        if count > 0:


            self.average_boot_time = (
                (
                    self.average_boot_time
                    *
                    (count - 1)
                )
                +
                seconds
            ) / count



    # =====================================================
    # Validação
    # =====================================================

    def register_validation_error(
        self,
        error: str
    ):


        self.validation_success = False


        self.last_validation_error = error



    def clear_validation(self):


        self.validation_success = True


        self.last_validation_error = None



    # =====================================================
    # Exceções
    # =====================================================

    def register_exception(
        self,
        error: Exception
    ):


        self.exception_count += 1


        self.last_exception = error