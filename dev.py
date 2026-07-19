"""
dev.py

Ponto de entrada do ambiente de desenvolvimento.

Executar:

    python dev.py
"""


import traceback


from devtools.logger import Logger
from devtools.runner import DevelopmentRunner
from devtools.events import EVENTS



def handle_exception(error):

    Logger.error(
        "Erro não tratado no ambiente."
    )

    Logger.error(
        str(error)
    )


    traceback.print_exc()


    EVENTS.emit(
        "error",
        error
    )



def main():

    try:

        Logger.setup()

        Logger.banner()


        runner = DevelopmentRunner()


        EVENTS.emit(
            "before_start",
            runner
        )


        runner.start()



    except KeyboardInterrupt:


        Logger.warning(
            "Execução interrompida pelo usuário."
        )



    except Exception as error:


        handle_exception(
            error
        )



    finally:


        EVENTS.emit(
            "shutdown"
        )



if __name__ == "__main__":

    main()