import threading
import traceback
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import BooleanProperty, DictProperty, ListProperty, StringProperty
from kivy.uix.screenmanager import SlideTransition

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

    def login_google(self):
        """Inicia o fluxo OAuth em segundo plano sem bloquear a interface."""
        if self.login_em_andamento:
            return

        self.login_em_andamento = True
        self.status_texto = "Abrindo o navegador para login..."
        self.status_cor = [0.25, 0.45, 0.75, 1]
        threading.Thread(target=self._autenticar_google, daemon=True).start()

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
        
        foto_url = perfil.get("picture")

        app = App.get_running_app()
        sm = app.root
        sm.perfil_usuario = perfil
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
    
