"""
commands.py

Sistema de comandos internos.

Permite criar comandos
executados pelo console do framework.

Exemplo:

PM> status
PM> reload
PM> plugins
"""


from devtools.logger import Logger



class CommandManager:


    def __init__(
        self,
        runner
    ):


        self.runner = runner


        self.commands = {}



    # =====================================================
    # Registrar comando
    # =====================================================


    def register(
        self,
        name,
        callback,
        description=""
    ):


        self.commands[name] = {


            "callback": callback,


            "description": description


        }



        Logger.debug(
            f"Comando registrado: {name}"
        )



    # =====================================================
    # Executar comando
    # =====================================================


    def execute(
        self,
        command
    ):


        parts = command.split()


        if not parts:

            return



        name = parts[0]


        args = parts[1:]



        if name not in self.commands:


            Logger.warning(
                f"Comando desconhecido: {name}"
            )


            return



        try:


            result = self.commands[name][
                "callback"
            ](
                *args
            )



            return result



        except Exception as error:


            Logger.error(
                f"Erro executando comando {name}: {error}"
            )



    # =====================================================
    # Comandos padrão
    # =====================================================


    def register_default(self):


        self.register(

            "status",

            self.status,

            "Mostra estado da aplicação"

        )



        self.register(

            "reload",

            self.reload,

            "Recarrega aplicação"

        )



        self.register(

            "plugins",

            self.plugins,

            "Lista plugins ativos"

        )



        self.register(

            "logs",

            self.logs,

            "Mostra últimos logs"

        )



        self.register(

            "profile",

            self.profile,

            "Mostra dados de desempenho"

        )



    # =====================================================
    # Implementações
    # =====================================================


    def status(self):


        state = self.runner.state



        Logger.box(

            "STATUS",

            f"Processo: {state.process_running}",

            f"PID: {state.process_id}",

            f"Reloads: {state.watcher_reload_count}",

            f"Restarts: {state.process_restart_count}"

        )



    def reload(self):


        self.runner.restart()



    def plugins(self):


        plugins = (
            self.runner.plugins.list()
        )


        Logger.box(

            "PLUGINS",

            *plugins

        )



    def logs(self):


        for log in Logger.last():

            print(log)



    def profile(self):


        data = (
            self.runner.profiler.report()
        )


        Logger.box(

            "PROFILE",

            *[
                f"{k}: {v:.4f}s"

                for k, v in data.items()

            ]

        )



    # =====================================================
    # Ajuda
    # =====================================================


    def help(self):


        Logger.box(

            "COMMANDS",

            *[

                f"{name} - {data['description']}"

                for name, data

                in self.commands.items()

            ]

        )