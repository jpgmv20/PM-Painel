# view/componentes.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty, ListProperty, OptionProperty
from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty
from kivy.factory import Factory
from kivy.properties import BooleanProperty
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.dropdown import DropDown
from kivy.core.image import Image as CoreImage
from kivy.animation import Animation
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.app import App
import os
from kivymd.icon_definitions import md_icons
from kivymd.uix.label import MDIcon
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField

from service.login.authentication import AuthenticationService as auth




import socket
import threading
from kivy.clock import Clock



class LayoutFundo(BoxLayout):
    """Layout base reutilizável que já vem com o fundo gradiente e grafismos."""
    fundo_textura = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        app = App.get_running_app()
        theme = app.settings.theme if app is not None and hasattr(app, "settings") else "Claro"
        self.fundo_textura = self.criar_gradiente_fundo(theme)
        if app is not None and hasattr(app, "settings"):
            app.settings.bind(theme=self._atualizar_tema)

    def criar_gradiente_fundo(self, theme="Claro"):
        texture = Texture.create(size=(1, 2), colorfmt='rgba')
        if str(theme).casefold() in {"escuro", "dark"}:
            pixels = bytes([12, 18, 29, 255, 22, 33, 49, 255])
        else:
            pixels = bytes([244, 247, 251, 255, 232, 238, 246, 255])
        texture.blit_buffer(pixels, colorfmt='rgba', bufferfmt='ubyte')
        return texture

    def _atualizar_tema(self, _settings, theme):
        self.fundo_textura = self.criar_gradiente_fundo(theme)
    


class MenuPerfil(DropDown):
    logout_bloqueado = BooleanProperty(False)

    def atualizar_estado_logout(self) -> None:
        app = App.get_running_app()
        if app is None or getattr(app, "root", None) is None:
            return

        tela_atual = app.root.current
        self.logout_bloqueado = tela_atual in {"home", "login"}



class FotoPerfil(Button):
    # Só precisamos declarar a variável, o Kivy cuida do resto!
    source = StringProperty('')

class Cabecalho(BoxLayout):
    """Cabeçalho moderno estilizado totalmente via código Kivy."""
    titulo = StringProperty("PM - Painel")
    gradiente_textura = ObjectProperty(None)
    gradiente_login = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gradiente_textura = self._criar_gradiente_azul()
        app = App.get_running_app()
        if app is not None and hasattr(app, "settings"):
            app.settings.bind(theme=self._atualizar_tema)
        self.bind(gradiente_login=self._atualizar_tema)
        
        # Instancia o menu suspenso
        self.menu_perfil = MenuPerfil()
        
        # Vincula o evento de seleção do menu a uma função
        self.menu_perfil.bind(on_select=self.tratar_selecao_menu)
        
    def abrir_menu(self, widget):
        """Abre o menu suspenso ancorado ao botão de perfil."""
        self.menu_perfil.atualizar_estado_logout()
        self.menu_perfil.open(widget)
    
    def atualizar_foto_perfil(self, novo_caminho_da_imagem = "assets/icon/user_icon.png"):
        app = App.get_running_app()
        if app is not None:
            app.set_profile_photo(novo_caminho_da_imagem)

    def _voltar_para_login(self, app):
        manager = getattr(app, "root", None)
        if manager is None:
            return

        try:
            login_screen = manager.get_screen("login")
        except Exception:
            return

        if login_screen.children:
            tela_login = login_screen.children[-1]
            tela_login.login_em_andamento = False
            tela_login.status_texto = "Entre com e-mail e senha ou use sua conta Google."
            tela_login.status_cor = [0.45, 0.45, 0.45, 1]

        manager.transition = SlideTransition(direction="down", duration=0.35)
        manager.current = "login"

    def tratar_selecao_menu(self, instance, selection):
        """Trata a seleção do menu suspenso."""
        print(f"Opção selecionada: {selection}")

        app = App.get_running_app()

        if selection in {"Perfil", "perfil"}:
            if app is not None and getattr(app, "root", None) is not None:
                try:
                    manager = app.root
                    manager.get_screen("perfil").children[0].atualizar()
                    manager.transition = SlideTransition(direction="left", duration=0.25)
                    manager.current = "perfil"
                except Exception:
                    pass
            self.menu_perfil.dismiss()
        elif selection == "logout":
            if app is not None:
                if getattr(app.root, "current", None) in {"home", "login"}:
                    self.menu_perfil.dismiss()
                    return
                app.authentication_service.logout()
                app.refresh_user_role()
                app.set_profile_photo()
                self._voltar_para_login(app)

            self.menu_perfil.dismiss()
        elif selection == "Sair":
            if app is not None:
                app.solicitar_saida()
            self.menu_perfil.dismiss()

    def _atualizar_tema(self, _settings, _theme):
        self.gradiente_textura = self._criar_gradiente_azul()

    def _criar_gradiente_azul(self):
        # Textura vertical de 1x2 pixels
        texture = Texture.create(size=(1, 2), colorfmt='rgba')
        app = App.get_running_app()
        theme = app.settings.theme if app is not None and hasattr(app, "settings") else "Claro"
        if self.gradiente_login and str(theme).casefold() in {"escuro", "dark"}:
            pixels = bytes([6, 16, 35, 255, 21, 45, 80, 255])
        elif self.gradiente_login:
            pixels = bytes([100, 180, 240, 255, 13, 74, 161, 255])
        elif str(theme).casefold() in {"escuro", "dark"}:
            pixels = bytes([0, 58, 121, 255, 0, 70, 150, 255])
        else:
            pixels = bytes([0, 58, 121, 255, 0, 70, 150, 255])
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
        app = App.get_running_app()
        if app is not None and app.settings.offline_mode:
            self._aplicar_status(False)
            return
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
        app = App.get_running_app()
        if app is not None and app.settings.offline_mode:
            self.status_texto = f"{self.version} | Modo offline"
            self.status_cor = [0.9, 0.7, 0.2, 1]
        elif conectado:
            self.status_texto = f"{self.version} | Conectado"
            self.status_cor = [0.3, 0.85, 0.3, 1]  # Verde Vibrante
        else:
            self.status_texto = f"{self.version} | Desconectado"
            self.status_cor = [0.95, 0.3, 0.3, 1]  # Vermelho Alerta



class CartaoMaterial(MDCard):
    """Cartão reutilizável com elevação e cantos consistentes do KivyMD."""


class CartaoInterativo(CartaoMaterial):
    """Cartão Material com clique, efeito ripple e elevação ao passar o mouse."""

    hovering = BooleanProperty(False)

    def __init__(self, **kwargs):
        kwargs.setdefault("ripple_behavior", True)
        kwargs.setdefault("focus_behavior", True)
        kwargs.setdefault("style", "elevated")
        kwargs.setdefault("elevation", 3)
        kwargs.setdefault("radius", [dp(22)] * 4)
        super().__init__(**kwargs)
        self._hover_animation = None
        self._monitorando_mouse = False
        self.bind(hovering=self._atualizar_elevacao)

    def on_parent(self, _widget, parent):
        if parent is not None and not self._monitorando_mouse:
            Window.bind(mouse_pos=self._on_mouse_pos)
            self._monitorando_mouse = True
        elif parent is None and self._monitorando_mouse:
            Window.unbind(mouse_pos=self._on_mouse_pos)
            self._monitorando_mouse = False
            self.hovering = False

    def _on_mouse_pos(self, _window, pos):
        if not self.get_root_window():
            return
        inside = self.collide_point(*self.to_widget(*pos))
        if self.hovering != inside:
            self.hovering = inside

    def _atualizar_elevacao(self, *_args):
        if self._hover_animation is not None:
            self._hover_animation.cancel(self)
        self._hover_animation = Animation(
            elevation=6 if self.hovering else 3,
            d=0.14,
            t="out_quad",
        )
        self._hover_animation.start(self)


class CardMenu(CartaoInterativo):
    """Cartão de menu com ícone Material, descrição e estados interativos."""

    titulo = StringProperty("Título do Card")
    descricao = StringProperty("Descrição do card, explicando sua função.")
    icone = StringProperty("view-dashboard-outline")



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

class BotaoAcao(BotaoHover):
    """Botão da interface com cápsula, contorno e estados de foco consistentes."""

    icone = StringProperty("")
    icon_position = OptionProperty("left", options=("left", "right"))
    variant = OptionProperty(
        "primary", options=("primary", "secondary", "light", "danger", "quiet")
    )

    def on_text(self, _instance, value):
        if not self.icone:
            self.icone = self._icone_para_acao(value)

    @staticmethod
    def _icone_para_acao(text):
        text = str(text).casefold()
        for terms, icon in (
            (("voltar",), "arrow-left"),
            (("painel", "início", "inicio", "home"), "home-outline"),
            (("criar", "novo", "adicionar"), "plus-circle-outline"),
            (("salvar", "guardar"), "content-save-outline"),
            (("enviar", "publicar", "upload"), "upload-outline"),
            (("instalar", "baixar", "download"), "download-outline"),
            (("atualiza", "verificar", "reiniciar"), "refresh"),
            (("editar",), "pencil-outline"),
            (("excluir", "remover", "apagar", "deletar"), "delete-outline"),
            (("buscar", "pesquisar", "filtrar"), "magnify"),
            (("entrar", "login"), "login"),
            (("sair", "logout", "fechar", "encerrar"), "exit-to-app"),
            (("executar", "simular", "iniciar"), "play-outline"),
            (("continuar", "abrir", "acessar"), "arrow-right"),
            (("confirmar", "aprovar"), "check-circle-outline"),
        ):
            if any(term in text for term in terms):
                return icon
        return ""


class IconeUI(MDIcon):
    """Ícone vetorial com nome validado e fallback visível, sem depender de emoji."""

    nome = StringProperty("help-circle-outline")

    def __init__(self, **kwargs):
        requested = kwargs.pop("nome", "help-circle-outline")
        kwargs["icon"] = "help-circle-outline"
        kwargs.setdefault("font_name", "Icons")
        kwargs.setdefault("theme_text_color", "Custom")
        super().__init__(**kwargs)
        self.bind(nome=self._atualizar_icone)
        self.nome = requested
        self._atualizar_icone(self, self.nome)

    def _atualizar_icone(self, _instance, nome):
        self.icon = nome if nome in md_icons else "help-circle-outline"


class CampoTextoClassico(TextInput):
    """Campo de texto original, mantido no login para preservar o visual conhecido."""

    appearance = OptionProperty("light", options=("light", "dark"))
    surface_color = ListProperty([.97, .98, 1, 1])
    disabled_surface_color = ListProperty([.88, .91, .95, 1])
    border_color = ListProperty([.78, .84, .92, 1])
    focus_color = ListProperty([.14, .49, .91, 1])
    text_color = ListProperty([.08, .14, .23, 1])
    hint_color = ListProperty([.43, .51, .62, 1])

    def __init__(self, **kwargs):
        palette = self._palette(kwargs.get("appearance", "light"))
        for prop, value in palette.items():
            kwargs.setdefault(prop, value)
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_active", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("foreground_color", palette["text_color"])
        kwargs.setdefault("hint_text_color", palette["hint_color"])
        kwargs.setdefault("cursor_color", palette["focus_color"])
        kwargs.setdefault("padding", (dp(14), dp(12)))
        kwargs.setdefault("write_tab", False)
        super().__init__(**kwargs)

        with self.canvas.before:
            self._surface_instruction = Color(*self.surface_color)
            self._surface = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            self._border_instruction = Color(*self.border_color)
            self._border = Line(rounded_rectangle=(*self.pos, *self.size, dp(12)), width=1.05)
        self.bind(
            pos=self._atualizar_visual,
            size=self._atualizar_visual,
            focus=self._atualizar_visual,
            disabled=self._atualizar_visual,
            surface_color=self._atualizar_visual,
            disabled_surface_color=self._atualizar_visual,
            border_color=self._atualizar_visual,
            focus_color=self._atualizar_visual,
            text_color=self._atualizar_tinta,
            hint_color=self._atualizar_tinta,
            appearance=self._aplicar_aparencia,
        )
        self._atualizar_visual()

    @staticmethod
    def _palette(appearance):
        if appearance == "dark":
            return {
                "surface_color": [.075, .13, .23, 1],
                "disabled_surface_color": [.10, .15, .23, 1],
                "border_color": [.19, .31, .48, 1],
                "focus_color": [.28, .63, 1, 1],
                "text_color": [.94, .97, 1, 1],
                "hint_color": [.55, .65, .82, 1],
            }
        return {
            "surface_color": [.97, .98, 1, 1],
            "disabled_surface_color": [.90, .93, .97, 1],
            "border_color": [.78, .84, .92, 1],
            "focus_color": [.14, .49, .91, 1],
            "text_color": [.08, .14, .23, 1],
            "hint_color": [.43, .51, .62, 1],
        }

    def _aplicar_aparencia(self, *_args):
        for prop, value in self._palette(self.appearance).items():
            setattr(self, prop, value)
        self.foreground_color = self.text_color
        self.hint_text_color = self.hint_color
        self.cursor_color = self.focus_color
        self._atualizar_visual()

    def _atualizar_visual(self, *_args):
        if not hasattr(self, "_surface_instruction"):
            return
        self._surface.pos = self.pos
        self._surface.size = self.size
        fill = self.disabled_surface_color if self.disabled else self.surface_color
        stroke = self.focus_color if self.focus and not self.disabled else self.border_color
        self._surface_instruction.rgba = fill
        self._border_instruction.rgba = stroke
        self._border.rounded_rectangle = (*self.pos, *self.size, dp(12))
        self._border.width = 1.35 if self.focus and not self.disabled else 1.05

    def _atualizar_tinta(self, *_args):
        self.foreground_color = self.text_color
        self.hint_text_color = self.hint_color
        self.cursor_color = self.focus_color


class CampoTexto(MDTextField):
    """Campo KivyMD com paletas compatíveis com as telas claras e escuras."""

    appearance = OptionProperty("light", options=("light", "dark"))
    surface_color = ListProperty([.97, .98, 1, 1])
    disabled_surface_color = ListProperty([.88, .91, .95, 1])
    border_color = ListProperty([.78, .84, .92, 1])
    focus_color = ListProperty([.14, .49, .91, 1])
    text_color = ListProperty([.08, .14, .23, 1])
    hint_color = ListProperty([.43, .51, .62, 1])

    def __init__(self, **kwargs):
        appearance = kwargs.get("appearance", "light")
        if not kwargs.get("icon_left"):
            icon = self._icone_para_hint(kwargs.get("hint_text", ""))
            if icon:
                kwargs["icon_left"] = icon
        palette = self._palette(appearance)
        for prop, value in palette.items():
            kwargs.setdefault(prop, value)
        kwargs.setdefault("mode", "round")
        kwargs.setdefault("fill_color_normal", palette["surface_color"])
        kwargs.setdefault("fill_color_focus", palette["surface_color"])
        kwargs.setdefault("line_color_normal", palette["border_color"])
        kwargs.setdefault("line_color_focus", palette["focus_color"])
        kwargs.setdefault("text_color_normal", palette["text_color"])
        kwargs.setdefault("text_color_focus", palette["text_color"])
        kwargs.setdefault("hint_text_color_normal", palette["hint_color"])
        kwargs.setdefault("hint_text_color_focus", palette["focus_color"])
        kwargs.setdefault("font_name", "Nunito")
        kwargs.setdefault("font_name_hint_text", "Nunito")
        kwargs.setdefault("font_name_helper_text", "Nunito")
        kwargs.setdefault("cursor_color", palette["focus_color"])
        kwargs.setdefault("padding", (dp(14), dp(12)))
        kwargs.setdefault("write_tab", False)
        super().__init__(**kwargs)
        self.bind(
            surface_color=self._aplicar_cores,
            disabled_surface_color=self._aplicar_cores,
            disabled=self._aplicar_cores,
            border_color=self._aplicar_cores,
            focus_color=self._aplicar_cores,
            text_color=self._aplicar_cores,
            hint_color=self._aplicar_cores,
            appearance=self._aplicar_aparencia,
        )
        self._aplicar_cores()

    @staticmethod
    def _icone_para_hint(hint):
        hint = str(hint).casefold()
        for terms, icon in (
            (("e-mail", "email", "contato"), "email-outline"),
            (("senha", "password"), "lock-outline"),
            (("buscar", "pesquisar", "filtro"), "magnify"),
            (("turma", "matéria", "materia", "conteúdo", "conteudo"), "book-open-page-variant-outline"),
            (("versão", "versao"), "tag-outline"),
            (("descrição", "descricao", "mensagem", "comentário", "comentario"), "text-long"),
            (("comando", "terminal"), "console-line"),
            (("título", "titulo"), "format-title"),
            (("nome",), "account-outline"),
        ):
            if any(term in hint for term in terms):
                return icon
        return ""

    @staticmethod
    def _palette(appearance):
        if appearance == "dark":
            return {
                "surface_color": [.075, .13, .23, 1],
                "disabled_surface_color": [.10, .15, .23, 1],
                "border_color": [.19, .31, .48, 1],
                "focus_color": [.28, .63, 1, 1],
                "text_color": [.94, .97, 1, 1],
                "hint_color": [.55, .65, .82, 1],
            }
        return {
            "surface_color": [.97, .98, 1, 1],
            "disabled_surface_color": [.90, .93, .97, 1],
            "border_color": [.78, .84, .92, 1],
            "focus_color": [.14, .49, .91, 1],
            "text_color": [.08, .14, .23, 1],
            "hint_color": [.43, .51, .62, 1],
        }

    def _aplicar_aparencia(self, *_args):
        for prop, value in self._palette(self.appearance).items():
            setattr(self, prop, value)
        self._aplicar_cores()

    def _aplicar_cores(self, *_args):
        fill = self.disabled_surface_color if self.disabled else self.surface_color
        self.fill_color_normal = fill
        self.fill_color_focus = fill
        self.line_color_normal = self.border_color
        self.line_color_focus = self.focus_color
        self.text_color_normal = self.text_color
        self.text_color_focus = self.text_color
        self.hint_text_color_normal = self.hint_color
        self.hint_text_color_focus = self.focus_color
        self.cursor_color = self.focus_color


Factory.register("BotaoAcao", cls=BotaoAcao)
Factory.register("IconeUI", cls=IconeUI)
Factory.register("CampoTexto", cls=CampoTexto)
Factory.register("CampoTextoClassico", cls=CampoTextoClassico)
Factory.register('BotaoHover', cls=BotaoHover)
