"""Catálogo e painel de execução de extensões locais."""

from __future__ import annotations

from pathlib import Path

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import SlideTransition

from model.componentes import BotaoAcao, CampoTexto, LayoutFundo


class TelaExtensoes(LayoutFundo):
    """Apresenta extensões submetidas e limita aprovação a professores e moderadores."""

    def on_kv_post(self, _base_widget):
        self.atualizar()

    @property
    def _app(self):
        return App.get_running_app()

    def voltar(self):
        self._app.root.transition = SlideTransition(direction="right", duration=.25)
        self._app.root.current = "principal"

    def atualizar(self):
        profile = self._app.session_manager.user or {}
        role = self._app.permission_service.papel_do_perfil(profile)
        self.ids.extension_status.text = (
            f"Catálogo neste computador • perfil: {role.value} • "
            + ("conectado" if self._online() else "sem conexão")
        )
        area = self.ids.extension_list
        area.clear_widgets()
        entries = self._app.extensions_service.list_extensions()
        if not entries:
            area.add_widget(self._label(
                "Nenhuma extensão no catálogo. Envie um arquivo .py para revisão."
            ))
            return
        can_approve = self._app.permission_service.perfil_pode_aprovar_extensoes(profile)
        for extension in entries:
            card = BoxLayout(
                orientation="vertical", size_hint_y=None, height=dp(128),
                padding=dp(12), spacing=dp(4),
            )
            with card.canvas.before:
                from kivy.graphics import Color, RoundedRectangle
                Color(.055, .09, .15, 1)
                background = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
            card.bind(
                pos=lambda item, value, shape=background: setattr(shape, "pos", value),
                size=lambda item, value, shape=background: setattr(shape, "size", value),
            )
            card.add_widget(self._label(
                f"{extension.get('name', 'Extensão')}  •  v{extension.get('version', '?')}  •  {extension.get('status', '').capitalize()}",
                bold=True,
            ))
            card.add_widget(self._label(extension.get("description") or "Sem descrição."))
            card.add_widget(self._label(f"Enviada por {extension.get('author', 'Usuário')}"))
            actions = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(8))
            status = extension.get("status")
            if status == "pendente" and can_approve:
                actions.add_widget(self._button(
                    "Aprovar", lambda ident=extension["id"]: self.aprovar(ident)
                ))
            if status == "aprovada":
                actions.add_widget(self._button(
                    "Instalar", lambda ident=extension["id"]: self.instalar(ident)
                ))
            if status == "instalada":
                actions.add_widget(self._button(
                    "Executar", lambda ident=extension["id"]: self.confirmar_execucao(ident)
                ))
            card.add_widget(actions)
            area.add_widget(card)

    def enviar_extensao(self):
        if self._app.feature_blocked_for_current_user():
            self._mensagem("Função bloqueada", "O envio de extensões está bloqueado para alunos neste laboratório.")
            return
        profile = self._app.session_manager.user
        if not profile:
            self._mensagem("Faça login", "Entre no PM-Painel antes de enviar uma extensão.")
            return
        name = CampoTexto(appearance="dark", hint_text="Nome", multiline=False, size_hint_y=None, height=dp(48))
        version = CampoTexto(appearance="dark", text="1.0", hint_text="Versão", multiline=False, size_hint_y=None, height=dp(48))
        description = CampoTexto(appearance="dark", hint_text="Descrição", multiline=True, size_hint_y=None, height=dp(112))
        requires_network = CheckBox(size_hint_x=None, width=dp(34), active=False)
        chooser = FileChooserListView(path=str(Path.home()), filters=["*.py"], multiselect=False)
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        for field in (name, version, description):
            content.add_widget(field)
        network_row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        network_row.add_widget(requires_network)
        network_row.add_widget(Label(
            text="Esta extensão precisa de internet para ser instalada",
            color=(.88, .93, 1, 1), halign="left",
        ))
        content.add_widget(network_row)
        content.add_widget(chooser)
        popup = Popup(
            title="Enviar extensão para revisão", content=content, size_hint=(.82, .86),
            title_color=(.90, .95, 1, 1), separator_color=(.11, .42, .82, 1),
        )

        def submit():
            if not chooser.selection:
                self._mensagem("Arquivo necessário", "Selecione um arquivo .py.")
                return
            try:
                self._app.extensions_service.submit(
                    name.text, version.text, description.text, chooser.selection[0],
                    profile.get("name") or profile.get("email") or "Usuário",
                    requires_network=requires_network.active,
                )
            except (OSError, ValueError) as error:
                self._mensagem("Não foi possível enviar", str(error))
                return
            popup.dismiss()
            self.atualizar()

        content.add_widget(self._button("Enviar para revisão", submit))
        popup.open()

    def aprovar(self, extension_id: str):
        profile = self._app.session_manager.user or {}
        if not self._app.permission_service.perfil_pode_aprovar_extensoes(profile):
            self._mensagem("Acesso restrito", "Apenas professores e moderadores aprovam extensões.")
            return
        try:
            self._app.extensions_service.approve(
                extension_id, profile.get("name") or profile.get("email") or "Professor"
            )
        except (KeyError, ValueError, OSError) as error:
            self._mensagem("Não foi possível aprovar", str(error))
            return
        self.atualizar()

    def instalar(self, extension_id: str):
        if self._app.feature_blocked_for_current_user():
            self._mensagem("Função bloqueada", "A instalação de extensões está bloqueada para alunos neste laboratório.")
            return
        item = next(
            (entry for entry in self._app.extensions_service.list_extensions() if entry["id"] == extension_id),
            {},
        )
        online = self._online()
        try:
            if item.get("requires_network", False):
                self._app.internet_service.require_online(
                    offline_mode=self._app.settings.offline_mode,
                    action="A instalação desta extensão",
                )
            self._app.extensions_service.install(extension_id, online=online)
        except (ConnectionError, FileNotFoundError, KeyError, ValueError, OSError) as error:
            self._mensagem("Não foi possível instalar", str(error))
            return
        self.atualizar()

    def confirmar_execucao(self, extension_id: str):
        if self._app.feature_blocked_for_current_user():
            self._mensagem("Função bloqueada", "A execução de extensões está bloqueada para alunos neste laboratório.")
            return
        item = next(
            (entry for entry in self._app.extensions_service.list_extensions() if entry["id"] == extension_id),
            {},
        )
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        content.add_widget(Label(
            text=f"Executar {item.get('name', 'esta extensão')}? O script terá acesso aos recursos do seu usuário neste computador.",
            color=(.08, .12, .20, 1), halign="left", valign="middle",
        ))
        popup = Popup(title="Confirmar execução", content=content, size_hint=(.62, .38))

        def run():
            try:
                pid = self._app.extensions_service.execute(extension_id)
            except (FileNotFoundError, KeyError, ValueError, OSError) as error:
                popup.dismiss()
                self._mensagem("Não foi possível executar", str(error))
                return
            popup.dismiss()
            self._mensagem("Extensão iniciada", f"Processo aberto (PID {pid}).")

        content.add_widget(self._button("Executar extensão", run))
        popup.open()

    def _online(self) -> bool:
        return not self._app.settings.offline_mode and self._app.internet_service.online()

    def _label(self, text: str, bold: bool = False) -> Label:
        label = Label(
            text=text, bold=bold, size_hint_y=None, height=dp(24),
            color=(.88, .93, 1, 1), halign="left", valign="middle",
        )
        label.bind(width=lambda item, width: setattr(item, "text_size", (width, None)))
        return label

    def _button(self, title: str, action) -> BotaoAcao:
        button = BotaoAcao(
            text=title, variant="primary", size_hint_y=None, height=dp(42),
            color=(1, 1, 1, 1),
        )
        button.bind(on_release=lambda _button: action())
        return button

    def _mensagem(self, title: str, text: str):
        Popup(
            title=title,
            content=Label(text=text, color=(.08, .12, .20, 1), halign="left", valign="middle"),
            size_hint=(.62, .36),
        ).open()
