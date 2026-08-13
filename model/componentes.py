# view/componentes.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty
from kivy.factory import Factory
from kivy.properties import BooleanProperty
from kivy.properties import NumericProperty
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.dropdown import DropDown
from kivy.core.image import Image as CoreImage
from kivy.animation import Animation
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.app import App

from service.login.authentication import AuthenticationService as auth




import socket
import threading
from kivy.clock import Clock


class LayoutFundo(BoxLayout):
    """Layout base reutilizável que já vem com o fundo gradiente e grafismos."""
    fundo_textura = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fundo_textura = self.criar_gradiente_fundo()

    def criar_gradiente_fundo(self):
        texture = Texture.create(size=(1, 2), colorfmt='rgba')
        
        # Seus pixels personalizados
        pixels = bytes([
            13,  74,  161, 255,
            100, 180, 240, 255
        ])
        
        texture.blit_buffer(pixels, colorfmt='rgba', bufferfmt='ubyte')
        return texture
    


class MenuPerfil(DropDown):
    pass



class FotoPerfil(Button):
    # Só precisamos declarar a variável, o Kivy cuida do resto!
    source = StringProperty('')

class Cabecalho(BoxLayout):
    """Cabeçalho moderno estilizado totalmente via código Kivy."""
    titulo = StringProperty("PM - Painel")
    gradiente_textura = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gradiente_textura = self._criar_gradiente_azul()
        
        # Instancia o menu suspenso
        self.menu_perfil = MenuPerfil()
        
        # Vincula o evento de seleção do menu a uma função
        self.menu_perfil.bind(on_select=self.tratar_selecao_menu)
        
    def abrir_menu(self, widget):
        """Abre o menu suspenso ancorado ao botão de perfil."""
        self.menu_perfil.open(widget)
    
    def atualizar_foto_perfil(self, novo_caminho_da_imagem = "assets/icon/user_icon.png"):
        # Acessamos o botão através do ID definido no .kv e mudamos o source
        self.ids.btn_perfil.source = novo_caminho_da_imagem

    # Exemplo: simulando quando o usuário faz login
    def on_kv_post(self, base_widget):
        # on_kv_post roda logo após o arquivo .kv ser carregado
        # Você pode chamar a função para definir a foto inicial aqui
        self.atualizar_foto_perfil()  # Caminho da imagem do usuário
        
    def tratar_selecao_menu(self, instance, selection):
        """Trata a seleção do menu suspenso."""
        print(f"Opção selecionada: {selection}")

        app = App.get_running_app()

        if selection == "Perfil":
            print("Abrindo perfil...")
            self.menu_perfil.dismiss()
        elif selection == "logout":
            if app is not None:
                app.authentication_service.logout()
                self.atualizar_foto_perfil()

                manager = app.root
                manager.transition = SlideTransition(direction="down", duration=0.35)
                manager.current = "login"

                login_screen = manager.get_screen("login").children[0]
                login_screen.login_em_andamento = False
                login_screen.status_texto = "Faça login com sua conta Google."
                login_screen.status_cor = [0.45, 0.45, 0.45, 1]

            self.menu_perfil.dismiss()
        elif selection == "Sair":
            if app is not None:
                app.stop()
            self.menu_perfil.dismiss()

    def _criar_gradiente_azul(self):
        # Textura vertical de 1x2 pixels
        texture = Texture.create(size=(1, 2), colorfmt='rgba')
        
        # Pixels [R, G, B, A] de 0 a 255:
        # Pixel 0 (Baixo) -> Azul Claro Transicional (RGB: 100, 180, 240)
        # Pixel 1 (Cima)  -> Azul Escuro PM (RGB: 13, 74, 161)
        pixels = bytes([
            100, 180, 240, 255,  # Baixo
            13,  74,  161, 255   # Cima
        ])
        
        texture.blit_buffer(pixels, colorfmt='rgba', bufferfmt='ubyte')
        return texture


class Rodape(BoxLayout):
    """Rodapé reutilizável com indicador de status de conexão em tempo real."""
    
    # Texto dinâmico do status
    status_texto = StringProperty("v0.0.0 | Verificando...")
    
    version = StringProperty("v0.0.1")  # Versão do aplicativo
    
    # Cor dinâmica do texto [R, G, B, A]
    # Padrão inicial: Amarelo/Laranja (Verificando)
    status_cor = ListProperty([0.9, 0.7, 0.2, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Executa a primeira checagem após 1 segundo da inicialização
        Clock.schedule_once(lambda dt: self.atualizar_conexao(), 1)
        # Repete a verificação automaticamente a cada 10 segundos
        Clock.schedule_interval(lambda dt: self.atualizar_conexao(), 1)

    def atualizar_conexao(self):
        """Inicia a verificação de conexão em uma thread separada (para não travar a UI)."""
        threading.Thread(target=self._testar_servidor, daemon=True).start()

    def _testar_servidor(self):
        """Testa a conexão com o servidor (temporariamente testando socket no IP 8.8.8.8 porta 53)."""
        # Servidor de Teste Temporário
        HOST_SERVIDOR = "8.8.8.8"  
        PORTA_SERVIDOR = 53

        conectado = False
        try:
            # Tenta conectar com timeout rápido de 2.5 segundos
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.5)
                s.connect((HOST_SERVIDOR, PORTA_SERVIDOR))
                conectado = True
        except Exception:
            conectado = False

        # Atualiza a interface gráfica na Thread Principal do Kivy
        Clock.schedule_once(lambda dt: self._aplicar_status(conectado))

    def _aplicar_status(self, conectado):
        """Atualiza o texto e a cor no rodapé com base no resultado."""
        if conectado:
            self.status_texto = f"{self.version} | Conectado"
            self.status_cor = [0.3, 0.85, 0.3, 1]  # Verde Vibrante
        else:
            self.status_texto = f"{self.version} | Desconectado"
            self.status_cor = [0.95, 0.3, 0.3, 1]  # Vermelho Alerta



class CardMenu(ButtonBehavior, BoxLayout):
    """Cartão de menu com aparência e animação de hover reutilizáveis."""

    titulo = StringProperty("Título do Card")
    descricao = StringProperty("Descrição do card, explicando sua função.")
    imagem_source = StringProperty("assets/img/config.jpg")
    hovering = BooleanProperty(False)

    # Estas propriedades são consumidas pela regra <CardMenu> em componentes.kv.
    # Manter a aparência no KV deixa este widget responsável apenas pelo comportamento.
    cor_fundo = ListProperty([0.06, 0.21, 0.48, 0.98])
    cor_fundo_normal = ListProperty([0.06, 0.21, 0.48, 0.98])
    cor_fundo_hover = ListProperty([0.08, 0.28, 0.60, 1])
    deslocamento_sombra = ListProperty([6, -6])
    deslocamento_sombra_normal = ListProperty([6, -6])
    deslocamento_sombra_hover = ListProperty([14, -16])
    opacidade_sombra = NumericProperty(0.22)
    opacidade_sombra_normal = NumericProperty(0.22)
    opacidade_sombra_hover = NumericProperty(0.38)
    elevacao = NumericProperty(0)
    elevacao_hover = NumericProperty(10)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._animacao = None
        self._monitorando_mouse = False
        self.bind(hovering=self._on_hovering)

    def on_parent(self, _widget, parent):
        """Monitora o mouse apenas enquanto o cartão estiver na interface."""
        if parent is not None and not self._monitorando_mouse:
            Window.bind(mouse_pos=self._on_mouse_pos)
            self._monitorando_mouse = True
        elif parent is None and self._monitorando_mouse:
            Window.unbind(mouse_pos=self._on_mouse_pos)
            self._monitorando_mouse = False
            self.hovering = False

    def _on_hovering(self, *args):
        if self._animacao:
            self._animacao.cancel(self)

        cor_alvo = self.cor_fundo_hover if self.hovering else self.cor_fundo_normal
        sombra_alvo = (
            self.deslocamento_sombra_hover
            if self.hovering
            else self.deslocamento_sombra_normal
        )
        opacidade_alvo = (
            self.opacidade_sombra_hover
            if self.hovering
            else self.opacidade_sombra_normal
        )
        self._animacao = Animation(
            cor_fundo=cor_alvo,
            deslocamento_sombra=sombra_alvo,
            opacidade_sombra=opacidade_alvo,
            elevacao=self.elevacao_hover if self.hovering else 0,
            d=0.14,
            t='out_quad',
        )
        self._animacao.start(self)

    def _on_mouse_pos(self, _window, pos):
        if not self.get_root_window():
            return

        local_pos = self.to_widget(*pos)
        inside = self.collide_point(*local_pos)

        if self.hovering != inside:
            self.hovering = inside



class BotaoHover(Button):
    hovering = BooleanProperty(False)
    
    # 1. Variável compartilhada por todos os botões para rastrear o hover
    _botoes_focados = [] 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, window, pos):
        if not self.get_root_window():
            return
            
        local_pos = self.to_widget(*pos)
        inside = self.collide_point(*local_pos)

        if self.hovering != inside:
            self.hovering = inside
            
            if inside:
                # 2. Adiciona este botão à lista de focados
                if self not in BotaoHover._botoes_focados:
                    BotaoHover._botoes_focados.append(self)
                Window.set_system_cursor('hand')
            else:
                # 3. Remove este botão da lista de focados
                if self in BotaoHover._botoes_focados:
                    BotaoHover._botoes_focados.remove(self)
                
                # 4. A MÁGICA: Só volta pra 'arrow' se NENHUM outro botão estiver na lista
                if len(BotaoHover._botoes_focados) == 0:
                    Window.set_system_cursor('arrow')

Factory.register('BotaoHover', cls=BotaoHover)
