"""Registro opcional de widgets usados pela aplicação Kivy."""

from __future__ import annotations

from weakref import WeakValueDictionary

from devtools.logger import Logger


class WidgetManager:
    """Guarda referências fracas, sem impedir a destruição de telas antigas."""

    def __init__(self) -> None:
        self._widgets: WeakValueDictionary[str, object] = WeakValueDictionary()

    def register(self, widget: object, name: str | object | None = None) -> str:
        """Registra ``widget`` e devolve seu nome.

        Aceita tanto ``register(widget)`` quanto a forma antiga
        ``register('nome', widget)`` para não quebrar telas já existentes.
        """
        if isinstance(widget, str) and name is not None:
            key, target = widget, name
        else:
            target = widget
            key = str(name) if isinstance(name, str) else f"{type(target).__name__}:{id(target)}"
        try:
            self._widgets[key] = target  # type: ignore[assignment]
        except TypeError:
            Logger.warning(f"Widget não pode ser registrado por referência fraca: {key}")
            return key
        Logger.debug(f"Widget registrado: {key}")
        return key

    def unregister(self, widget_or_name: object) -> None:
        if isinstance(widget_or_name, str):
            self._widgets.pop(widget_or_name, None)
            return
        for key, widget in tuple(self._widgets.items()):
            if widget is widget_or_name:
                self._widgets.pop(key, None)

    def get(self, name: str) -> object | None:
        return self._widgets.get(name)

    def refresh(self) -> int:
        updated = 0
        for name, widget in tuple(self._widgets.items()):
            try:
                canvas = getattr(widget, "canvas", None)
                if canvas is not None:
                    canvas.ask_update()
                callback = getattr(widget, "on_devtools_reload", None)
                if callable(callback):
                    callback()
                updated += 1
            except Exception as error:
                Logger.error(f"Erro atualizando widget {name}: {error}")
        return updated

    def reload(self) -> int:
        return self.refresh()

    def list(self) -> list[str]:
        return list(self._widgets.keys())

    def clear(self) -> None:
        self._widgets.clear()


WIDGETS = WidgetManager()
