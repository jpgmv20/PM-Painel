"""Tela e ações de configurações do PM-Painel."""

from __future__ import annotations

import platform
import socket
import webbrowser

from kivy.app import App
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition

import model.componentes as componentes


class TelaConfiguracoes(componentes.LayoutFundo):
    """Interface das preferências persistentes e do estado dos serviços."""

    titulo = StringProperty("Configurações")
    update_status = StringProperty("")
    computer_info = StringProperty("")
    latest_update_url = StringProperty("")

    def on_kv_post(self, _base_widget: object) -> None:
        app = App.get_running_app()
        self.computer_info = self._computer_summary()
        app.settings.bind(show_computer_info=self._refresh_computer_summary)
        app.settings.bind(language=self._refresh_computer_language)
        app.bind(update_status=self._sync_update_status)
        app.bind(latest_update_url=self._sync_update_link)
        self.update_status = app.update_status
        self.latest_update_url = app.latest_update_url

    def set_boolean(self, field: str, value: bool) -> None:
        App.get_running_app().settings.set_value(field, value)

    def set_choice(self, field: str, value: str) -> None:
        if field == "maximum_session_time":
            value = {
                "30 minutes": "30 minutos",
                "1 hour": "1 hora",
                "2 hours": "2 horas",
                "4 hours": "4 horas",
                "8 hours": "8 horas",
                "Unlimited": "Ilimitado",
            }.get(value, value)
        App.get_running_app().settings.set_value(field, value)

    @staticmethod
    def session_time_label(value: str, language: str) -> str:
        if language.casefold().startswith("english"):
            return {
                "30 minutos": "30 minutes",
                "1 hora": "1 hour",
                "2 horas": "2 hours",
                "4 horas": "4 hours",
                "8 horas": "8 hours",
                "Ilimitado": "Unlimited",
            }.get(value, value)
        return value

    def verificar_atualizacoes(self) -> None:
        """Consulta o canal publicado sem bloquear a interface."""
        app = App.get_running_app()
        app.check_for_updates()

    def abrir_pagina_atualizacoes(self) -> None:
        if self.latest_update_url:
            webbrowser.open(self.latest_update_url, new=2)

    def _refresh_computer_summary(self, _settings: object, enabled: bool) -> None:
        if enabled:
            self.computer_info = self._computer_summary()
        else:
            self.computer_info = ""

    def _refresh_computer_language(self, _settings: object, _language: str) -> None:
        if App.get_running_app().settings.show_computer_info:
            self.computer_info = self._computer_summary()

    def _sync_update_status(self, app: object, status: str) -> None:
        self.update_status = status

    def _sync_update_link(self, app: object, url: str) -> None:
        self.latest_update_url = url

    @staticmethod
    def _computer_summary() -> str:
        name = socket.gethostname()
        system = f"{platform.system()} {platform.release()}"
        memory = ""
        try:
            import psutil
            total_gb = psutil.virtual_memory().total / (1024 ** 3)
            memory = f" • Memória: {total_gb:.0f} GB"
        except ImportError:
            pass
        app = App.get_running_app()
        if app.settings.language.casefold().startswith("english"):
            return f"Device: {name} • System: {system}{memory.replace('Memória', 'Memory')}"
        return f"Dispositivo: {name} • Sistema: {system}{memory}"

    def voltar_para_painel(self, _instance: object) -> None:
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="right", duration=0.25)
        manager.current = "principal" if "principal" in manager.screen_names else "home"


class ConfiguracaoOpcao(BoxLayout):
    """Linha reutilizável para uma preferência com switch."""

    titulo = StringProperty("")
    descricao = StringProperty("")
    aviso = StringProperty("")
    key = StringProperty("")
    active = BooleanProperty(False)
    admin_only = BooleanProperty(False)

    def on_active(self, _instance: object, value: bool) -> None:
        if self.key:
            app = App.get_running_app()
            if self.admin_only and not app.user_is_moderator():
                return
            app.settings.set_value(self.key, value)


class ServicoOpcao(BoxLayout):
    """Card compacto para exibir ou ocultar um atalho da Home."""

    titulo = StringProperty("")
    descricao = StringProperty("")
    imagem = StringProperty("")
    simbolo = StringProperty("")
    key = StringProperty("")
    active = BooleanProperty(False)

    def on_active(self, _instance: object, value: bool) -> None:
        if self.key:
            App.get_running_app().settings.set_value(self.key, value)
