import threading
import traceback
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import BooleanProperty, DictProperty, ListProperty, StringProperty
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.graphics.texture import Texture
from kivy.metrics import dp

import model.componentes as componentes
from service.login.authentication import AuthenticationService as auth

from pathlib import Path
import tempfile
import requests


class TelaLogin(componentes.LayoutFundo):
    """Tela Kivy responsável apenas pela interação visual do login."""

    login_em_andamento = BooleanProperty(False)
    status_texto = StringProperty("")
    status_cor = ListProperty([0.45, 0.45, 0.45, 1])
    perfil_usuario = DictProperty({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def criar_gradiente_fundo(self, theme="Claro"):
        """Mantém o fundo azul original na tela de login."""
        texture = Texture.create(size=(1, 2), colorfmt="rgba")
        if str(theme).casefold() in {"escuro", "dark"}:
            pixels = bytes([7, 20, 43, 255, 28, 57, 96, 255])
        else:
            pixels = bytes([13, 74, 161, 255, 100, 180, 240, 255])
        texture.blit_buffer(pixels, colorfmt="rgba", bufferfmt="ubyte")
        return texture

    def login_google(self):
        """Inicia o fluxo OAuth em segundo plano sem bloquear a interface."""
        if self.login_em_andamento:
            return
        if App.get_running_app().settings.offline_mode:
            self._exibir_erro("Desative o modo offline para entrar com o Google.")
            return

        self.login_em_andamento = True
        self.status_texto = "Abrindo o navegador para login..."
        self.status_cor = [0.25, 0.45, 0.75, 1]
        threading.Thread(target=self._autenticar_google, daemon=True).start()

    def login_com_senha(self):
        """Autentica uma conta local cadastrada anteriormente."""
        email = self.ids.email_input.text.strip()
        password = self.ids.password_input.text
        app = App.get_running_app()
        try:
            profile = app.authentication_service.login_with_password(
                email, password, offline_mode=app.settings.offline_mode
            )
        except (ConnectionError, ValueError, OSError) as error:
            self._exibir_erro(str(error))
            return
        self._concluir_login(profile)

    def abrir_cadastro(self):
        """Abre o cadastro livre de aluno, sem oferecer seleção de perfil privilegiado."""
        fields = [
            componentes.CampoTextoClassico(appearance="dark", hint_text="Nome", multiline=False, size_hint_y=None, height=dp(48)),
            componentes.CampoTextoClassico(appearance="dark", hint_text="E-mail", multiline=False, size_hint_y=None, height=dp(48)),
            componentes.CampoTextoClassico(appearance="dark", hint_text="Senha (mínimo de 8 caracteres)", password=True, multiline=False, size_hint_y=None, height=dp(48)),
            componentes.CampoTextoClassico(appearance="dark", hint_text="Confirmar senha", password=True, multiline=False, size_hint_y=None, height=dp(48)),
        ]
        box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        for field in fields:
            box.add_widget(field)
        popup = Popup(
            title="Criar conta de aluno",
            content=box,
            size_hint=(.72, .52),
            title_color=(.90, .95, 1, 1),
            separator_color=(.11, .42, .82, 1),
        )

        def save(_instance):
            try:
                app = App.get_running_app()
                profile = app.authentication_service.register_student(
                    fields[0].text, fields[1].text, fields[2].text, fields[3].text,
                    offline_mode=app.settings.offline_mode,
                )
            except (ConnectionError, ValueError, OSError) as error:
                self._exibir_erro(str(error))
                return
            popup.dismiss()
            self._concluir_login(profile)

        button = componentes.BotaoAcao(
            text="Criar conta",
            variant="primary",
            icone="",
            size_hint_y=None,
            height=dp(48),
            color=(1, 1, 1, 1),
        )
        button.bind(on_release=save)
        box.add_widget(button)
        popup.open()

    def _autenticar_google(self):
        """Orquestra o login usando os serviços de autenticação em memória."""
        app = App.get_running_app()
        perfil = None
        try:
            perfil = app.authentication_service.login_with_google()
            print(f"[LOGIN] login_with_google retornou: {type(perfil)}")
            if isinstance(perfil, dict):
                print(f"[LOGIN] perfil email={perfil.get('email')}, picture={perfil.get('picture')}")
        except Exception as error:
            print(f"[LOGIN] Falha na autenticação Google: {error}")
            traceback.print_exc()
            Clock.schedule_once(
                lambda _dt: self._exibir_erro(
                    "Não foi possível concluir o login. Tente novamente."
                )
            )
            return

        Clock.schedule_once(lambda _dt: self._concluir_login(perfil))

    def _exibir_erro(self, mensagem):
        self.login_em_andamento = False
        self.status_texto = mensagem
        self.status_cor = [0.82, 0.20, 0.20, 1]

    def _concluir_login(self, perfil):
        """Atualiza a interface e navega apenas após um login válido."""
        self.login_em_andamento = False
        self.perfil_usuario = perfil
        print(f"[LOGIN] _concluir_login recebido perfil: {type(perfil)}")
        if isinstance(perfil, dict):
            print(f"[LOGIN] perfil keys: {list(perfil.keys())}")
        self.status_texto = f"Login concluído: {perfil.get('email', '')}"
        self.status_cor = [0.20, 0.62, 0.32, 1]
        if "password_input" in self.ids:
            self.ids.password_input.text = ""
        
        foto_url = perfil.get("picture")

        app = App.get_running_app()
        sm = app.root
        app.refresh_user_role()
        app.iniciar_limite_sessao()
        sm.perfil_usuario = perfil
        try:
            sm.get_screen("principal").children[0].refresh_access()
        except Exception:
            pass
        # Troca de tela (UI)
        sm.transition = SlideTransition(direction="left", duration=0.35)
        sm.current = "principal"

        # Baixa a imagem em background e aplica no cabeçalho da tela principal
        def _baixar_e_aplicar():
            if not foto_url:
                caminho = 'assets/icon/user_icon.png'
            else:
                pasta = Path(tempfile.gettempdir()) / "pm_painel"
                pasta.mkdir(exist_ok=True)
                arquivo = pasta / "perfil_google.jpg"
                try:
                    resposta = requests.get(foto_url, timeout=20)
                    resposta.raise_for_status()
                    arquivo.write_bytes(resposta.content)
                    app.google_auth.remember_profile_photo(arquivo)
                    caminho = str(arquivo)
                except Exception:
                    caminho = 'assets/icon/user_icon.png'

            # Atualiza o cabeçalho da tela principal na thread principal
            def _aplicar(dt):
                try:
                    tela_principal = sm.get_screen("principal").children[0]
                    tela_principal.atualizar_foto_perfil(caminho)
                except Exception:
                    pass

            Clock.schedule_once(_aplicar, 0)

        threading.Thread(target=_baixar_e_aplicar, daemon=True).start()
    
    def _logout(self):
        app = App.get_running_app()
        if app is not None:
            app.authentication_service.logout()
            app.refresh_user_role()
    
