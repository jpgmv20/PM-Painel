import json
import os
from kivy.config import Config

# -------------------------------------------------------------
# CONFIGURAÇÕES DA JANELA (DEVE VIR ANTES DOS OUTROS IMPORTS)
# -------------------------------------------------------------
# 1. Inicia em tela cheia ('auto' usa a resolução nativa do monitor)
Config.set('graphics', 'fullscreen', 'auto')

# 2. Fixa a janela (impede redimensionamento)
Config.set('graphics', 'resizable', '0')

from pathlib import Path
import shutil

from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from devtools.widgets import WIDGETS
from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty
from kivy.app import App


import model.componentes as componentes


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


# Diretório base (raiz do projeto)
base_dir = os.path.dirname(__file__)

# 1. Primeiro carregamos os componentes (para o Kivy aprender os widgets)
Builder.load_file(os.path.join(base_dir, 'view', 'componentes.kv'))

# 2. Depois carregamos as telas que serão trocadas dinamicamente
Builder.load_file(os.path.join(base_dir, 'view', 'main.kv'))
Builder.load_file(os.path.join(base_dir, 'view', 'login.kv'))
Builder.load_file(os.path.join(base_dir, 'view', 'home.kv'))

class TelaInicial(componentes.LayoutFundo):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        WIDGETS.register(self)

    def abrir_MenuPrincipal(self, instance):
        app = App.get_running_app()
        manager = app.root

        # Login temporário para testes
        login = False

        if login:
            manager.transition = SlideTransition(direction='left', duration=0.35)
            manager.current = 'principal'
        else:
            manager.transition = SlideTransition(direction='down', duration=0.35)
            manager.current = 'login'

        print(manager.transition.direction)
        
    

class MeuApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._window_save_event = None
        self._window_state_poll = None
        self._last_saved_window_state = None
        
        # --- 1. APAGAR UM ARQUIVO ESPECÍFICO ---
        caminho_arquivo = ""

        if os.path.exists(caminho_arquivo):
            try:
                os.remove(caminho_arquivo)
                print(f"Arquivo '{caminho_arquivo}' removido com sucesso!")
            except Exception as e:
                print(f"Erro ao remover arquivo: {e}")

        # --- 2. APAGAR UMA PASTA INTEIRA E SEU CONTEÚDO ---
        caminho_pasta = "logs"

        if os.path.exists(caminho_pasta):
            try:
                # shutil.rmtree apaga a pasta e TUDO que estiver dentro dela
                shutil.rmtree(caminho_pasta)
                print(f"Pasta '{caminho_pasta}' removida com sucesso!")
            except Exception as e:
                print(f"Erro ao remover pasta: {e}")

    def build(self):
        restore_window_state()
        Window.bind(size=self._schedule_window_save)
        self._window_state_poll = Clock.schedule_interval(
            self._track_window_state,
            0.5,
        )

        manager = ScreenManager()
        manager.transition = SlideTransition(direction='right', duration=0.25)

        tela_inicial_screen = Screen(name='home')
        tela_inicial_screen.add_widget(TelaInicial())
        manager.add_widget(tela_inicial_screen)

        tela_login_screen = Screen(name='login')
        tela_login_screen.add_widget(__import__('model.login', fromlist=['TelaLogin']).TelaLogin())
        manager.add_widget(tela_login_screen)

        tela_principal_screen = Screen(name='principal')
        tela_principal_screen.add_widget(__import__('model.home', fromlist=['TelaPrincipal']).TelaPrincipal())
        manager.add_widget(tela_principal_screen)

        manager.current = 'home'
        return manager
    
    def on_stop(self):
        """Este método é executado automaticamente quando o app está sendo fechado."""
        print("Encerrando a aplicação e limpando arquivos temporários...")

        # --- 1. APAGAR UM ARQUIVO ESPECÍFICO ---
        caminho_arquivo = ""

        if os.path.exists(caminho_arquivo):
            try:
                os.remove(caminho_arquivo)
                print(f"Arquivo '{caminho_arquivo}' removido com sucesso!")
            except Exception as e:
                print(f"Erro ao remover arquivo: {e}")

        # --- 2. APAGAR UMA PASTA INTEIRA E SEU CONTEÚDO ---
        caminho_pasta = ""

        if os.path.exists(caminho_pasta):
            try:
                # shutil.rmtree apaga a pasta e TUDO que estiver dentro dela
                shutil.rmtree(caminho_pasta)
                print(f"Pasta '{caminho_pasta}' removida com sucesso!")
            except Exception as e:
                print(f"Erro ao remover pasta: {e}")

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
