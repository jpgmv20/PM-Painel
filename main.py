"""Ponto de entrada do PM-Painel."""

import os

from kivy.config import Config

# Estas opções precisam ser definidas antes de importar os módulos visuais do Kivy.
Config.set("graphics", "fullscreen", "auto")
Config.set("graphics", "resizable", "0")

from kivy.app import App
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivymd.app import MDApp

import model.componentes as componentes
from model.configuracoes import TelaConfiguracoes
from model.home import TelaPrincipal
from model.login import TelaLogin
from service.git_bash import GitBashManager
from service.login.authentication import AuthenticationService
from service.web.browser import BrowserManager
from service.login.google_auth import GoogleAuth
from service.login.session import SessionManager
from service.settings import SettingsStore


PROJECT_DIR = os.path.dirname(__file__)

# Carrega primeiro os widgets reutilizáveis e depois as telas que os utilizam.
for view_name in ("componentes.kv", "main.kv", "login.kv", "home.kv", "configuracoes.kv"):
    Builder.load_file(os.path.join(PROJECT_DIR, "view", view_name))


class TelaInicial(componentes.LayoutFundo):
    """Tela de boas-vindas que encaminha o usuário para a autenticação."""

    def abrir_menu_principal(self, _instance: object) -> None:
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="down", duration=0.35)
        manager.current = "login"

    # Mantém o nome antigo enquanto o arquivo KV é atualizado gradualmente.
    abrir_MenuPrincipal = abrir_menu_principal


class MeuApp(MDApp):
    """Monta as telas e controla os recursos que existem só nesta execução."""

    profile_photo = StringProperty("assets/icon/user_icon.png")

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.settings = SettingsStore()
        self.browser_manager = BrowserManager(
            cleanup_abandoned_profiles=self.settings.clear_abandoned_sessions,
        )
        self.git_bash_manager = GitBashManager()
        self.session_manager = SessionManager()
        self.google_auth = GoogleAuth()
        self.authentication_service = AuthenticationService(
            google_auth=self.google_auth,
            session_manager=self.session_manager,
            browser_manager=self.browser_manager,
        )
        self.settings.bind(fullscreen=self._apply_fullscreen)
        self._apply_fullscreen(self.settings, self.settings.fullscreen)

    @staticmethod
    def _apply_fullscreen(_settings: SettingsStore, enabled: bool) -> None:
        """Aplica imediatamente a única preferência de computador suportada pelo app."""
        Window.fullscreen = "auto" if enabled else False

    def build(self) -> ScreenManager:
        manager = ScreenManager(transition=SlideTransition(direction="right", duration=0.25))
        for name, widget in (
            ("home", TelaInicial()),
            ("login", TelaLogin()),
            ("principal", TelaPrincipal()),
            ("configuracoes", TelaConfiguracoes()),
        ):
            screen = Screen(name=name)
            screen.add_widget(widget)
            manager.add_widget(screen)
        return manager

    def set_profile_photo(self, path: str | None = None) -> None:
        """Atualiza todos os cabeçalhos por meio de uma única propriedade reativa."""
        self.profile_photo = path or "assets/icon/user_icon.png"

    def on_stop(self) -> None:
        """Remove sessão, credenciais e perfil do navegador ao fechar o painel."""
        if self.settings.clear_sessions_on_exit:
            self.session_manager.clear()
            self.google_auth.logout()
        self.browser_manager.shutdown(remove_profile=self.settings.clear_temporary_browser)
        self.git_bash_manager.shutdown()


if __name__ == "__main__":
    MeuApp().run()
