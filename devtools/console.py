"""
console.py

Terminal interativo do framework.

Permite executar comandos:

PM> status
PM> reload
PM> plugins
PM> logs
"""


import threading


from devtools.logger import Logger



class DevelopmentConsole:


    def __init__(
        self,
        commands
    ):


        self.commands = commands


        self.running = False


        self.thread = None



    # =====================================================
    # Iniciar console
    # =====================================================


    def start(self):


        if self.running:

            return



        self.running = True



        self.thread = threading.Thread(

            target=self.loop,

            daemon=True

        )



        self.thread.start()



        Logger.success(
            "Console iniciado."
        )



    # =====================================================
    # Loop principal
    # =====================================================


    def loop(self):


        while self.running:


            try:


                command = input(
                    "\nPM> "
                )



                if command.strip() == "":

                    continue



                if command == "exit":


                    self.stop()


                    break



                self.commands.execute(
                    command
                )



            except EOFError:


                break



            except Exception as error:


                Logger.error(
                    f"Erro no console: {error}"
                )



    # =====================================================
    # Parar
    # =====================================================


    def stop(self):


        self.running = False


        Logger.info(
            "Console encerrado."
        )