"""Carregamento seguro de plugins locais do DevTools."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from types import ModuleType

from devtools.config import CONFIG
from devtools.events import EVENTS
from devtools.logger import Logger


class PluginManager:
    def __init__(self, project_root: Path, runner) -> None:
        self.project_root = Path(project_root).resolve()
        self.runner = runner
        self.plugins_path = self.project_root / CONFIG.plugins_directory
        self.loaded_plugins: dict[str, dict[str, object]] = {}

    def load_all(self) -> None:
        if not CONFIG.enable_plugins:
            Logger.info("Plugins desativados.")
            return
        self.plugins_path.mkdir(exist_ok=True)
        for file in sorted(self.plugins_path.glob("*.py")):
            if not file.name.startswith("_"):
                self.load(file)

    def load(self, file: Path) -> bool:
        file = Path(file).resolve()
        name = file.stem
        if not file.is_file():
            Logger.warning(f"Plugin não encontrado: {file.name}")
            return False
        if name in self.loaded_plugins:
            self.unload(name)
        module_name = f"pm_dev_plugin_{name}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, file)
            if spec is None or spec.loader is None:
                raise ImportError("não foi possível carregar o módulo")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            handlers = self._register_hooks(module)
            self.loaded_plugins[name] = {
                "module": module,
                "file": file,
                "handlers": handlers,
                "module_name": module_name,
            }
            self._call_hook(module, "setup", self.runner)
            self._call_hook(module, "on_start", self.runner)
            Logger.success(f"Plugin carregado: {name}")
            return True
        except Exception as error:
            sys.modules.pop(module_name, None)
            Logger.error(f"Erro carregando plugin {name}: {error}")
            return False

    def _register_hooks(self, module: ModuleType) -> list[tuple[str, object]]:
        handlers: list[tuple[str, object]] = []
        event_hooks = {"after_reload": "on_reload", "shutdown": "on_shutdown"}
        for event_name, hook_name in event_hooks.items():
            hook = getattr(module, hook_name, None)
            if not callable(hook):
                continue

            def callback(*args, _hook=hook, **kwargs):
                self._call(_hook, *args, **kwargs)

            EVENTS.on(event_name, callback)
            handlers.append((event_name, callback))
        return handlers

    def _call_hook(self, module: ModuleType, name: str, *args: object) -> None:
        hook = getattr(module, name, None)
        if callable(hook):
            self._call(hook, *args)

    @staticmethod
    def _call(hook, *args: object, **kwargs: object) -> None:
        try:
            signature = inspect.signature(hook)
            accepts_args = any(
                parameter.kind is inspect.Parameter.VAR_POSITIONAL
                for parameter in signature.parameters.values()
            )
            positional = [
                parameter
                for parameter in signature.parameters.values()
                if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            hook(*args if accepts_args else args[:len(positional)], **kwargs)
        except Exception as error:
            Logger.error(f"Erro no plugin {getattr(hook, '__module__', '?')}: {error}")

    def reload_file(self, file: Path) -> bool:
        file = Path(file).resolve()
        name = file.stem
        if name in self.loaded_plugins:
            self.unload(name)
        return self.load(file) if file.exists() else False

    def unload(self, name: str, run_shutdown: bool = True) -> None:
        plugin = self.loaded_plugins.pop(name, None)
        if plugin is None:
            return
        module = plugin["module"]
        if run_shutdown:
            self._call_hook(module, "on_shutdown")
        for event_name, callback in plugin["handlers"]:
            EVENTS.off(event_name, callback)
        module_name = str(plugin["module_name"])
        EVENTS.remove_module_listeners(module_name)
        sys.modules.pop(module_name, None)
        Logger.info(f"Plugin descarregado: {name}")

    def unload_all(self, run_shutdown: bool = True) -> None:
        for name in tuple(self.loaded_plugins):
            self.unload(name, run_shutdown=run_shutdown)

    def list(self) -> list[str]:
        return sorted(self.loaded_plugins)

    def status(self) -> dict[str, bool]:
        return {name: True for name in self.loaded_plugins}
