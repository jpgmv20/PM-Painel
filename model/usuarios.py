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

from model.componentes import BotaoAcao, CampoTexto, LayoutFundo


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
            area.add_widget(self._label("Seu perfil não tem permissão para gerenciar usuários."))
            return

        users = self._app.authentication_service.list_users()
        self.ids.user_status.text = (
            f"{len(users)} conta(s) neste computador • "
            + ("internet disponível" if self._online() else "sem conexão: gestão bloqueada")
        )
        if not users:
            area.add_widget(self._label("Nenhuma conta local foi cadastrada ainda."))
            return
        subject_names = {item.id: item.nome for item in self._app.materias_service.listar()}
        for user in users:
            card = BoxLayout(
                orientation="vertical", size_hint_y=None, height=dp(130),
                padding=dp(12), spacing=dp(5),
            )
            with card.canvas.before:
                from kivy.graphics import Color, RoundedRectangle
                Color(.055, .09, .15, 1)
                background = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
            card.bind(
                pos=lambda item, value, shape=background: setattr(shape, "pos", value),
                size=lambda item, value, shape=background: setattr(shape, "size", value),
            )
            role = str(user.get("role", "aluno")).capitalize()
            status = "Ativa" if user.get("active", True) else "Suspensa"
            card.add_widget(self._label(f"{user.get('name', 'Usuário')}  •  {role}  •  {status}", bold=True))
            card.add_widget(self._label(user.get("email", "")))
            assigned = user.get("materias_responsaveis", [])
            names = [subject_names[item] for item in assigned if item in subject_names]
            if role.casefold() == "professor":
                card.add_widget(self._label("Matérias: " + (", ".join(names) if names else "nenhuma atribuída")))
            actions = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
            if user.get("role") == "professor":
                actions.add_widget(self._button("Atribuir matérias", lambda item=user: self._abrir_formulario(item)))
            if user.get("id") != self._app.session_manager.user.get("id"):
                active = user.get("active", True)
                actions.add_widget(self._button(
                    "Suspender conta" if active else "Reativar conta",
                    lambda ident=user["id"], value=not active: self._alterar_ativacao(ident, value),
                ))
            card.add_widget(actions)
            area.add_widget(card)

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
            size_hint=(.6, .35),
        ).open()
