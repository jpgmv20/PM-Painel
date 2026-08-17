"""Tela e ações de configurações do PM-Painel."""

from __future__ import annotations

from kivy.app import App
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition

import model.componentes as componentes


class TelaConfiguracoes(componentes.LayoutFundo):
    """Interface das preferências persistentes, sem assumir serviços inexistentes."""

    titulo = StringProperty("Configurações")
    update_status = StringProperty("")

    def set_boolean(self, field: str, value: bool) -> None:
        App.get_running_app().settings.set_value(field, value)

    def set_choice(self, field: str, value: str) -> None:
        App.get_running_app().settings.set_value(field, value)

    def verificar_atualizacoes(self) -> None:
        """Ponto de integração para um futuro serviço real de atualização."""
        self.update_status = "Verificador de atualizações será conectado em uma versão futura."

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

    def on_active(self, _instance: object, value: bool) -> None:
        if self.key:
            App.get_running_app().settings.set_value(self.key, value)


class ServicoOpcao(BoxLayout):
    """Card compacto para exibir ou ocultar um atalho da Home."""

    titulo = StringProperty("")
    descricao = StringProperty("")
    simbolo = StringProperty("")
    key = StringProperty("")
    active = BooleanProperty(False)

    def on_active(self, _instance: object, value: bool) -> None:
        if self.key:
            App.get_running_app().settings.set_value(self.key, value)
