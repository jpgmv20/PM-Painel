"""Tela de tratamento de exceção quando o Docker não está ativo ao iniciar o programa."""
from __future__ import annotations

import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import SlideTransition

import model.componentes as componentes
from service.docker_service import DockerService
from service.translations import translate


class TelaDockerErro(componentes.LayoutFundo):
    """Apresenta diagnóstico amigável e ação para ativar o Docker quando fechado."""

    titulo_erro = StringProperty("Docker não está em execução")
    descricao_erro = StringProperty(
        "O PM-Painel requer o Docker Desktop ativo para seus laboratórios e serviços integrados. "
        "O serviço do Docker não foi detectado no momento."
    )
    detalhe_tecnico = StringProperty("")
    status_texto = StringProperty("Docker Desktop / Serviço offline")
    status_cor = ListProperty([0.95, 0.45, 0.20, 1])  # Âmbar / Laranja
    iniciando_docker = BooleanProperty(False)
    progresso_texto = StringProperty("")
    docker_pronto = BooleanProperty(False)
    destino_pos_sucesso = StringProperty("home")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._thread_ativacao: threading.Thread | None = None
        self._cancelado = False

    @property
    def docker_service(self) -> DockerService:
        """Utiliza a instância compartilhada do aplicativo quando disponível."""
        app = App.get_running_app()
        if app is not None and hasattr(app, "docker_service"):
            return app.docker_service
        if not hasattr(self, "_local_docker_service"):
            self._local_docker_service = DockerService()
        return self._local_docker_service

    def configurar(self, destino_pos_sucesso: str = "home", detalhe: str = "") -> None:
        """Configura a tela com a rota de destino e o detalhe técnico do diagnóstico."""
        self.destino_pos_sucesso = destino_pos_sucesso
        self.detalhe_tecnico = detalhe or ""
        self.iniciando_docker = False
        self.docker_pronto = False
        self.status_cor = [0.95, 0.45, 0.20, 1]
        if not self.docker_service.is_installed():
            self.titulo_erro = "Docker não encontrado no sistema"
            self.status_texto = "Docker Desktop não instalado"
            self.progresso_texto = "Instale o Docker Desktop para habilitar os laboratórios do painel."
        else:
            self.titulo_erro = "Docker não está em execução"
            self.status_texto = "Docker Desktop / Serviço offline"
            self.progresso_texto = detalhe or "O Docker Desktop precisa ser iniciado."

    def iniciar_servico_docker(self) -> None:
        """Dispara a ativação do Docker em background e monitora o resultado."""
        if self.iniciando_docker:
            return

        self.iniciando_docker = True
        self.docker_pronto = False
        self._cancelado = False
        self.status_texto = "Iniciando Docker..."
        self.status_cor = [0.20, 0.55, 0.90, 1]  # Azul em andamento
        self.progresso_texto = "Abrindo o Docker Desktop e aguardando o serviço responder..."

        def callback_progresso(segundos: int, mensagem: str) -> None:
            def atualizar(_dt):
                if not self._cancelado and self.iniciando_docker:
                    self.progresso_texto = mensagem
            Clock.schedule_once(atualizar, 0)

        def worker() -> None:
            ok, mensagem = self.docker_service.start_docker_service(
                progress_callback=callback_progresso,
                timeout=60,
            )

            def finalizar(_dt):
                if self._cancelado:
                    return
                self.iniciando_docker = False
                if ok:
                    self.docker_pronto = True
                    self.status_texto = "Docker iniciado com sucesso!"
                    self.status_cor = [0.20, 0.82, 0.35, 1]  # Verde vibrante
                    self.progresso_texto = "O serviço Docker está pronto! Iniciando o programa..."
                    # Aguarda 1.2s para o usuário visualizar o sucesso e inicia o programa automaticamente
                    Clock.schedule_once(lambda _dt: self.iniciar_programa(), 1.2)
                else:
                    self.docker_pronto = False
                    self.status_texto = "Não foi possível conectar ao Docker"
                    self.status_cor = [0.92, 0.26, 0.26, 1]  # Vermelho
                    self.progresso_texto = mensagem
                    self._mostrar_aviso_falha(mensagem)

            Clock.schedule_once(finalizar, 0)

        self._thread_ativacao = threading.Thread(
            target=worker,
            name="PM-Painel-DockerStartup",
            daemon=True,
        )
        self._thread_ativacao.start()

    def verificar_novamente(self) -> None:
        """Checa manualmente se o usuário abriu o Docker externamente."""
        self.progresso_texto = "Verificando se o Docker está ativo..."
        running, msg = self.docker_service.is_running(timeout=2.0)
        if running:
            self.docker_pronto = True
            self.status_texto = "Docker detectado!"
            self.status_cor = [0.20, 0.82, 0.35, 1]
            self.progresso_texto = "Serviço Docker em execução. Abrindo o painel..."
            Clock.schedule_once(lambda _dt: self.iniciar_programa(), 0.8)
        else:
            self.status_texto = "Docker ainda não está respondendo"
            self.status_cor = [0.95, 0.45, 0.20, 1]
            self.progresso_texto = msg

    def _obter_manager(self):
        """Recupera a instância do ScreenManager associada."""
        if hasattr(self, "parent") and hasattr(self.parent, "manager") and self.parent.manager is not None:
            return self.parent.manager
        app = App.get_running_app()
        if app is not None and getattr(app, "root", None) is not None:
            return app.root
        return None

    def iniciar_programa(self) -> None:
        """Prossegue com a inicialização normal do aplicativo para a tela de destino."""
        manager = self._obter_manager()
        if manager is None:
            return

        app = App.get_running_app()
        destino = self.destino_pos_sucesso or "home"
        if destino not in manager.screen_names:
            destino = "home"

        manager.transition = SlideTransition(direction="left", duration=0.35)
        manager.current = destino
        if destino == "principal" and app is not None:
            Clock.schedule_once(lambda _dt: app.iniciar_limite_sessao(), 0)

    def continuar_sem_docker(self) -> None:
        """Permite que o usuário use o PM-Painel em modo limitado sem o Docker."""
        self._cancelado = True
        self.iniciar_programa()

    def _mostrar_aviso_falha(self, mensagem: str) -> None:
        """Apresenta diálogo modal detalhando o ocorrido e orientando o usuário."""
        app = App.get_running_app()
        lang = app.settings.language if app and hasattr(app, "settings") else "Português (Brasil)"
        theme_text = tuple(app.theme_text) if app and hasattr(app, "theme_text") else (1, 1, 1, 1)
        theme_surface = tuple(app.theme_surface) if app and hasattr(app, "theme_surface") else (0.1, 0.14, 0.21, 1)

        content = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(14))
        content.add_widget(Label(
            text=translate(
                "Não foi possível iniciar o Docker automaticamente.\n\n"
                "Recomendação:\n"
                "• Abra o aplicativo Docker Desktop pelo Menu Iniciar do Windows.\n"
                "• Aguarde até que o ícone na barra de tarefas indique que a engine está pronta.\n"
                "• Em seguida, clique em 'Verificar novamente' ou 'Continuar sem Docker'.",
                lang,
            ),
            color=theme_text,
            halign="center",
            valign="middle",
        ))
        botoes = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        btn_ok = componentes.BotaoAcao(
            text=translate("Entendi", lang),
            variant="primary",
            size_hint_y=None,
            height=dp(42),
        )
        popup = Popup(
            title=translate("Aviso do Docker", lang),
            content=content,
            size_hint=(0.60, 0.42),
            title_color=theme_text,
            background_color=theme_surface,
        )
        btn_ok.bind(on_release=popup.dismiss)
        botoes.add_widget(btn_ok)
        content.add_widget(botoes)
        popup.open()
