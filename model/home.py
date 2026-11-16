from kivy.app import App
from functools import partial
from pathlib import Path

from kivy.factory import Factory
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.screenmanager import SlideTransition

from model.componentes import CartaoInterativo, CartaoMaterial, LayoutFundo


PROJECT_DIR = Path(__file__).resolve().parents[1]


def _icone_do_servico(filename: str) -> str:
    """Retorna um PNG personalizado quando ele estiver disponível na pasta de ícones."""
    relative_path = f"assets/icon/{filename}"
    return relative_path if (PROJECT_DIR / relative_path).is_file() else ""


class AtalhoNavegador(CartaoInterativo):
    """Botão visual para abrir um serviço pelo perfil temporário."""

    icone = StringProperty("")
    simbolo = StringProperty("apps")
    titulo = StringProperty("")


class AreaNavegador(CartaoMaterial):
    """Área de aplicativos web abertos em janelas isoladas do navegador."""

    status_texto = StringProperty("Perfil temporário pronto para o navegador.")
    profile_path = StringProperty("")
    browser_pronto = BooleanProperty(False)

    def configurar_browser(self) -> None:
        """Confirma que o perfil temporário do navegador está disponível."""
        app = App.get_running_app()
        self.profile_path = str(app.browser_manager.get_profile_path())
        self.status_texto = "Perfil temporário do navegador ativo para esta execução."
        self.browser_pronto = True
        self.atualizar_atalhos()

    def atualizar_atalhos(self, *_args: object) -> None:
        """Reconstrói somente os atalhos habilitados na preferência central."""
        if "shortcuts_grid" not in self.ids:
            return
        app = App.get_running_app()
        shortcuts = (
            ("show_google", "Chrome", "google.png", "google-chrome", self.abrir_navegador),
            ("show_youtube", "YouTube", "youtube.png", "youtube", partial(self.abrir_atalho, "https://www.youtube.com/")),
            ("show_outlook", "Outlook", "outlook.png", "microsoft-outlook", partial(self.abrir_atalho, "https://outlook.office.com/")),
            ("show_teams", "Teams", "teams.png", "microsoft-teams", partial(self.abrir_atalho, "https://teams.microsoft.com/")),
            ("show_word", "Word", "word.png", "microsoft-word", partial(self.abrir_atalho, "https://www.office.com/launch/word")),
            ("show_excel", "Excel", "excel.png", "microsoft-excel", partial(self.abrir_atalho, "https://www.office.com/launch/excel")),
            ("show_onedrive", "OneDrive", "onedrive.png", "microsoft-onedrive", partial(self.abrir_atalho, "https://www.office.com/launch/onedrive")),
            ("show_google_drive", "Google Drive", "google_drive.png", "google-drive", partial(self.abrir_atalho, "https://drive.google.com/")),
            ("show_classroom", "Classroom", "classroom.png", "google-classroom", partial(self.abrir_atalho, "https://classroom.google.com/")),
            ("show_github", "GitHub", "github.png", "github", partial(self.abrir_atalho, "https://github.com/")),
            ("show_discord", "Discord", "discord.png", "message-text-outline", partial(self.abrir_atalho, "https://discord.com/app")),
            ("show_git", "Git Bash", "git.png", "console-line", self.abrir_git_bash),
            ("show_google_calendar", "Google Agenda", "google_calendar.png", "calendar-month-outline", partial(self.abrir_atalho, "https://calendar.google.com/")),
            ("show_google_meet", "Google Meet", "google_meet.png", "video-outline", partial(self.abrir_atalho, "https://meet.google.com/")),
            ("show_google_docs", "Google Docs", "google_docs.png", "file-document-outline", partial(self.abrir_atalho, "https://docs.google.com/document/")),
            ("show_google_slides", "Google Slides", "google_slides.png", "presentation", partial(self.abrir_atalho, "https://slides.google.com/")),
            ("show_google_forms", "Google Forms", "google_forms.png", "clipboard-list-outline", partial(self.abrir_atalho, "https://forms.google.com/")),
            ("show_google_maps", "Google Maps", "google_maps.png", "map-marker-outline", partial(self.abrir_atalho, "https://maps.google.com/")),
            ("show_google_keep", "Google Keep", "google_keep.png", "note-text-outline", partial(self.abrir_atalho, "https://keep.google.com/")),
            ("show_canva", "Canva", "canva.png", "palette-outline", partial(self.abrir_atalho, "https://www.canva.com/")),
            ("show_notion", "Notion", "notion.png", "notebook-outline", partial(self.abrir_atalho, "https://www.notion.so/")),
            ("show_trello", "Trello", "trello.png", "view-column-outline", partial(self.abrir_atalho, "https://trello.com/")),
        )
        grid = self.ids.shortcuts_grid
        grid.clear_widgets()
        for setting, title, icon_filename, symbol, callback in shortcuts:
            if not getattr(app.settings, setting):
                continue
            icon = _icone_do_servico(icon_filename)
            button = Factory.AtalhoNavegador(titulo=title, icone=icon, simbolo=symbol)
            button.bind(on_release=lambda _button, action=callback: action())
            grid.add_widget(button)

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
        app = App.get_running_app()
        if app.feature_blocked_for_current_user():
            self.status_texto = "O Git Bash está bloqueado pelas regras deste laboratório."
            app._show_message("Função bloqueada", self.status_texto)
            return
        try:
            app.git_bash_manager.open_git_bash()
            self.status_texto = "Git Bash aberto com perfil temporário."
        except (RuntimeError, ValueError) as error:
            self.status_texto = str(error)


class TelaPrincipal(LayoutFundo):
    """Tela principal que constrói os cartões a partir da configuração do menu."""

    is_moderator = BooleanProperty(False)

    def on_kv_post(self, _base_widget) -> None:
        self.refresh_access()
        self.ids.browser_area.configurar_browser()
        settings = App.get_running_app().settings
        for field in (
            "show_google", "show_youtube", "show_outlook", "show_git", "show_classroom",
            "show_teams", "show_word", "show_excel", "show_onedrive", "show_google_drive",
            "show_discord", "show_github", "show_google_calendar", "show_google_meet",
            "show_google_docs", "show_google_slides", "show_google_forms", "show_google_maps",
            "show_google_keep", "show_canva", "show_notion", "show_trello",
        ):
            settings.bind(**{field: self.ids.browser_area.atualizar_atalhos})

    def refresh_access(self) -> None:
        app = App.get_running_app()
        self.is_moderator = app.permission_service.perfil_pode_gerenciar_usuarios(
            app.session_manager.user
        )

    def atualizar_foto_perfil(self, caminho: str) -> None:
        """Encaminha a foto local para o cabeçalho da tela principal."""
        if caminho:
            self.ids.cabecalho.atualizar_foto_perfil(caminho)

    def abrir_configuracoes(self) -> None:
        """Vai para a tela de extensões e configurações a partir do primeiro card."""
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="left", duration=0.25)
        manager.current = "configuracoes"

    def abrir_extensoes(self) -> None:
        app = App.get_running_app()
        if app.feature_blocked_for_current_user():
            app._show_message(
                "Função bloqueada",
                "O catálogo de extensões está bloqueado para alunos neste laboratório.",
            )
            return
        manager = app.root
        manager.transition = SlideTransition(direction="left", duration=0.25)
        manager.get_screen("extensoes").children[0].atualizar()
        manager.current = "extensoes"

    def abrir_usuarios(self) -> None:
        app = App.get_running_app()
        if not app.permission_service.perfil_pode_gerenciar_usuarios(app.session_manager.user):
            return
        manager = app.root
        manager.transition = SlideTransition(direction="left", duration=0.25)
        manager.get_screen("usuarios").children[0].atualizar()
        manager.current = "usuarios"

    def abrir_perfil(self) -> None:
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="left", duration=0.25)
        manager.get_screen("perfil").children[0].atualizar()
        manager.current = "perfil"

    def abrir_materias(self, secao: str = "feed") -> None:
        """Abre o módulo local de conteúdos teóricos e didáticos."""
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="left", duration=0.25)
        tela = manager.get_screen("materias").children[0]
        tela.atualizar(secao)
        manager.current = "materias"

    def abrir_praticas(self) -> None:
        """Abre o catálogo fixo de laboratórios práticos do sistema."""
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="left", duration=0.25)
        manager.current = "praticas"
