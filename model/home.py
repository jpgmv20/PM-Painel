from kivy.app import App
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition

from model.componentes import BotaoHover, LayoutFundo


class AtalhoNavegador(BotaoHover):
    """Botão visual para abrir um serviço pelo perfil temporário."""

    icone = StringProperty("")
    titulo = StringProperty("")


class AreaNavegador(BoxLayout):
    """Área que abre o WebView2 usando o perfil temporário do processo."""

    status_texto = StringProperty("Perfil temporário pronto para o navegador.")
    profile_path = StringProperty("")
    browser_pronto = BooleanProperty(False)

    def configurar_browser(self) -> None:
        """Confirma que o perfil temporário do navegador está disponível."""
        app = App.get_running_app()
        self.profile_path = str(app.browser_manager.get_profile_path())
        self.status_texto = "Perfil temporário do navegador ativo para esta execução."
        self.browser_pronto = True

    def abrir_navegador(self) -> None:
        """Abre o navegador Chromium com o perfil efêmero do processo."""
        if not self.browser_pronto:
            self.status_texto = "O perfil temporário ainda não está disponível."
            return

        try:
            App.get_running_app().browser_manager.open_url(
                url="https://www.google.com/",
                title="Navegador do PM-Painel",
            )
            self.status_texto = "Navegador aberto com perfil temporário."
        except (RuntimeError, ValueError) as error:
            self.status_texto = str(error)


    def abrir_atalho(self, url: str, app_mode: bool = True) -> None:
        """Abre serviços em modo aplicativo, sem a barra do navegador."""
        if not self.browser_pronto:
            self.status_texto = "O perfil temporário ainda não está disponível."
            return

        try:
            App.get_running_app().browser_manager.open_url(
                url=url,
                title="Atalho do PM-Painel",
                app_mode=app_mode,
            )
            self.status_texto = "Atalho aberto com perfil temporário."
        except (RuntimeError, ValueError) as error:
            self.status_texto = str(error)

    def abrir_git_bash(self) -> None:
        """Abre o terminal Git Bash com dados descartados ao fechar o painel."""
        try:
            App.get_running_app().git_bash_manager.open_git_bash()
            self.status_texto = "Git Bash aberto com perfil temporário."
        except (RuntimeError, ValueError) as error:
            self.status_texto = str(error)


class TelaPrincipal(LayoutFundo):
    """Tela principal que constrói os cartões a partir da configuração do menu."""

    def atualizar_foto_perfil(self, caminho: str) -> None:
        """Encaminha a foto local para o cabeçalho da tela principal."""
        if caminho:
            self.ids.cabecalho.atualizar_foto_perfil(caminho)

    def abrir_configuracoes(self) -> None:
        """Vai para a tela de extensões e configurações a partir do primeiro card."""
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="left", duration=0.25)
        manager.current = "configuracoes"

    def on_kv_post(self, _base_widget) -> None:
        self.ids.browser_area.configurar_browser()
