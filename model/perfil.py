"""Edição das informações básicas do perfil autenticado."""

from __future__ import annotations

from datetime import datetime

from kivy.app import App
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.screenmanager import SlideTransition

from model.componentes import LayoutFundo


class TelaPerfil(LayoutFundo):
    nome = StringProperty("")
    email = StringProperty("")
    papel = StringProperty("aluno")
    sessao_status = StringProperty("")
    mensagem = StringProperty("")

    def on_kv_post(self, _base_widget):
        self.atualizar()

    def atualizar(self):
        app = App.get_running_app()
        profile = app.session_manager.user or {}
        self.nome = profile.get("name", "")
        self.email = profile.get("email", "")
        self.papel = app.permission_service.papel_do_perfil(profile).value
        if app.session_manager.offline_expires_at:
            expires = datetime.fromisoformat(app.session_manager.offline_expires_at)
            self.sessao_status = f"Acesso offline disponível até {expires.astimezone().strftime('%d/%m/%Y às %H:%M')}"
        else:
            self.sessao_status = "Nenhuma sessão offline ativa."
        self.mensagem = ""
        if "nome_input" in self.ids:
            self.ids.nome_input.text = self.nome

    def salvar(self):
        try:
            updated = App.get_running_app().authentication_service.update_profile(
                App.get_running_app().session_manager.user or {},
                self.ids.nome_input.text,
            )
        except (ValueError, OSError, RuntimeError, PermissionError) as error:
            self.mensagem = str(error)
            return
        self.nome = updated.get("name", self.nome)
        self.mensagem = "Perfil atualizado neste dispositivo."

    def voltar(self):
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="right", duration=.25)
        manager.current = "principal"
