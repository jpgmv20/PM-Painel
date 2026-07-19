"""
process.py

Gerenciador do processo principal do Kivy.

Responsável por:

- Iniciar aplicação
- Encerrar aplicação
- Reiniciar automaticamente
- Controlar PID
- Integrar com o estado global
"""


import subprocess
import sys
import time


from pathlib import Path


from devtools.logger import Logger



class ProcessManager:


    def __init__(
        self,
        main_file: Path,
        state
    ):


        self.main_file = main_file

        self.state = state


        self.process = None



    # =====================================================
    # Iniciar
    # =====================================================


    def start(self):


        if self.process:

            Logger.warning(
                "Processo já está em execução."
            )

            return



        try:


            self.process = subprocess.Popen(

                [
                    sys.executable,
                    str(self.main_file)
                ],

                stdout=subprocess.PIPE,

                stderr=subprocess.STDOUT,

                text=True,

                bufsize=1

            )


            self.state.register_process(
                self.process.pid
            )


            Logger.success(
                f"Kivy iniciado | PID: {self.process.pid}"
            )



        except Exception as error:


            Logger.error(
                f"Erro iniciando aplicação: {error}"
            )



    # =====================================================
    # Parar
    # =====================================================


    def stop(self):


        if not self.process:


            return



        try:


            Logger.info(
                "Encerrando aplicação..."
            )


            self.process.terminate()



            try:


                self.process.wait(
                    timeout=3
                )


            except subprocess.TimeoutExpired:


                self.process.kill()



        except Exception as error:


            Logger.error(
                f"Erro encerrando processo: {error}"
            )



        finally:


            self.process = None


            self.state.stop_process()



    # =====================================================
    # Reiniciar
    # =====================================================


    def restart(self):


        Logger.info(
            "Reiniciando aplicação..."
        )


        self.stop()



        time.sleep(
            0.2
        )


        self.state.register_restart()



        self.start()



    # =====================================================
    # Status
    # =====================================================


    def running(self):


        if not self.process:

            return False



        return (
            self.process.poll()
            is
            None
        )



    # =====================================================
    # Saída do processo
    # =====================================================


    def read_output(self):


        if not self.process:

            return



        if self.process.stdout:


            for line in self.process.stdout:


                Logger.info(
                    line.rstrip()
                )