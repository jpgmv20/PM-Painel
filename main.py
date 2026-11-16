"""Ponto de entrada do PM-Painel."""

import os
from pathlib import Path
import sys
import threading

from kivy.config import Config

# Estas opções precisam ser definidas antes de importar os módulos visuais do Kivy.
Config.set("graphics", "fullscreen", "auto")
Config.set("graphics", "resizable", "0")

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivymd.app import MDApp

import model.componentes as componentes
from model.configuracoes import TelaConfiguracoes
from model.home import TelaPrincipal
from model.login import TelaLogin
from model.tela_materias import TelaEquipe, TelaMaterias
from model.praticas import TelaPraticas
from model.extensoes import TelaExtensoes
from model.perfil import TelaPerfil
from model.usuarios import TelaUsuarios
from model.docker_erro import TelaDockerErro
from service.git_bash import GitBashManager
from service.materias import MateriasService
from service.permissoes import Papel, PermissionService
from service.login.authentication import AuthenticationService
from service.login.users import LocalUserStore
from service.extensions import ExtensionsService
from service.network import InternetService
from service.web.browser import BrowserManager
from service.login.google_auth import GoogleAuth
from service.login.session import SessionManager
from service.settings import SettingsStore
from service.updates import UpdateService
from service.translations import translate
from service.windows_startup import WindowsStartupService
from service.windows_tray import WindowsTrayService
from service.docker_service import DockerService


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
resource_add_path(PROJECT_DIR)
if getattr(sys, "_MEIPASS", None):
    resource_add_path(str(Path(sys._MEIPASS)))

FONT_DIR = Path(getattr(sys, "_MEIPASS", PROJECT_DIR)) / "assets" / "fonts"
LabelBase.register(
    name="Nunito",
    fn_regular=str(FONT_DIR / "Nunito-Regular.ttf"),
    fn_bold=str(FONT_DIR / "Nunito-Bold.ttf"),
    fn_italic=str(FONT_DIR / "Nunito-Regular.ttf"),
    fn_bolditalic=str(FONT_DIR / "Nunito-Bold.ttf"),
)
LabelBase.register(
    name="NunitoSemiBold",
    fn_regular=str(FONT_DIR / "Nunito-SemiBold.ttf"),
    fn_bold=str(FONT_DIR / "Nunito-Bold.ttf"),
    fn_italic=str(FONT_DIR / "Nunito-SemiBold.ttf"),
    fn_bolditalic=str(FONT_DIR / "Nunito-Bold.ttf"),
)
LabelBase.register(
    name="Roboto",
    fn_regular=str(FONT_DIR / "Nunito-Regular.ttf"),
    fn_bold=str(FONT_DIR / "Nunito-Bold.ttf"),
    fn_italic=str(FONT_DIR / "Nunito-Regular.ttf"),
    fn_bolditalic=str(FONT_DIR / "Nunito-Bold.ttf"),
)
LabelBase.register(
    name="RobotoMedium",
    fn_regular=str(FONT_DIR / "Nunito-SemiBold.ttf"),
    fn_bold=str(FONT_DIR / "Nunito-Bold.ttf"),
)
LabelBase.register(
    name="RobotoLight",
    fn_regular=str(FONT_DIR / "Nunito-Regular.ttf"),
)

# Carrega primeiro os widgets reutilizáveis e depois as telas que os utilizam.
for view_name in (
    "componentes.kv", "main.kv", "login.kv", "home.kv", "configuracoes.kv",
    "materias.kv", "usuarios.kv", "extensoes.kv", "perfil.kv", "docker_erro.kv",
):
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
    settings_feedback = StringProperty("")
    update_status = StringProperty("")
    latest_update_url = StringProperty("")
    font_family = StringProperty("Nunito")
    font_family_medium = StringProperty("NunitoSemiBold")
    is_moderator = BooleanProperty(False)
    theme_surface = ListProperty([.95, .97, 1, 1])
    theme_text = ListProperty([.06, .10, .18, 1])
    theme_muted = ListProperty([.37, .43, .53, 1])

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "900"
        self.theme_cls.accent_palette = "LightBlue"
        self.theme_cls.font_styles = {
            style: [
                "NunitoSemiBold" if values[0] == "RobotoMedium" else (
                    "Nunito" if values[0] in {"Roboto", "RobotoLight"} else values[0]
                ),
                *values[1:],
            ]
            for style, values in self.theme_cls.font_styles.items()
        }
        local_app_data = os.environ.get("LOCALAPPDATA")
        self.data_dir = (
            Path(local_app_data) / "PM-Painel" if local_app_data else Path(self.user_data_dir)
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings = SettingsStore(path=self.data_dir / "settings.json")
        if self.settings.start_in_lab_mode and not self.settings.laboratory_mode:
            self.settings.laboratory_mode = True
        self.materias_service = MateriasService(path=self.data_dir / "materias.json")
        self.permission_service = PermissionService()
        self.internet_service = InternetService()
        self.extensions_service = ExtensionsService(path=self.data_dir / "extensions.json")
        self.user_store = LocalUserStore(path=self.data_dir / "users.json")
        self.browser_manager = BrowserManager(
            cleanup_abandoned_profiles=self.settings.clear_abandoned_sessions,
            prevent_login_persistence=self.settings.prevent_login_persistence,
            persistent_profile_dir=self.data_dir / "browser-profile",
        )
        self.git_bash_manager = GitBashManager(
            cleanup_abandoned_profiles=self.settings.clear_abandoned_sessions,
        )
        self.docker_service = DockerService()
        self.session_manager = SessionManager(path=self.data_dir / "offline_session.json")
        self.update_service = UpdateService(self.data_dir, PROJECT_DIR)
        self.startup_service = WindowsStartupService()
        self.tray_service: WindowsTrayService | None = None
        self._app_started = False
        self._exit_dialog: Popup | None = None
        self._session_timeout = None
        self._reverting_startup = False
        self._reverting_tray = False
        self._language_states: dict[object, tuple[str, str]] = {}
        self._language_bound: set[tuple[int, str]] = set()
        self._language_mutating: set[object] = set()
        self.google_auth = GoogleAuth()
        self.authentication_service = AuthenticationService(
            google_auth=self.google_auth,
            session_manager=self.session_manager,
            browser_manager=self.browser_manager,
            user_store=self.user_store,
            internet_service=self.internet_service,
        )
        self.settings.bind(fullscreen=self._apply_fullscreen)
        self.settings.bind(theme=self._apply_theme)
        self.settings.bind(start_with_windows=self._sync_windows_startup)
        self.settings.bind(minimize_to_tray=self._sync_tray_setting)
        self.settings.bind(prevent_login_persistence=self._sync_login_privacy)
        self.settings.bind(start_in_lab_mode=self._apply_lab_startup)
        self.settings.bind(laboratory_mode=self._refresh_session_timeout)
        self.settings.bind(maximum_session_time=self._refresh_session_timeout)
        self.settings.bind(language=self._apply_language)
        self.settings.bind(auto_check_updates=self._on_auto_check_changed)
        self.settings.bind(auto_download_updates=self._on_auto_download_changed)
        self.settings.bind(update_channel=self._on_update_channel_changed)
        Window.title = "PM-Painel"
        self._apply_fullscreen(self.settings, self.settings.fullscreen)
        self._apply_theme(self.settings, self.settings.theme)
        self._sync_windows_startup(self.settings, self.settings.start_with_windows)

    def on_start(self) -> None:
        self._app_started = True
        Window.bind(on_request_close=self._on_window_close)
        try:
            Window.bind(on_minimize=self._on_window_minimize)
        except Exception:
            pass
        self._sync_tray_setting(self.settings, self.settings.minimize_to_tray)
        Clock.schedule_once(lambda _dt: self._translate_tree(self.root), 0)
        Clock.schedule_once(self._check_updates_at_startup, 1)
        Clock.schedule_once(lambda _dt: self._refresh_session_timeout(self.settings, self.settings.laboratory_mode), 0)

    def on_stop(self) -> None:
        """Encerra recursos temporários e respeita as políticas de limpeza."""
        if self._session_timeout is not None:
            self._session_timeout.cancel()
            self._session_timeout = None
        if self.tray_service is not None:
            self.tray_service.stop()
            self.tray_service = None
        if self.settings.clear_sessions_on_exit:
            self.session_manager.clear(preserve_offline_token=False)
            self.google_auth.logout()
        self.browser_manager.shutdown(remove_profile=self.settings.clear_temporary_browser)
        self.git_bash_manager.shutdown()

    @staticmethod
    def _apply_fullscreen(_settings: SettingsStore, enabled: bool) -> None:
        """Aplica imediatamente a única preferência de computador suportada pelo app."""
        Window.fullscreen = "auto" if enabled else False

    def _apply_theme(self, _settings: SettingsStore, theme: str) -> None:
        is_light = theme.casefold() in {"claro", "light"}
        self.theme_cls.theme_style = "Light" if is_light else "Dark"
        if is_light:
            self.theme_surface = [.95, .97, 1, 1]
            self.theme_text = [.06, .10, .18, 1]
            self.theme_muted = [.37, .43, .53, 1]
            Window.clearcolor = [.92, .95, .99, 1]
        else:
            self.theme_surface = [.10, .14, .21, 1]
            self.theme_text = [.91, .94, .99, 1]
            self.theme_muted = [.67, .73, .83, 1]
            Window.clearcolor = [.035, .055, .09, 1]

    def _sync_windows_startup(self, _settings: SettingsStore, enabled: bool) -> None:
        if self._reverting_startup:
            return
        try:
            self.startup_service.set_enabled(enabled)
            if self._app_started or enabled:
                self.settings_feedback = "Inicialização do Windows atualizada."
        except (OSError, ImportError) as error:
            if enabled and self.settings.start_with_windows:
                self._reverting_startup = True
                self.settings.start_with_windows = False
                self._reverting_startup = False
            self.settings_feedback = str(error)

    def _sync_login_privacy(self, _settings: SettingsStore, enabled: bool) -> None:
        self.browser_manager.prevent_login_persistence = bool(enabled)

    def _apply_lab_startup(self, _settings: SettingsStore, enabled: bool) -> None:
        if enabled and not self.settings.laboratory_mode:
            self.settings.laboratory_mode = True

    def _sync_tray_setting(self, _settings: SettingsStore, enabled: bool) -> None:
        if self._reverting_tray:
            return
        if not self._app_started:
            return
        if not enabled:
            had_service = self.tray_service is not None
            if had_service:
                self.tray_service.stop()
                self.tray_service = None
            if had_service:
                self.settings_feedback = "Minimização para a bandeja desativada."
            return
        if self.tray_service is not None and self.tray_service.running:
            return
        try:
            self.tray_service = WindowsTrayService(self._restore_from_tray, self.solicitar_saida)
            self.settings_feedback = "Ícone do PM-Painel disponível na bandeja do Windows."
        except (OSError, RuntimeError, ImportError) as error:
            self._reverting_tray = True
            self.settings.minimize_to_tray = False
            self._reverting_tray = False
            self.settings_feedback = str(error)

    def _on_window_minimize(self, *_args: object) -> None:
        if self.settings.minimize_to_tray and self.tray_service is not None:
            self.tray_service.minimize()

    def _restore_from_tray(self) -> None:
        if self.tray_service is not None:
            self.tray_service.restore()
        try:
            Window.restore()
        except Exception:
            pass

    def _is_moderator(self) -> bool:
        return self.permission_service.perfil_pode_gerenciar_usuarios(self.session_manager.user)

    def user_is_moderator(self) -> bool:
        return bool(self.is_moderator)

    def refresh_user_role(self) -> None:
        self.is_moderator = self._is_moderator()

    def _blocks_current_user(self) -> bool:
        return (
            self.settings.laboratory_mode
            and self.settings.block_app_close
            and self.permission_service.papel_do_perfil(self.session_manager.user) == Papel.ALUNO
        )

    def _on_window_close(self, *_args: object) -> bool:
        if self._blocks_current_user():
            self._show_message(
                "Fechamento bloqueado",
                "O modo laboratório impede o encerramento para alunos. Solicite ao moderador.",
            )
            return True
        if self.settings.minimize_to_tray and self.tray_service is not None:
            self.tray_service.minimize()
            return True
        if self.settings.confirm_before_close:
            self._confirm_exit()
            return True
        return False

    def solicitar_saida(self, *_args: object) -> None:
        if self._blocks_current_user():
            self._show_message(
                "Fechamento bloqueado",
                "O modo laboratório impede o encerramento para alunos. Solicite ao moderador.",
            )
            return
        if self.settings.confirm_before_close:
            self._confirm_exit()
        else:
            self.stop()

    def _confirm_exit(self) -> None:
        if self._exit_dialog is not None:
            return
        content = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(14))
        content.add_widget(Label(
            text=translate("Deseja realmente encerrar o PM-Painel?", self.settings.language),
            color=tuple(self.theme_text), halign="center", valign="middle",
        ))
        actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(10))
        dialog = Popup(
            title=translate("Confirmar saída", self.settings.language), content=content, size_hint=(.48, .28),
            title_color=tuple(self.theme_text), separator_color=(.11, .42, .82, 1),
            background_color=tuple(self.theme_surface),
        )
        exit_button = componentes.BotaoAcao(text=translate("Sair", self.settings.language), variant="danger")
        cancel = componentes.BotaoAcao(
            text=translate("Continuar usando", self.settings.language),
            variant="secondary",
            icon_position="right",
            icone="arrow-right",
        )

        def close_dialog(*_args: object) -> None:
            dialog.dismiss()
            self._exit_dialog = None

        cancel.bind(on_release=close_dialog)
        exit_button.bind(on_release=lambda *_: (close_dialog(), self.stop()))
        actions.add_widget(exit_button)
        actions.add_widget(cancel)
        content.add_widget(actions)
        self._exit_dialog = dialog
        dialog.bind(on_dismiss=lambda *_: setattr(self, "_exit_dialog", None))
        dialog.open()

    def _show_message(self, title: str, message: str) -> None:
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(Label(text=translate(message, self.settings.language), color=tuple(self.theme_text), halign="center", valign="middle"))
        button = componentes.BotaoAcao(text=translate("Entendi", self.settings.language), variant="primary", size_hint_y=None, height=dp(46))
        popup = Popup(title=translate(title, self.settings.language), content=content, size_hint=(.56, .32), title_color=tuple(self.theme_text), background_color=tuple(self.theme_surface))
        button.bind(on_release=popup.dismiss)
        content.add_widget(button)
        popup.open()

    def feature_blocked_for_current_user(self) -> bool:
        return (
            self.settings.laboratory_mode
            and self.settings.block_restricted_features
            and self.permission_service.papel_do_perfil(self.session_manager.user) == Papel.ALUNO
        )

    def iniciar_limite_sessao(self) -> None:
        self._refresh_session_timeout(self.settings, self.settings.laboratory_mode)

    def _refresh_session_timeout(self, _settings: SettingsStore, _value: object) -> None:
        if self._session_timeout is not None:
            self._session_timeout.cancel()
            self._session_timeout = None
        if not self._app_started or not self.settings.laboratory_mode or not self.session_manager.is_authenticated:
            return
        minutes = {
            "30 minutos": 30,
            "1 hora": 60,
            "2 horas": 120,
            "4 horas": 240,
            "8 horas": 480,
        }.get(self.settings.maximum_session_time)
        if minutes is not None:
            self._session_timeout = Clock.schedule_once(self._expire_laboratory_session, minutes * 60)

    def _expire_laboratory_session(self, _dt: float) -> None:
        self._session_timeout = None
        self.authentication_service.logout()
        self.refresh_user_role()
        self.set_profile_photo()
        if self.root is not None and "login" in self.root.screen_names:
            login = self.root.get_screen("login").children[0]
            login.status_texto = "Sessão encerrada pelo limite de tempo do laboratório."
            login.status_cor = [.9, .48, .12, 1]
            self.root.transition = SlideTransition(direction="right", duration=.25)
            self.root.current = "login"
        self._show_message("Sessão encerrada", "O limite de tempo do modo laboratório foi atingido.")

    def check_for_updates(self, *, automatic: bool = False) -> None:
        if automatic and not self.settings.auto_check_updates:
            return
        if self.settings.offline_mode:
            self.update_status = "A verificação de atualizações está indisponível no modo offline."
            self.latest_update_url = ""
            return

        channel = self.settings.update_channel
        should_download = self.settings.auto_download_updates
        install_next_start = self.settings.install_updates_on_restart

        def worker() -> None:
            try:
                result = self.update_service.check(channel)
                message = result["message"]
                if result.get("available") and should_download:
                    try:
                        path = self.update_service.download(result)
                        if install_next_start:
                            message += f" Instalador verificado; será aberto na próxima inicialização: {path.name}."
                        else:
                            message += f" Instalador verificado salvo: {path.name}. Ative 'Instalar ao reiniciar' para abri-lo na próxima inicialização."
                    except (OSError, RuntimeError, KeyError) as error:
                        message += f" Download não concluído: {error}"
                elif result.get("available"):
                    message += " Consulte o link de lançamento para baixar manualmente."
                update_link = result.get("url", "")
            except (OSError, RuntimeError, ValueError) as error:
                message = str(error)
                update_link = ""

            def apply_result(_dt: float) -> None:
                self.update_status = message
                self.settings_feedback = message
                self.latest_update_url = update_link
            Clock.schedule_once(apply_result, 0)

        threading.Thread(target=worker, name="PM-Painel-UpdateCheck", daemon=True).start()

    def _check_updates_at_startup(self, _dt: float) -> None:
        if self.settings.auto_check_updates:
            self.check_for_updates(automatic=True)

    def _on_auto_check_changed(self, _settings: SettingsStore, enabled: bool) -> None:
        if enabled and self._app_started:
            self.check_for_updates(automatic=True)

    def _on_auto_download_changed(self, _settings: SettingsStore, enabled: bool) -> None:
        if enabled and self._app_started and self.settings.auto_check_updates:
            self.check_for_updates(automatic=True)

    def _on_update_channel_changed(self, _settings: SettingsStore, _channel: str) -> None:
        if self._app_started and self.settings.auto_check_updates:
            self.check_for_updates(automatic=True)

    def _apply_language(self, _settings: SettingsStore, _language: str) -> None:
        if self.root is not None:
            Clock.schedule_once(lambda _dt: self._translate_tree(self.root), 0)

    def _translate_tree(self, widget: object) -> None:
        if widget is None:
            return
        for attribute in ("text", "titulo", "descricao", "hint_text"):
            if hasattr(widget, attribute):
                self._translate_widget_property(widget, attribute, str(getattr(widget, attribute)))
                binding = (id(widget), attribute)
                if binding not in self._language_bound:
                    widget.bind(**{
                        attribute: lambda item, value, name=attribute: self._translate_widget_property(item, name, value)
                    })
                    self._language_bound.add(binding)
        if hasattr(widget, "children"):
            binding = (id(widget), "children")
            if binding not in self._language_bound:
                widget.bind(children=lambda item, _children: self._translate_tree(item))
                self._language_bound.add(binding)
            for child in tuple(widget.children):
                self._translate_tree(child)

    def _translate_widget_property(self, widget: object, attribute: str, value: str) -> None:
        key = (widget, attribute)
        if key in self._language_mutating:
            return
        previous = self._language_states.get(key)
        original = previous[0] if previous is not None and value == previous[1] else str(value)
        translated = translate(original, self.settings.language)
        self._language_states[key] = (original, translated)
        if value != translated:
            self._language_mutating.add(key)
            setattr(widget, attribute, translated)
            self._language_mutating.discard(key)

    def build(self) -> ScreenManager:
        manager = ScreenManager(transition=SlideTransition(direction="right", duration=0.25))
        offline_start = self.settings.offline_mode or not self.internet_service.online()
        restored_offline = self.session_manager.restore_offline_session() if offline_start else False
        self.refresh_user_role()
        for name, widget in (
            ("home", TelaInicial()),
            ("login", TelaLogin()),
            ("principal", TelaPrincipal()),
            ("configuracoes", TelaConfiguracoes()),
            ("materias", TelaMaterias()),
            ("praticas", TelaPraticas()),
            ("equipe", TelaEquipe()),
            ("usuarios", TelaUsuarios()),
            ("extensoes", TelaExtensoes()),
            ("perfil", TelaPerfil()),
            ("docker_erro", TelaDockerErro()),
        ):
            screen = Screen(name=name)
            screen.add_widget(widget)
            manager.add_widget(screen)

        if self.session_manager.is_authenticated:
            destino_inicial = "principal"
        elif self.settings.start_after_login:
            destino_inicial = "login"
        else:
            destino_inicial = "home"

        if offline_start and not restored_offline:
            login = manager.get_screen("login").children[0]
            login.status_texto = "Sem conexão: o passe offline expirou. Conecte-se para entrar novamente."
            login.status_cor = [.9, .48, .12, 1]

        if self.settings.check_docker_on_startup:
            docker_ok, docker_msg = self.docker_service.is_running(timeout=2.0)
            if not docker_ok:
                tela_docker = manager.get_screen("docker_erro").children[0]
                tela_docker.configurar(
                    destino_pos_sucesso=destino_inicial,
                    detalhe=docker_msg,
                )
                manager.current = "docker_erro"
                return manager

        manager.current = destino_inicial
        if destino_inicial == "principal":
            Clock.schedule_once(lambda _dt: self.iniciar_limite_sessao(), 0)
        return manager

    def set_profile_photo(self, path: str | None = None) -> None:
        """Atualiza todos os cabeçalhos por meio de uma única propriedade reativa."""
        self.profile_photo = path or "assets/icon/user_icon.png"

if __name__ == "__main__":
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    data_dir = local_app_data / "PM-Painel"
    saved_settings = SettingsStore(path=data_dir / "settings.json")
    pending_updates = UpdateService(data_dir, PROJECT_DIR)
    if not (saved_settings.install_updates_on_restart and pending_updates.launch_pending_installer()):
        MeuApp().run()
