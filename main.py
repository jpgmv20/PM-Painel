import json
import os
from pathlib import Path

from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from devtools.widgets import WIDGETS


if os.environ.get("LOCALAPPDATA"):
    APP_DATA_DIRECTORY = Path(os.environ["LOCALAPPDATA"]) / "PM-Painel"
else:
    APP_DATA_DIRECTORY = Path.home() / ".pm-painel"

WINDOW_STATE_FILE = APP_DATA_DIRECTORY / "window-state.json"
MINIMUM_WINDOW_SIZE = (640, 480)


def restore_window_state():
    """Restaura tamanho e posição sem impedir a abertura do painel."""
    try:
        saved_state = json.loads(WINDOW_STATE_FILE.read_text(encoding="utf-8"))
        width = int(saved_state["width"])
        height = int(saved_state["height"])
        if width >= MINIMUM_WINDOW_SIZE[0] and height >= MINIMUM_WINDOW_SIZE[1]:
            Window.size = (width, height)

        left = saved_state.get("left")
        top = saved_state.get("top")
        if left is not None and top is not None:
            left = int(left)
            top = int(top)
            # Evita usar coordenadas corrompidas; valores negativos são
            # válidos quando há mais de um monitor.
            if -32768 <= left <= 32767 and -32768 <= top <= 32767:
                Window.left = left
                Window.top = top
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        pass


# Carrega o arquivo da subpasta
caminho_kv = os.path.join(os.path.dirname(__file__), 'view', 'main.kv')
Builder.load_file(caminho_kv)

class TelaPrincipal(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        WIDGETS.register(self)
        
    def executar_login(self):
        usuario = self.ids.login_usuario.text
        senha = self.ids.login_senha.text
        print(f"[LOGIN] Usuário: {usuario} | Senha: {senha}")

    def executar_cadastro(self):
        nome = self.ids.cad_nome.text
        email = self.ids.cad_email.text
        senha = self.ids.cad_senha.text
        print(f"[CADASTRO] Nome: {nome} | Email: {email} | Senha: {senha}")

class MeuApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._window_save_event = None
        self._window_state_poll = None
        self._last_saved_window_state = None

    def build(self):
        restore_window_state()
        Window.bind(size=self._schedule_window_save)
        self._window_state_poll = Clock.schedule_interval(
            self._track_window_state,
            0.5,
        )
        return TelaPrincipal()

    def _schedule_window_save(self, *_):
        if self._window_save_event is not None:
            self._window_save_event.cancel()
        self._window_save_event = Clock.schedule_once(self._save_window_state, 0.25)

    @staticmethod
    def _current_window_state():
        try:
            width, height = (round(value) for value in Window.size)
            left = round(Window.left)
            top = round(Window.top)
        except (TypeError, ValueError):
            return None

        if width < MINIMUM_WINDOW_SIZE[0] or height < MINIMUM_WINDOW_SIZE[1]:
            return None
        return {"width": width, "height": height, "left": left, "top": top}

    def _track_window_state(self, *_):
        if self._current_window_state() != self._last_saved_window_state:
            self._schedule_window_save()

    def _save_window_state(self, *_):
        self._window_save_event = None
        window_state = self._current_window_state()
        if window_state is None:
            return
        try:
            APP_DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
            temporary_file = WINDOW_STATE_FILE.with_suffix(".tmp")
            temporary_file.write_text(
                json.dumps(window_state),
                encoding="utf-8",
            )
            temporary_file.replace(WINDOW_STATE_FILE)
            self._last_saved_window_state = window_state
        except OSError as error:
            print(f"[WINDOW] Não foi possível salvar o estado: {error}")

    def on_stop(self):
        if self._window_state_poll is not None:
            self._window_state_poll.cancel()
        self._save_window_state()

if __name__ == "__main__":
    MeuApp().run()
