from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import SlideTransition

import model.componentes as componentes


class TelaConfiguracoes(componentes.LayoutFundo):
    """Tela de ajustes básicos do painel."""

    titulo = StringProperty("Configurações")

    def voltar_para_painel(self, _instance: object) -> None:
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="right", duration=0.25)
        manager.current = "principal" if "principal" in manager.screen_names else "home"
