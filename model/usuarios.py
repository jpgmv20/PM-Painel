"""Painel de contas e atribuição de matérias para moderadores."""

from __future__ import annotations

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import SlideTransition

from kivy.uix.widget import Widget
from model.componentes import BotaoAcao, CampoTexto, LayoutFundo, IconeUI


class TelaUsuarios(LayoutFundo):
    """Lista contas locais; somente moderadores podem criar ou administrar perfis."""

    def on_kv_post(self, _base_widget):
        self.atualizar()

    @property
    def _app(self):
        return App.get_running_app()

    def voltar(self):
        self._app.root.transition = SlideTransition(direction="right", duration=.25)
        self._app.root.current = "principal"

    def _moderador(self) -> bool:
        return self._app.permission_service.perfil_pode_gerenciar_usuarios(
            self._app.session_manager.user
        )

    def atualizar(self):
        area = self.ids.user_list
        area.clear_widgets()
        if not self._moderador():
            self.ids.user_status.text = "Apenas moderadores podem abrir este painel."
            area.add_widget(self._card_vazio("Permissão restrita", "Seu perfil atual não tem permissão de moderador para gerenciar contas.", "shield-alert-outline"))
            return

        users = self._app.authentication_service.list_users()
        self.ids.user_status.text = (
            f"{len(users)} conta(s) neste computador • "
            + ("internet disponível" if self._online() else "sem conexão: gestão bloqueada")
        )
        if not users:
            area.add_widget(self._card_vazio("Nenhuma conta cadastrada", "Nenhuma conta local foi cadastrada ainda neste computador.", "account-question-outline"))
            return
        subject_names = {item.id: item.nome for item in self._app.materias_service.listar()}
        for user in users:
            area.add_widget(self._criar_cartao_usuario(user, subject_names))

    def _badge_tag(self, text: str, role: str) -> BoxLayout:
        from kivy.graphics import Color, RoundedRectangle
        if role == "moderador":
            bg_col = (0.75, 0.50, 0.10, 0.28)
            txt_col = (1, 0.85, 0.45, 1)
        elif role == "professor":
            bg_col = (0.45, 0.22, 0.75, 0.28)
            txt_col = (0.85, 0.65, 1, 1)
        else:
            bg_col = (0.15, 0.35, 0.70, 0.28)
            txt_col = (0.55, 0.82, 1, 1)

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

    def _badge_status(self, text: str, active: bool) -> BoxLayout:
        from kivy.graphics import Color, RoundedRectangle
        bg_col = (0.12, 0.65, 0.35, 0.28) if active else (0.65, 0.18, 0.18, 0.28)
        txt_col = (0.45, 0.95, 0.65, 1) if active else (1, 0.45, 0.45, 1)

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

    def _criar_cartao_usuario(self, user: dict, subject_names: dict) -> BoxLayout:
        from kivy.graphics import Color, RoundedRectangle, Line
        role_raw = str(user.get("role", "aluno")).lower()
        role_display = role_raw.capitalize()
        active = user.get("active", True)
        status_display = "Ativa" if active else "Suspensa"
        current_user = self._app.session_manager.user or {}
        is_self = str(user.get("id")) == str(current_user.get("id"))
        assigned = user.get("materias_responsaveis", [])
        names = [subject_names[item] for item in assigned if item in subject_names]
        is_prof = role_raw == "professor"
        has_mat = is_prof and bool(names)

        card_h = dp(96) if has_mat else dp(82)
        card = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=card_h,
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

        # Avatar com ícone
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
        icone_nome = "shield-crown" if role_raw == "moderador" else ("school" if role_raw == "professor" else "account")
        icone_cor = (1, 0.82, 0.35, 1) if role_raw == "moderador" else ((0.5, 0.85, 1, 1) if role_raw == "professor" else (0.75, 0.85, 1, 1))
        avatar.add_widget(IconeUI(nome=icone_nome, size_hint=(1, 1), font_size="22sp", color=icone_cor, halign="center", valign="middle"))
        card.add_widget(avatar)

        # Coluna Central: Nome, Badges, Email, Matérias
        info_col = BoxLayout(orientation="vertical", spacing=dp(3), size_hint_x=1)
        top_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(26))
        lbl_nome = Label(
            text=user.get("name", "Usuário"),
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
        top_row.add_widget(self._badge_tag(role_display, role_raw))
        top_row.add_widget(self._badge_status(status_display, active))
        top_row.add_widget(Widget())
        info_col.add_widget(top_row)

        lbl_email = Label(
            text=user.get("email", ""),
            font_size="12sp",
            color=(0.60, 0.70, 0.85, 1),
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle"
        )
        lbl_email.bind(size=lambda item, val: setattr(item, "text_size", val))
        info_col.add_widget(lbl_email)

        if has_mat:
            lbl_mat = Label(
                text="Matérias: " + ", ".join(names),
                font_size="11sp",
                color=(0.42, 0.78, 0.95, 0.9),
                size_hint_y=None,
                height=dp(18),
                halign="left",
                valign="middle"
            )
            lbl_mat.bind(size=lambda item, val: setattr(item, "text_size", val))
            info_col.add_widget(lbl_mat)

        card.add_widget(info_col)

        # Ações à direita (compactas, nunca esticam!)
        actions = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            height=dp(38),
            spacing=dp(8),
            pos_hint={"center_y": 0.5}
        )
        total_btn_w = dp(0)

        if is_prof:
            btn_mat = BotaoAcao(
                text="Atribuir matérias",
                icone="book-edit-outline",
                variant="secondary",
                size_hint=(None, None),
                size=(dp(160), dp(36)),
                font_size="11sp"
            )
            btn_mat.bind(on_release=lambda _b, item=user: self._abrir_formulario(item))
            actions.add_widget(btn_mat)
            total_btn_w += dp(168)

        if not is_self:
            btn_toggle = BotaoAcao(
                text="Suspender conta" if active else "Reativar conta",
                icone="account-cancel-outline" if active else "account-check-outline",
                variant="danger" if active else "primary",
                size_hint=(None, None),
                size=(dp(150), dp(36)),
                font_size="11sp"
            )
            btn_toggle.bind(on_release=lambda _b, ident=user["id"], val=not active: self._alterar_ativacao(ident, val))
            actions.add_widget(btn_toggle)
            total_btn_w += dp(150)
        else:
            lbl_self = Label(
                text="Você (Sessão atual)",
                color=(0.45, 0.75, 1, 0.8),
                font_size="11sp",
                bold=True,
                size_hint=(None, None),
                size=(dp(140), dp(36)),
                halign="center",
                valign="middle"
            )
            actions.add_widget(lbl_self)
            total_btn_w += dp(140)

        actions.width = total_btn_w
        card.add_widget(actions)
        return card

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

    def novo_usuario(self):
        if not self._validar_moderador():
            return
        if not self._validar_rede():
            return
        self._abrir_formulario(None)

    def _abrir_formulario(self, user: dict | None):
        edit = user is not None
        form = GridLayout(cols=1, spacing=dp(8), padding=dp(8), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        name = CampoTexto(
            appearance="dark",
            text=user.get("name", "") if user else "", hint_text="Nome completo",
            multiline=False, size_hint_y=None, height=dp(42), disabled=edit,
        )
        email = CampoTexto(
            appearance="dark",
            text=user.get("email", "") if user else "", hint_text="E-mail",
            multiline=False, size_hint_y=None, height=dp(42), disabled=edit,
        )
        password = CampoTexto(
            appearance="dark",
            hint_text="Senha (mínimo de 8 caracteres)", password=True, multiline=False,
            size_hint_y=None, height=dp(42), disabled=edit,
        )
        confirm_password = CampoTexto(
            appearance="dark",
            hint_text="Confirmar senha", password=True, multiline=False,
            size_hint_y=None, height=dp(42), disabled=edit,
        )
        for field in (name, email, password, confirm_password):
            form.add_widget(field)
        role = Spinner(
            text=user.get("role", "professor") if user else "professor",
            values=("professor", "moderador"), size_hint_y=None, height=dp(42),
            disabled=edit,
        )
        form.add_widget(role)
        form.add_widget(Label(
            text="Matérias sob responsabilidade do professor", size_hint_y=None,
            height=dp(28), color=(.82, .88, .98, 1), halign="left",
        ))
        selected = set(user.get("materias_responsaveis", [])) if user else set()
        checks: dict[str, CheckBox] = {}
        subjects = self._app.materias_service.listar()
        if subjects:
            for subject in subjects:
                row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(8))
                check = CheckBox(size_hint_x=None, width=dp(36), active=subject.id in selected)
                checks[subject.id] = check
                row.add_widget(check)
                row.add_widget(Label(text=subject.nome, color=(.9, .93, .98, 1), halign="left"))
                form.add_widget(row)
        else:
            form.add_widget(Label(
                text="Crie matérias antes de atribuí-las ao professor.",
                size_hint_y=None, height=dp(36), color=(.67, .75, .89, 1),
            ))
        scroller = ScrollView(do_scroll_x=False, bar_width=dp(6))
        scroller.add_widget(form)
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(scroller)
        popup = Popup(
            title="Atribuir matérias" if edit else "Criar conta de equipe",
            content=root, size_hint=(.72, .82),
            title_color=(.90, .95, 1, 1), separator_color=(.11, .42, .82, 1),
        )

        def save():
            subject_ids = [ident for ident, checkbox in checks.items() if checkbox.active]
            if not edit and password.text != confirm_password.text:
                self._mensagem("Senhas diferentes", "Confirme a mesma senha nos dois campos.")
                return
            try:
                if edit:
                    self._app.authentication_service.set_user_subjects(
                        user["id"], subject_ids, self._app.session_manager.user,
                        offline_mode=self._app.settings.offline_mode,
                    )
                else:
                    self._app.authentication_service.create_staff_user(
                        name.text, email.text, password.text, role.text,
                        subject_ids if role.text == "professor" else [],
                        self._app.session_manager.user,
                        offline_mode=self._app.settings.offline_mode,
                    )
            except (ConnectionError, ValueError, KeyError, PermissionError, OSError) as error:
                self._mensagem("Não foi possível salvar", str(error))
                return
            popup.dismiss()
            self.atualizar()

        root.add_widget(self._button("Salvar", save))
        popup.open()

    def _alterar_ativacao(self, user_id: str, active: bool):
        try:
            self._app.authentication_service.set_user_active(
                user_id, active, self._app.session_manager.user,
                offline_mode=self._app.settings.offline_mode,
            )
        except (ConnectionError, PermissionError, KeyError, OSError) as error:
            self._mensagem("Não foi possível atualizar a conta", str(error))
        self.atualizar()

    def _validar_moderador(self) -> bool:
        if self._moderador():
            return True
        self._mensagem("Acesso restrito", "Somente moderadores podem gerenciar contas.")
        return False

    def _validar_rede(self) -> bool:
        try:
            self._app.internet_service.require_online(
                offline_mode=self._app.settings.offline_mode,
                action="O gerenciamento de usuários",
            )
            return True
        except ConnectionError as error:
            self._mensagem("Conexão necessária", str(error))
            return False

    def _online(self) -> bool:
        return not self._app.settings.offline_mode and self._app.internet_service.online()

    def _label(self, text: str, bold: bool = False) -> Label:
        label = Label(
            text=text, bold=bold, size_hint_y=None, height=dp(24),
            color=(.88, .93, 1, 1), halign="left", valign="middle",
        )
        label.bind(width=lambda item, width: setattr(item, "text_size", (width, None)))
        return label

    def _button(self, title: str, action, variant="primary", width=dp(150)) -> BotaoAcao:
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
            size_hint=(.6, .35),
        ).open()
