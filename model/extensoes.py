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

from kivy.uix.widget import Widget
from model.componentes import BotaoAcao, CampoTexto, LayoutFundo, IconeUI


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
            area.add_widget(self._card_vazio(
                "Nenhuma extensão cadastrada",
                "Envie um script Python (.py) para revisão do laboratório através do botão 'Enviar extensão' acima.",
                "puzzle-outline"
            ))
            return
        can_approve = self._app.permission_service.perfil_pode_aprovar_extensoes(profile)
        for extension in entries:
            area.add_widget(self._criar_cartao_extensao(extension, can_approve))

    def _criar_cartao_extensao(self, extension: dict, can_approve: bool) -> BoxLayout:
        from kivy.graphics import Color, RoundedRectangle, Line
        status = extension.get("status", "pendente").lower()
        status_display = status.capitalize()

        card = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(88),
            padding=(dp(16), dp(10)),
            spacing=dp(14),
        )
        with card.canvas.before:
            Color(0.06, 0.10, 0.18, 0.88)
            background = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
            Color(0.18, 0.32, 0.52, 0.45)
            border = Line(rounded_rectangle=(card.x, card.y, card.width, card.height, dp(12)), width=dp(1))

        card.bind(
            pos=lambda item, value, s=background, b=border: (
                setattr(s, "pos", value),
                setattr(b, "rounded_rectangle", (value[0], value[1], item.width, item.height, dp(12)))
            ),
            size=lambda item, value, s=background, b=border: (
                setattr(s, "size", value),
                setattr(b, "rounded_rectangle", (item.x, item.y, value[0], value[1], dp(12)))
            ),
        )

        # Avatar Ícone Extensão
        avatar = BoxLayout(size_hint=(None, None), size=(dp(44), dp(44)), pos_hint={"center_y": 0.5})
        with avatar.canvas.before:
            Color(0.12, 0.22, 0.38, 1)
            av_bg = RoundedRectangle(pos=avatar.pos, size=avatar.size, radius=[dp(22)])
            Color(0.28, 0.50, 0.82, 0.7)
            av_border = Line(rounded_rectangle=(avatar.x, avatar.y, avatar.width, avatar.height, dp(22)), width=dp(1.2))
        avatar.bind(
            pos=lambda item, value, s=av_bg, b=av_border: (
                setattr(s, "pos", value),
                setattr(b, "rounded_rectangle", (value[0], value[1], item.width, item.height, dp(22)))
            ),
            size=lambda item, value, s=av_bg, b=av_border: (
                setattr(s, "size", value),
                setattr(b, "rounded_rectangle", (item.x, item.y, value[0], value[1], dp(22)))
            ),
        )
        avatar.add_widget(IconeUI(nome="puzzle-outline", size_hint=(1, 1), font_size="22sp", color=(0.42, 0.78, 1, 1), halign="center", valign="middle"))
        card.add_widget(avatar)

        # Informações Centrais
        info_col = BoxLayout(orientation="vertical", spacing=dp(3), size_hint_x=1)
        top_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(26))
        lbl_nome = Label(
            text=extension.get("name", "Extensão"),
            bold=True,
            font_size="15sp",
            color=(0.92, 0.96, 1, 1),
            size_hint=(None, None),
            height=dp(24),
            halign="left",
            valign="middle"
        )
        lbl_nome.bind(texture_size=lambda item, size: setattr(item, "width", size[0]))
        top_row.add_widget(lbl_nome)

        # Versão badge
        ver_tag = self._badge_tag(f"v{extension.get('version', '1.0')}", (0.15, 0.32, 0.60, 0.28), (0.55, 0.82, 1, 1))
        top_row.add_widget(ver_tag)

        # Status badge
        if status == "instalada":
            st_tag = self._badge_tag("Instalada", (0.12, 0.65, 0.35, 0.28), (0.45, 0.95, 0.65, 1))
        elif status == "aprovada":
            st_tag = self._badge_tag("Aprovada", (0.15, 0.45, 0.85, 0.28), (0.50, 0.80, 1, 1))
        else:
            st_tag = self._badge_tag("Pendente", (0.75, 0.50, 0.10, 0.28), (1, 0.85, 0.45, 1))
        top_row.add_widget(st_tag)
        top_row.add_widget(Widget())
        info_col.add_widget(top_row)

        desc = extension.get("description") or "Sem descrição cadastrada."
        lbl_desc = Label(
            text=f"{desc}  •  Por {extension.get('author', 'Usuário')}",
            font_size="12sp",
            color=(0.60, 0.70, 0.85, 1),
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle"
        )
        lbl_desc.bind(size=lambda item, val: setattr(item, "text_size", val))
        info_col.add_widget(lbl_desc)

        card.add_widget(info_col)

        # Ações à direita (compactas)
        actions = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            height=dp(38),
            spacing=dp(8),
            pos_hint={"center_y": 0.5}
        )
        total_w = dp(0)

        if status == "pendente" and can_approve:
            btn_aprov = BotaoAcao(
                text="Aprovar",
                icone="check-circle-outline",
                variant="primary",
                size_hint=(None, None),
                size=(dp(120), dp(36)),
                font_size="11sp"
            )
            btn_aprov.bind(on_release=lambda _b, ident=extension["id"]: self.aprovar(ident))
            actions.add_widget(btn_aprov)
            total_w += dp(120)

        if status == "aprovada":
            btn_inst = BotaoAcao(
                text="Instalar",
                icone="download-outline",
                variant="primary",
                size_hint=(None, None),
                size=(dp(120), dp(36)),
                font_size="11sp"
            )
            btn_inst.bind(on_release=lambda _b, ident=extension["id"]: self.instalar(ident))
            actions.add_widget(btn_inst)
            total_w += dp(120)

        if status == "instalada":
            btn_exec = BotaoAcao(
                text="Executar",
                icone="play-outline",
                variant="primary",
                size_hint=(None, None),
                size=(dp(120), dp(36)),
                font_size="11sp"
            )
            btn_exec.bind(on_release=lambda _b, ident=extension["id"]: self.confirmar_execucao(ident))
            actions.add_widget(btn_exec)
            total_w += dp(120)

        actions.width = total_w
        card.add_widget(actions)
        return card

    def _badge_tag(self, text: str, bg_col, txt_col) -> BoxLayout:
        from kivy.graphics import Color, RoundedRectangle
        pill = BoxLayout(size_hint=(None, None), height=dp(22), padding=(dp(8), dp(2)))
        with pill.canvas.before:
            Color(*bg_col)
            bg = RoundedRectangle(pos=pill.pos, size=pill.size, radius=[dp(11)])
        pill.bind(pos=lambda item, value, s=bg: setattr(s, "pos", value),
                  size=lambda item, value, s=bg: setattr(s, "size", value))
        lbl = Label(text=text, font_size="10sp", bold=True, color=txt_col, size_hint=(None, None), height=dp(18))
        lbl.bind(texture_size=lambda item, sz: (setattr(item, "width", sz[0]), setattr(pill, "width", sz[0] + dp(16))))
        pill.add_widget(lbl)
        return pill

    def _card_vazio(self, titulo: str, subtitulo: str, icone: str) -> BoxLayout:
        from kivy.graphics import Color, RoundedRectangle, Line
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(110), padding=dp(16), spacing=dp(6))
        with box.canvas.before:
            Color(0.06, 0.10, 0.18, 0.7)
            bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(12)])
            Color(0.18, 0.32, 0.52, 0.3)
            b = Line(rounded_rectangle=(box.x, box.y, box.width, box.height, dp(12)), width=dp(1))
        box.bind(pos=lambda item, val, s=bg, ln=b: (setattr(s, "pos", val), setattr(ln, "rounded_rectangle", (val[0], val[1], item.width, item.height, dp(12)))),
                 size=lambda item, val, s=bg, ln=b: (setattr(s, "size", val), setattr(ln, "rounded_rectangle", (item.x, item.y, val[0], val[1], dp(12)))))
        topo = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28), spacing=dp(8))
        topo.add_widget(IconeUI(nome=icone, size_hint=(None, None), size=(dp(24), dp(24)), font_size="20sp", color=(0.4, 0.7, 1, 0.9)))
        topo.add_widget(Label(text=titulo, bold=True, font_size="14sp", color=(0.88, 0.93, 1, 1), halign="left", valign="middle", size_hint_x=1))
        box.add_widget(topo)
        lbl_sub = Label(text=subtitulo, font_size="11sp", color=(0.6, 0.7, 0.85, 0.8), halign="left", valign="middle", size_hint_y=None, height=dp(24))
        lbl_sub.bind(size=lambda item, val: setattr(item, "text_size", val))
        box.add_widget(lbl_sub)
        return box

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

    def _button(self, title: str, action, variant="primary", width=dp(130)) -> BotaoAcao:
        button = BotaoAcao(
            text=title, variant=variant, size_hint=(None, None), size=(width, dp(36)),
            color=(1, 1, 1, 1), font_size="11sp"
        )
        button.bind(on_release=lambda _button: action())
        return button

    def _mensagem(self, title: str, text: str):
        Popup(
            title=title,
            content=Label(text=text, color=(.08, .12, .20, 1), halign="left", valign="middle"),
            size_hint=(.62, .36),
        ).open()
