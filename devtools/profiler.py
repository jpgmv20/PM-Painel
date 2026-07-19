"""
profiler.py

Sistema de análise de desempenho.

Responsável por:

- Medir tempo de inicialização
- Medir operações
- Guardar histórico
- Exibir estatísticas
"""


import time
from functools import wraps


from devtools.logger import Logger
from devtools.config import CONFIG



class Profiler:


    def __init__(self):

        self.records = {}

        self.start_time = None

        self.enabled = CONFIG.profile_startup



    # =====================================================
    # Início da aplicação
    # =====================================================


    def start(self):


        if not self.enabled:

            return



        self.start_time = time.perf_counter()



    # =====================================================
    # Finalização da inicialização
    # =====================================================


    def finish_startup(
        self,
        state
    ):


        if not self.enabled:

            return



        if self.start_time is None:

            return



        elapsed = (
            time.perf_counter()
            -
            self.start_time
        )



        state.register_boot_time(
            elapsed
        )


        Logger.success(
            f"Inicialização: {elapsed:.3f}s"
        )



    # =====================================================
    # Medir função
    # =====================================================


    def measure(
        self,
        name
    ):


        def decorator(func):


            @wraps(func)
            def wrapper(*args, **kwargs):


                start = time.perf_counter()



                result = func(
                    *args,
                    **kwargs
                )



                elapsed = (
                    time.perf_counter()
                    -
                    start
                )



                self.records[name] = elapsed



                Logger.debug(
                    f"{name}: {elapsed:.4f}s"
                )



                return result



            return wrapper


        return decorator



    # =====================================================
    # Registrar manualmente
    # =====================================================


    def record(
        self,
        name,
        seconds
    ):


        self.records[name] = seconds



    # =====================================================
    # Relatório
    # =====================================================


    def report(self):


        return dict(
            self.records
        )



    # =====================================================
    # Limpar dados
    # =====================================================


    def clear(self):

        self.records.clear()