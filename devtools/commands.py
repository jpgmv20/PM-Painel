"""Comandos disponíveis no console do DevTools."""

from __future__ import annotations

import shlex
from collections.abc import Callable

from devtools.logger import Logger


class CommandManager:
    def __init__(self, runner) -> None:
        self.runner = runner
        self.commands: dict[str, tuple[Callable, str]] = {}

    def register(self, name: str, callback: Callable, description: str) -> None:
        normalized = name.casefold()
        self.commands[normalized] = (callback, description)
        Logger.debug(f"Comando registrado: {normalized}")

    def register_default(self) -> None:
        self.register("status", self.status, "Mostra o estado da aplicação.")
        self.register("reload", self.reload, "Reinicia a aplicação agora.")
        self.register("restart", self.reload, "Alias de reload.")
        self.register("plugins", self.plugins, "Lista os plugins carregados.")
        self.register("logs", self.logs, "Mostra logs recentes; opcionalmente: logs 50.")
        self.register("profile", self.profile, "Mostra tempos do ambiente.")
        self.register("help", self.help, "Mostra os comandos disponíveis.")
        self.register("stop", self.stop, "Encerra o DevTools.")
        self.register("exit", self.stop, "Alias de stop.")

    def execute(self, command: str) -> None:
        try:
            parts = shlex.split(command, posix=False)
        except ValueError as error:
            Logger.warning(f"Comando inválido: {error}")
            return
        if not parts:
            return
        name, *args = parts
        item = self.commands.get(name.casefold())
        if item is None:
            Logger.warning(f"Comando desconhecido: {name}. Digite 'help'.")
            return
        callback, _ = item
        try:
            callback(*args)
        except TypeError:
            Logger.warning(f"Uso inválido para '{name}'. Digite 'help'.")
        except Exception as error:
            Logger.error(f"Erro executando comando '{name}': {error}")

    def status(self) -> None:
        state = self.runner.state.as_dict()
        Logger.box(
            "STATUS",
            f"PID: {state['pid']}", f"Executando: {state['running']}",
            f"Reinícios: {state['restarts']}", f"Recargas: {state['reloads']}",
            f"Arquivos alterados: {state['files_changed']}",
        )

    def reload(self) -> None:
        self.runner.hotreload.reload_now()

    def plugins(self) -> None:
        names = self.runner.plugins.list() or ["Nenhum plugin carregado."]
        Logger.box("PLUGINS", *names)

    def logs(self, amount: str = "20") -> None:
        try:
            quantity = max(1, min(int(amount), 500))
        except ValueError:
            Logger.warning("Quantidade de logs deve ser um número.")
            return
        for line in Logger.last(quantity):
            print(line, flush=True)

    def profile(self) -> None:
        self.runner.profiler.print_report()

    def help(self) -> None:
        Logger.box("COMANDOS", *(f"{name} — {item[1]}" for name, item in sorted(self.commands.items())))

    def stop(self) -> None:
        self.runner.shutdown()
