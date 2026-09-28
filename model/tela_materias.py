"""Experiência de equipes educacionais para a área de matérias."""
from __future__ import annotations

import os
from functools import partial
from pathlib import Path

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import SlideTransition

from model.componentes import BotaoAcao, CampoTexto, IconeUI, LayoutFundo
from model.materias import Comentario, Conteudo, Materia, Publicacao, Topico, Trabalho


class TeamCard(ButtonBehavior, BoxLayout):
    """Card clicável que abre a equipe ao tocar nele."""

    pass


class TelaMaterias(LayoutFundo):
    """Lista equipes e renderiza uma experiência interna em seções."""

    titulo = StringProperty("Equipes e matérias")
    status_texto = StringProperty("Carregando dados locais...")
    pode_editar = BooleanProperty(False)
    pode_gerenciar_materia = BooleanProperty(False)
    papel = StringProperty("aluno")
    equipe_id = StringProperty("")
    secao = StringProperty("feed")
    secao_inicial = StringProperty("feed")
    modo_equipe = BooleanProperty(False)
    documento_topico_id = StringProperty("")
    documento_conteudo_id = StringProperty("")
    filtro_equipes = StringProperty("")
    SECOES = (("feed", "Mural"), ("teorico", "Aulas"), ("arquivos", "Arquivos"),
              ("trabalhos", "Atividades"), ("testes", "Avaliações"), ("info", "Sobre a turma"))

    def on_kv_post(self, _base_widget): self.atualizar()
    @property
    def _service(self): return App.get_running_app().materias_service
    def _perfil(self): return App.get_running_app().session_manager.user or {}
    def _autor(self):
        profile = self._perfil(); return profile.get("name") or profile.get("email") or "Usuário local"
    def _email(self): return self._perfil().get("email") or ""

    def atualizar(self, secao="feed"):
        self.secao_inicial = secao if secao in {key for key, _title in self.SECOES} else "feed"
        app = App.get_running_app()
        permissions = app.permission_service
        profile = self._perfil()
        self.papel = permissions.papel_do_perfil(profile).value
        self.pode_editar = permissions.perfil_pode_editar_materias(profile)
        self.pode_gerenciar_materia = permissions.perfil_pode_gerenciar_materias(profile)
        self.mostrar_equipes()

    def voltar(self):
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="right", duration=.25); manager.current = "principal"

    def _clear(self):
        self.ids.conteudo.clear_widgets(); return self.ids.conteudo
    def _button(self, text, action, danger=False, compact=False, variant=None):
        variant = "danger" if danger else variant or "primary"
        button = BotaoAcao(text=text, variant=variant,
            size_hint_y=None, height=dp(36 if compact else 46),
            color=(.10, .24, .42, 1) if variant == "light" else (1, 1, 1, 1),
            font_size="13sp", bold=True,
            padding=(dp(12), dp(6)))
        button.bind(on_release=lambda _instance: action()); return button
    def _text(self, value, height=28, bold=False, color=(.91, .95, 1, 1), size="14sp", preserve_color=False):
        # A maior parte dos textos antigos usava tinta escura sobre o fundo claro.
        # Converte tons escuros para a paleta clara desta experiência de equipes.
        if not preserve_color and color[0] < .3 and color[1] < .4 and color[2] < .55:
            color = (.87, .92, .99, 1)
        label = Label(text=value, size_hint_y=None, height=dp(height), color=color, bold=bold, font_size=size, halign="left", valign="middle")
        label.bind(width=lambda item, width: setattr(item, "text_size", (width, None))); return label
    def _paragraph(self, value, color=(.90, .94, 1, 1), size="13sp", minimum=30):
        label = Label(text=value, size_hint_y=None, height=dp(minimum), color=color, font_size=size,
                      halign="left", valign="top", padding=(0, dp(3)))
        label.bind(width=lambda item, width: setattr(item, "text_size", (max(1, width), None)))
        label.bind(texture_size=lambda item, measured: setattr(item, "height", max(dp(minimum), measured[1] + dp(8))))
        return label
    def _avatar(self, initials, diameter=dp(38), color=(.10, .43, .82, 1)):
        avatar = Label(text=initials or "PM", size_hint=(None, None), size=(diameter, diameter),
                       color=(1, 1, 1, 1), bold=True, font_size="11sp")
        with avatar.canvas.before:
            Color(*color)
            background = Ellipse(pos=avatar.pos, size=avatar.size)
        avatar.bind(pos=lambda item, value: setattr(background, "pos", value),
                    size=lambda item, value: setattr(background, "size", value))
        return avatar
    def _empty(self, value): return Label(text=value, color=(.67, .75, .89, 1), halign="center", valign="middle", text_size=(dp(720), None))
    def _card(self, height, color=(.065, .21, .47, 1), border=None):
        card = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(18), spacing=dp(10))
        if height is None:
            card.bind(minimum_height=card.setter("height"))
        else:
            card.height = dp(height)
        with card.canvas.before:
            Color(.03, .14, .30, .08) if color[0] > .8 else Color(0, 0, 0, 0)
            shadow = RoundedRectangle(pos=(card.x + dp(2), card.y - dp(3)), size=card.size, radius=[dp(16)])
            Color(*color)
            background = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(16)])
            if border:
                Color(*border)
                outline = Line(rounded_rectangle=(*card.pos, *card.size, dp(16)), width=dp(1))
            else:
                outline = None
        def update(_item, _value):
            shadow.pos = (card.x + dp(2), card.y - dp(3))
            shadow.size = card.size
            background.pos = card.pos
            background.size = card.size
            if outline is not None:
                outline.rounded_rectangle = (*card.pos, *card.size, dp(16))
        card.bind(pos=update, size=update)
        return card

    def _comment_bubble(self, comment):
        own_message = (comment.autor or "").strip().casefold() == self._autor().strip().casefold()
        bubble = BoxLayout(orientation="vertical", size_hint=(.84, None), padding=(dp(13), dp(10)),
                           spacing=dp(5))
        bubble.bind(minimum_height=bubble.setter("height"))
        fill = (.85, .93, 1, 1) if own_message else (1, 1, 1, 1)
        with bubble.canvas.before:
            Color(*fill)
            background = RoundedRectangle(pos=bubble.pos, size=bubble.size, radius=[dp(14)])
            Color(.77, .85, .94, 1)
            outline = Line(rounded_rectangle=(*bubble.pos, *bubble.size, dp(14)), width=dp(.8))
        def update(_item, _value):
            background.pos = bubble.pos
            background.size = bubble.size
            outline.rounded_rectangle = (*bubble.pos, *bubble.size, dp(14))
        bubble.bind(pos=update, size=update)

        meta = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(8))
        author = Label(text=comment.autor or "Membro da turma", color=(.10, .27, .47, 1),
                       bold=True, font_size="11sp", halign="left", valign="middle")
        author.bind(size=lambda item, size: setattr(item, "text_size", size))
        timestamp = Label(text=self._horario(comment.criado_em), color=(.42, .52, .64, 1),
                          font_size="10sp", halign="right", valign="middle",
                          size_hint_x=None, width=dp(58))
        timestamp.bind(size=lambda item, size: setattr(item, "text_size", size))
        meta.add_widget(author)
        meta.add_widget(timestamp)
        bubble.add_widget(meta)
        bubble.add_widget(self._paragraph(comment.mensagem, color=(.15, .22, .32, 1),
                                          size="12sp", minimum=22))

        row = AnchorLayout(anchor_x="right" if own_message else "left", anchor_y="center",
                           size_hint_y=None, height=bubble.height)
        bubble.bind(height=lambda _item, value: setattr(row, "height", value))
        row.add_widget(bubble)
        return row

    def _conversation_panel(self, comments):
        conversation = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(12), spacing=dp(8))
        conversation.bind(minimum_height=conversation.setter("height"))
        with conversation.canvas.before:
            Color(.94, .97, 1, 1)
            background = RoundedRectangle(pos=conversation.pos, size=conversation.size, radius=[dp(15)])
            Color(.85, .90, .97, 1)
            outline = Line(rounded_rectangle=(*conversation.pos, *conversation.size, dp(15)), width=dp(.8))
        def update(_item, _value):
            background.pos = conversation.pos
            background.size = conversation.size
            outline.rounded_rectangle = (*conversation.pos, *conversation.size, dp(15))
        conversation.bind(pos=update, size=update)
        heading = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(8))
        heading.add_widget(Label(text="CONVERSA", color=(.14, .36, .62, 1), bold=True,
                                 font_size="10sp", halign="left", valign="middle"))
        heading.add_widget(Label(text=f"{len(comments)} respostas", color=(.43, .53, .66, 1),
                                 font_size="10sp", halign="right", valign="middle"))
        conversation.add_widget(heading)
        for comment in comments[-5:]:
            conversation.add_widget(self._comment_bubble(comment))
        return conversation

    def _team_card(self, height, action):
        card = TeamCard(orientation="vertical", size_hint=(1, None), height=dp(height), padding=dp(16), spacing=dp(7))
        with card.canvas.before:
            Color(.065, .21, .47, 1)
            background = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
        card.bind(pos=lambda item, value: setattr(background, "pos", value), size=lambda item, value: setattr(background, "size", value))
        card.bind(on_release=lambda *_args: action())
        return card
    def _center(self, panel, widget):
        """Centraliza cartões para manter o mural confortável para leitura."""
        row = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=widget.height)
        widget.size_hint_x = .94
        widget.bind(height=lambda _widget, value: setattr(row, "height", value))
        row.add_widget(widget); panel.add_widget(row)

    def _update_card_widths(self, *args):
        """Ajusta a largura dos cards para ocupar 1/cols da largura do GridLayout."""
        try:
            area = self.ids.conteudo
        except Exception:
            return

        if self.equipe_id or not area.children:
            area.cols = 1
            return
        width = area.width
        area.cols = 3 if width >= dp(1100) else 2 if width >= dp(700) else 1

    def filtrar_equipes(self, texto):
        self.filtro_equipes = texto or ""
        if not self.equipe_id and self.ids.get("conteudo") is not None:
            self.mostrar_equipes()

    # Lista de equipes/matérias
    def mostrar_equipes(self):
        self.equipe_id = ""; self.titulo = "Turmas"
        all_subjects = self._service.listar()
        query = self.filtro_equipes.strip().casefold()
        materias = [item for item in all_subjects if not query or query in " ".join((item.nome, item.categoria, item.descricao)).casefold()]
        area = self._clear()
        area.cols = 3 if area.width >= dp(1100) else 2 if area.width >= dp(700) else 1
        app = App.get_running_app()
        self.pode_editar = app.permission_service.perfil_pode_editar_materias(self._perfil())
        self.pode_gerenciar_materia = app.permission_service.perfil_pode_gerenciar_materias(self._perfil())
        noun = "turma" if len(materias) == 1 else "turmas"
        self.status_texto = f"{len(materias)} {noun} • aulas, conversas e materiais organizados em um só lugar"
        if not materias:
            message = "Nenhuma turma corresponde à pesquisa." if query else "Ainda não há turmas cadastradas.\nUm professor pode criar a primeira turma para começar."
            empty = self._card(None)
            empty.add_widget(self._text("Vamos começar por aqui", 36, True, size="20sp"))
            empty.add_widget(self._text(message, 54, color=(.76, .84, .96, 1), size="14sp"))
            if self.pode_gerenciar_materia:
                empty.add_widget(self._button("Criar turma", self.editar_materia))
            area.add_widget(empty)
            return
        for materia in materias:
            card = self._team_card(232, partial(self.abrir_equipe, materia.id, self.secao_inicial))
            team_header = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(12))
            initials = "".join(word[0] for word in materia.nome.split()[:2]).upper() or "PM"
            badge = Button(text=initials, disabled=True, size_hint=(None, None), size=(dp(52), dp(52)), background_normal="", background_color=(.17, .48, .85, 1), color=(1, 1, 1, 1), font_size="17sp", bold=True)
            team_header.add_widget(badge)
            labels = BoxLayout(orientation="vertical", spacing=dp(1))
            labels.add_widget(self._text(materia.nome, 30, True, size="17sp"))
            labels.add_widget(self._text(materia.categoria, 20, color=(.64, .79, 1, 1), size="12sp"))
            team_header.add_widget(labels); card.add_widget(team_header)
            card.add_widget(self._text(f"{len(materia.topicos)} módulos  •  {len(materia.publicacoes)} publicações  •  {len(materia.arquivos)} arquivos", 22, color=(.81, .88, .98, 1), size="12sp"))
            card.add_widget(self._text(materia.descricao or "Entre para acompanhar as aulas e conversar com a turma.", 36, color=(.78, .85, .96, 1), size="12sp"))
            actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
            actions.add_widget(self._button("Abrir turma", partial(self.abrir_equipe, materia.id, self.secao_inicial), compact=True))
            can_manage_team = app.permission_service.perfil_pode_gerenciar_materias(
                self._perfil(), materia.criado_por_email
            )
            if can_manage_team:
                actions.add_widget(self._button("Configurar", partial(self.editar_materia, materia.id), compact=True))
                actions.add_widget(self._button("Excluir", partial(self.confirmar_exclusao_materia, materia.id), danger=True, compact=True))
            card.add_widget(actions)
            area.add_widget(card)

        # Vincula atualização de largura para que cada card ocupe 1/3 da área
        try:
            area.bind(width=self._update_card_widths)
            # executa uma vez agora
            self._update_card_widths()
        except Exception:
            pass

    # Navegação interna da equipe
    def abrir_equipe(self, materia_id, secao="feed"):
        if secao not in {key for key, _title in self.SECOES}:
            secao = "feed"
        # A lista e a equipe são telas distintas no gerenciador. Isso mantém uma
        # área de trabalho própria para a equipe, em vez de apenas trocar um card.
        if not self.modo_equipe:
            manager = App.get_running_app().root
            target = manager.get_screen("equipe").children[0]
            target.papel, target.pode_editar = self.papel, self.pode_editar
            manager.transition = SlideTransition(direction="left", duration=.22)
            target.abrir_equipe(materia_id, secao)
            manager.current = "equipe"
            return
        self.equipe_id, self.secao = materia_id, secao
        materia = self._service.obter(materia_id); self.titulo = materia.nome
        app = App.get_running_app()
        profile = self._perfil()
        self.pode_editar = app.permission_service.perfil_pode_editar_conteudo(
            profile, materia_id, materia.criado_por_email
        )
        self.pode_gerenciar_materia = app.permission_service.perfil_pode_gerenciar_materias(
            profile, materia.criado_por_email
        )
        self.status_texto = f"{materia.categoria} • {len(materia.publicacoes)} publicações • {len(materia.arquivos)} arquivos"
        area = self._clear(); area.cols = 1
        header = BoxLayout(size_hint_y=None, height=dp(82), spacing=dp(14), padding=(dp(14), dp(10)))
        with header.canvas.before:
            Color(.065, .21, .47, 1)
            header_background = RoundedRectangle(pos=header.pos, size=header.size, radius=[dp(16)])
        header.bind(pos=lambda item, value: setattr(header_background, "pos", value), size=lambda item, value: setattr(header_background, "size", value))
        header.add_widget(self._button("‹  Turmas", self.mostrar_equipes, compact=True))
        emblem = Button(text="".join(word[0] for word in materia.nome.split()[:2]).upper() or "PM", disabled=True, size_hint=(None, None), size=(dp(52), dp(52)), background_normal="", background_color=(.17, .48, .85, 1), color=(1, 1, 1, 1), bold=True, font_size="18sp")
        header.add_widget(emblem)
        title_group = BoxLayout(orientation="vertical", spacing=dp(1))
        title_group.add_widget(self._text(materia.nome, 30, True, size="20sp"))
        title_group.add_widget(self._text(f"{materia.categoria}  •  {materia.status}", 22, color=(.77, .86, .99, 1), size="12sp"))
        header.add_widget(title_group); header.add_widget(Label())
        if self.pode_gerenciar_materia:
            header.add_widget(self._button("Configurar", partial(self.editar_materia, materia.id), compact=True))
        area.add_widget(header)

        nav = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8), padding=(dp(4), dp(6)))
        for key, title in self.SECOES:
            selected = key == self.secao
            tab = BotaoAcao(text=title, variant="primary" if selected else "secondary",
                size_hint_x=1, size_hint_y=None, height=dp(42),
                color=(1, 1, 1, 1), font_size="12sp", bold=selected)
            tab.bind(on_release=lambda _item, section=key: self.abrir_equipe(materia_id, section)); nav.add_widget(tab)
        area.add_widget(nav)

        shell = BoxLayout(size_hint_y=None, height=max(dp(450), Window.height - dp(265)), spacing=dp(12))
        panel_scroll = ScrollView(do_scroll_x=False, bar_width=dp(7))
        panel = GridLayout(cols=1, spacing=dp(12), padding=(dp(10), dp(10), dp(20), dp(18)), size_hint_y=None)
        panel.bind(minimum_height=panel.setter("height")); panel_scroll.add_widget(panel)
        shell.add_widget(panel_scroll); area.add_widget(shell)
        getattr(self, f"_render_{self.secao}")(materia, panel)
    def _toolbar(self, panel, primary=None):
        toolbar = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        if primary and self.pode_editar: toolbar.add_widget(self._button(*primary, compact=True))
        elif primary: toolbar.add_widget(self._text("Visualização para alunos", 30, color=(.22, .33, .48, 1)))
        panel.add_widget(toolbar)

    # Feed de publicações
    def _render_feed(self, materia, panel):
        visible_posts = [post for post in materia.publicacoes if self.pode_editar or post.status.casefold() != "rascunho"]
        heading = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(10), padding=(dp(4), 0))
        labels = BoxLayout(orientation="vertical", spacing=dp(1))
        labels.add_widget(self._text("Mural da turma", 30, True, color=(.08, .20, .37, 1), size="20sp", preserve_color=True))
        labels.add_widget(self._text("Aulas, avisos e conversas em um só lugar.", 22, color=(.34, .43, .55, 1), size="12sp", preserve_color=True))
        heading.add_widget(labels); heading.add_widget(Label())
        heading.add_widget(self._text(f"{len(visible_posts)} publicações", 28, True, color=(.14, .39, .69, 1), size="12sp", preserve_color=True))
        panel.add_widget(heading)

        composer = self._card(None, color=(1, 1, 1, 1), border=(.84, .90, .97, 1))
        identity = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(11))
        initials = "".join(part[0] for part in self._autor().split()[:2]).upper()
        identity.add_widget(self._avatar(initials, dp(40), (.12, .43, .80, 1)))
        identity_text = BoxLayout(orientation="vertical", spacing=dp(1))
        identity_text.add_widget(self._text(self._autor(), 22, True, color=(.10, .20, .34, 1), size="13sp", preserve_color=True))
        identity_text.add_widget(self._text("Professor" if self.pode_editar else "Aluno", 18, color=(.43, .53, .66, 1), size="11sp", preserve_color=True))
        identity.add_widget(identity_text)
        composer.add_widget(identity)
        composer.add_widget(self._text(
            "Compartilhe uma aula, orientação ou aviso com a turma." if self.pode_editar
            else "Tem uma dúvida? Comece uma conversa com a turma e o professor.",
            24, color=(.34, .43, .55, 1), size="13sp", preserve_color=True))
        actions = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        if self.pode_editar:
            actions.add_widget(self._button("Publicar aula", partial(self.editar_publicacao, materia.id, None, "aula")))
            actions.add_widget(self._button("Novo aviso", partial(self.editar_publicacao, materia.id, None, "aviso"), compact=True, variant="light"))
        else:
            actions.add_widget(self._button("Fazer uma pergunta", partial(self.editar_publicacao, materia.id, None, "pergunta")))
        actions.add_widget(Label())
        if self.pode_editar:
            actions.add_widget(self._button("Abrir arquivos da turma", partial(self.abrir_equipe, materia.id, "arquivos"), compact=True, variant="light"))
        composer.add_widget(actions)
        self._center(panel, composer)

        if not visible_posts:
            empty = self._card(None, color=(.97, .99, 1, 1), border=(.86, .91, .97, 1))
            empty.add_widget(self._text("O mural ainda está vazio", 34, True, color=(.10, .20, .34, 1), size="18sp", preserve_color=True))
            empty.add_widget(self._text("As publicações da turma vão aparecer aqui. Professores podem postar aulas; alunos podem iniciar uma pergunta.", 48, color=(.40, .49, .61, 1), size="13sp", preserve_color=True))
            self._center(panel, empty)
            return

        files_by_id = {item.id: item for item in materia.arquivos}
        labels_by_type = {"aula": "AULA", "aviso": "AVISO", "pergunta": "DÚVIDA", "recado": "RECADO", "conteudo": "MATERIAL", "tarefa": "ATIVIDADE"}
        for post in sorted(visible_posts, key=lambda item: item.criado_em, reverse=True):
            card = self._card(None, color=(1, 1, 1, 1), border=(.84, .90, .97, 1))
            author = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
            initials = "".join(part[0] for part in (post.autor or "PM").split()[:2]).upper()
            author.add_widget(self._avatar(initials, dp(38), (.12, .43, .80, 1)))
            author.add_widget(self._text(post.autor or "Membro da turma", 34, True, color=(.10, .20, .34, 1), size="13sp", preserve_color=True))
            author.add_widget(self._text(self._data(post.criado_em), 34, color=(.47, .56, .67, 1), size="11sp", preserve_color=True))
            author.add_widget(Label())
            author.add_widget(self._text(labels_by_type.get(post.tipo, post.tipo.upper()), 30, True, color=(.12, .43, .77, 1), size="11sp", preserve_color=True))
            if post.status.casefold() == "rascunho":
                author.add_widget(self._text("RASCUNHO", 30, True, color=(.67, .39, .04, 1), size="10sp", preserve_color=True))
            card.add_widget(author)
            card.add_widget(self._text(post.titulo, 34, True, color=(.09, .19, .32, 1), size="18sp", preserve_color=True))
            card.add_widget(self._paragraph(post.mensagem, color=(.27, .35, .46, 1), size="13sp"))
            if post.anexos:
                card.add_widget(self._text("Anexos: " + "  •  ".join(post.anexos), 22, color=(.28, .42, .61, 1), size="12sp", preserve_color=True))
            linked_files = [files_by_id[item] for item in post.arquivos_ids if item in files_by_id]
            for shared_file in linked_files:
                card.add_widget(self._button(
                    f"Abrir arquivo  ·  {shared_file.nome}  ·  {self._tamanho(shared_file.tamanho)}",
                    partial(self.abrir_arquivo, shared_file.caminho_local), compact=True, variant="light"))
            if post.arquivos_ids and len(linked_files) < len(post.arquivos_ids):
                card.add_widget(self._text("Um ou mais anexos foram removidos da biblioteca da turma.", 20, color=(.45, .53, .64, 1), size="11sp", preserve_color=True))
            if post.comentarios:
                card.add_widget(self._conversation_panel(post.comentarios))
            else:
                card.add_widget(self._text("Ainda sem respostas. Inicie a conversa com a turma.", 22, color=(.48, .57, .68, 1), size="11sp", preserve_color=True))
            actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
            actions.add_widget(self._button("Responder", partial(self.comentar_publicacao, materia.id, post.id), compact=True, variant="light"))
            if self.pode_editar:
                actions.add_widget(self._button("Editar", partial(self.editar_publicacao, materia.id, post.id), compact=True, variant="light"))
                actions.add_widget(self._button("Excluir", partial(self.confirmar_exclusao_publicacao, materia.id, post.id), True, True))
            card.add_widget(actions)
            self._center(panel, card)

    def _render_arquivos(self, materia, panel):
        heading = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(10))
        labels = BoxLayout(orientation="vertical")
        labels.add_widget(self._text("Arquivos da turma", 30, True, color=(.08, .20, .37, 1), size="20sp", preserve_color=True))
        labels.add_widget(self._text("Materiais guardados na biblioteca local desta turma.", 22, color=(.28, .39, .54, 1), size="12sp", preserve_color=True))
        heading.add_widget(labels); heading.add_widget(Label())
        if self.pode_editar:
            heading.add_widget(self._button("Enviar arquivo", partial(self.selecionar_arquivo, materia.id)))
        panel.add_widget(heading)
        if not materia.arquivos:
            empty = self._card(None)
            empty.add_widget(self._text("Nenhum arquivo compartilhado", 32, True, size="18sp"))
            empty.add_widget(self._text("O professor pode enviar PDFs, apresentações, documentos e outros materiais para a turma.", 44, color=(.76, .84, .96, 1), size="13sp"))
            if self.pode_editar:
                empty.add_widget(self._button("Enviar o primeiro arquivo", partial(self.selecionar_arquivo, materia.id)))
            self._center(panel, empty)
            return
        for arquivo in sorted(materia.arquivos, key=lambda item: item.criado_em, reverse=True):
            card = self._card(None)
            file_heading = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(10))
            file_heading.add_widget(IconeUI(nome="file-document-outline", size_hint=(None, None), size=(dp(22), dp(22)), color=(.55, .78, 1, 1)))
            file_heading.add_widget(self._text(arquivo.nome, 30, True, size="16sp"))
            card.add_widget(file_heading)
            card.add_widget(self._text(f"{arquivo.tipo}  ·  {self._tamanho(arquivo.tamanho)}  ·  enviado por {arquivo.autor}  ·  {self._data(arquivo.criado_em)}", 24, color=(.76, .84, .96, 1), size="12sp"))
            actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
            actions.add_widget(self._button("Abrir arquivo", partial(self.abrir_arquivo, arquivo.caminho_local), compact=True))
            if self.pode_editar:
                actions.add_widget(self._button("Remover", partial(self.confirmar_exclusao_arquivo, materia.id, arquivo.id), True, True))
            actions.add_widget(Label())
            card.add_widget(actions)
            self._center(panel, card)

    def _render_trabalhos(self, materia, panel):
        self._toolbar(panel, ("+ Novo trabalho", partial(self.editar_trabalho, materia.id, None)))
        panel.add_widget(self._empty(" "))
        if not materia.trabalhos: panel.add_widget(self._empty("Nenhum trabalho delegado nesta equipe.")); return
        for trabalho in materia.trabalhos:
            card = self._card(None); entregue = self._email() in trabalho.entregue_por
            card.add_widget(self._text(f"{trabalho.categoria.upper()}  •  {trabalho.status}", 20, True, color=(.07, .34, .72, 1), size="12sp"))
            card.add_widget(self._text(trabalho.titulo, 26, True, size="16sp")); card.add_widget(self._text(trabalho.descricao or "Sem descrição.", 30))
            card.add_widget(self._text(f"Prazo: {trabalho.prazo}  •  {len(trabalho.entregue_por)} entrega(s)", 20, color=(.25, .35, .48, 1), size="12sp"))
            if trabalho.anexos: card.add_widget(self._text("Anexos: " + ", ".join(trabalho.anexos), 18, color=(.07, .34, .72, 1), size="12sp"))
            actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            if not self.pode_editar and not entregue: actions.add_widget(self._button("Marcar como entregue", partial(self.entregar_trabalho, materia.id, trabalho.id), compact=True))
            elif entregue:
                confirmation = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(7))
                confirmation.add_widget(IconeUI(nome="check-circle-outline", size_hint=(None, None), size=(dp(18), dp(18)), color=(.32, .82, .57, 1)))
                confirmation.add_widget(self._text("Entregue por você", 24, color=(.32, .82, .57, 1), size="12sp"))
                actions.add_widget(confirmation)
            if self.pode_editar:
                actions.add_widget(self._button("Editar", partial(self.editar_trabalho, materia.id, trabalho.id), compact=True)); actions.add_widget(self._button("Excluir", partial(self.confirmar_exclusao_trabalho, materia.id, trabalho.id), True, True))
            card.add_widget(actions); panel.add_widget(card)

    # Conteúdo no formato de documentação
    def _conteudo_visivel(self, topico, content, categoria):
        if content.categoria != categoria:
            return False
        if self.pode_editar:
            return True
        return topico.status.casefold() in {"ativo", "publicado"} and content.status.casefold() in {"ativo", "publicado"}

    def _render_teorico(self, materia, panel): self._render_documentacao(materia, panel, "teorico", "Documentação didática")
    def _render_testes(self, materia, panel): self._render_documentacao(materia, panel, "testes", "Provas e avaliações")
    def _render_documentacao(self, materia, panel, categoria, heading):
        toolbar = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(10))
        heading_group = BoxLayout(orientation="vertical", spacing=dp(1))
        heading_group.add_widget(self._text("Aulas e materiais" if categoria == "teorico" else heading, 32, True, color=(.08, .20, .37, 1), size="20sp", preserve_color=True))
        heading_group.add_widget(self._text("Aprenda por módulos, no seu ritmo." if categoria == "teorico" else "Materiais de avaliação da turma.", 22, color=(.28, .39, .54, 1), size="12sp", preserve_color=True))
        toolbar.add_widget(heading_group); toolbar.add_widget(Label())
        if self.pode_editar:
            toolbar.add_widget(self._button("Novo módulo", partial(self.editar_topico, materia.id, None), compact=True))
        panel.add_widget(toolbar)
        chapters = [(topico, content) for topico in materia.topicos for content in topico.conteudos if self._conteudo_visivel(topico, content, categoria)]
        if not chapters:
            empty = self._card(None)
            is_tests = categoria == "testes"
            empty.add_widget(self._text("Ainda não há materiais de apoio" if is_tests else "Ainda não há aulas nesta área", 34, True, size="19sp"))
            empty.add_widget(self._text(
                "Os materiais de avaliação publicados pela equipe aparecerão aqui." if is_tests else
                "O professor pode organizar o material em módulos e publicar cada aula aqui. Arquivos da turma ficam disponíveis na aba Arquivos.",
                54, color=(.76, .84, .96, 1), size="13sp",
            ))
            if self.pode_editar and not materia.topicos:
                empty.add_widget(self._button("Criar o primeiro módulo", partial(self.editar_topico, materia.id, None)))
            self._center(panel, empty)
            if self.pode_editar and materia.topicos:
                for topico in materia.topicos:
                    module_card = self._card(None)
                    module_card.add_widget(self._text(topico.titulo, 30, True, size="16sp"))
                    if topico.descricao:
                        module_card.add_widget(self._paragraph(topico.descricao, color=(.80, .87, .97, 1), size="12sp"))
                    module_card.add_widget(self._button("Adicionar aula a este módulo", partial(self.editar_conteudo, materia.id, topico.id, None), compact=True))
                    self._center(panel, module_card)
            return
        chosen_topico, chosen = next((item for item in chapters if item[1].id == self.documento_conteudo_id), chapters[0])
        self.documento_topico_id = chosen_topico.id
        self.documento_conteudo_id = chosen.id
        doc_height = max(dp(430), Window.height - dp(380))
        doc = BoxLayout(size_hint_y=None, height=doc_height, spacing=dp(12))

        index_panel = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(250), spacing=dp(8), padding=dp(14))
        with index_panel.canvas.before:
            Color(.065, .21, .47, 1)
            index_background = RoundedRectangle(pos=index_panel.pos, size=index_panel.size, radius=[dp(14)])
        index_panel.bind(pos=lambda item, value: setattr(index_background, "pos", value), size=lambda item, value: setattr(index_background, "size", value))
        index_panel.add_widget(self._text("MÓDULOS", 28, True, color=(.68, .84, 1, 1), size="11sp"))
        index_scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        index_list = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        index_list.bind(minimum_height=index_list.setter("height"))
        topics = [topico for topico in materia.topicos if self.pode_editar or topico.status.casefold() in {"ativo", "publicado"}]
        for topico in topics:
            index_list.add_widget(self._text(topico.titulo, 28, True, color=(.91, .95, 1, 1), size="13sp"))
            topic_contents = [content for content in topico.conteudos if self._conteudo_visivel(topico, content, categoria)]
            for content in topic_contents:
                active = content.id == chosen.id
                button = self._button("  " + content.titulo, partial(self.ver_documento, materia.id, content.id), compact=True)
                button.size_hint_x = 1
                button.background_color = (.15, .48, .86, 1) if active else (.10, .29, .54, 1)
                index_list.add_widget(button)
            if self.pode_editar:
                index_list.add_widget(self._button("Adicionar aula", partial(self.editar_conteudo, materia.id, topico.id, None), compact=True))
        index_scroll.add_widget(index_list)
        index_panel.add_widget(index_scroll)

        body_panel = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(20), size_hint_y=None)
        with body_panel.canvas.before:
            Color(.065, .21, .47, 1)
            body_background = RoundedRectangle(pos=body_panel.pos, size=body_panel.size, radius=[dp(14)])
        body_panel.bind(pos=lambda item, value: setattr(body_background, "pos", value), size=lambda item, value: setattr(body_background, "size", value))
        body_panel.add_widget(self._text(chosen_topico.titulo.upper(), 22, True, color=(.67, .83, 1, 1), size="11sp"))
        body_panel.add_widget(self._text(chosen.titulo, 42, True, size="23sp"))
        body_panel.add_widget(self._text(f"{chosen.status.title()}  ·  atualizado em {self._data(chosen.atualizado_em)}", 22, color=(.72, .82, .97, 1), size="11sp"))
        if chosen.descricao:
            body_panel.add_widget(self._paragraph(chosen.descricao, color=(.85, .90, .98, 1), size="14sp"))
        body_panel.add_widget(self._paragraph(chosen.corpo or "Esta aula ainda não tem texto. O professor pode editar o material para adicionar a explicação.", color=(.92, .95, 1, 1), size="14sp", minimum=72))
        if self.pode_editar:
            body_panel.add_widget(self._button("Editar esta aula", partial(self.editar_conteudo, materia.id, chosen_topico.id, chosen.id), compact=True))
        current_index = next((index for index, item in enumerate(chapters) if item[1].id == chosen.id), 0)
        steps = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        previous = self._button("Aula anterior", partial(self.mover_documento, materia.id, categoria, -1), compact=True)
        previous.disabled = current_index == 0
        steps.add_widget(previous); steps.add_widget(Label())
        next_button = self._button("Próxima aula", partial(self.mover_documento, materia.id, categoria, 1), compact=True)
        next_button.disabled = current_index == len(chapters) - 1
        steps.add_widget(next_button)
        body_panel.add_widget(steps)
        body_panel.bind(minimum_height=body_panel.setter("height"))
        body_content = GridLayout(cols=1, size_hint_y=None, spacing=dp(8))
        body_content.bind(minimum_height=body_content.setter("height"))
        body_content.add_widget(body_panel)
        body_scroll = ScrollView(do_scroll_x=False, bar_width=dp(6))
        body_scroll.add_widget(body_content)
        doc.add_widget(index_panel); doc.add_widget(body_scroll); panel.add_widget(doc)

    def mover_documento(self, materia_id, categoria, deslocamento):
        materia = self._service.obter(materia_id)
        chapters = [(topic, content) for topic in materia.topicos for content in topic.conteudos if self._conteudo_visivel(topic, content, categoria)]
        index = next((i for i, item in enumerate(chapters) if item[1].id == self.documento_conteudo_id), 0)
        target = max(0, min(len(chapters) - 1, index + deslocamento))
        if chapters:
            self.documento_conteudo_id = chapters[target][1].id
            self.abrir_equipe(materia_id, self.secao)
    def ver_documento(self, materia_id, conteudo_id):
        self.documento_conteudo_id = conteudo_id
        self.abrir_equipe(materia_id, self.secao)

    def _render_info(self, materia, panel):
        if self.pode_gerenciar_materia:
            self._toolbar(panel, ("Editar informações", partial(self.editar_materia, materia.id)))
        else:
            self._toolbar(panel, None)
        panel.add_widget(self._empty(" "))
        card = self._card(260); card.add_widget(self._text("Sobre esta turma", 32, True, size="19sp")); card.add_widget(self._text(materia.descricao or "Sem descrição.", 55))
        card.add_widget(self._text(f"Categoria: {materia.categoria}\nStatus: {materia.status}\nCriada em: {self._data(materia.criado_em)}\n{len(materia.topicos)} módulos, {len(materia.publicacoes)} publicações, {len(materia.arquivos)} arquivos e {len(materia.trabalhos)} atividades.", 90))
        card.add_widget(self._paragraph("As turmas e os arquivos são armazenados localmente neste computador. A sincronização automática entre computadores ainda não está configurada.", color=(.76, .84, .96, 1), size="12sp", minimum=42))
        panel.add_widget(card)

    # Formulários de gestão estilizados e reutilizáveis
    def exigir_edicao(self, materia_id=None):
        if materia_id:
            materia = self._service.obter(materia_id)
            if App.get_running_app().permission_service.perfil_pode_editar_conteudo(
                self._perfil(), materia_id, materia.criado_por_email
            ):
                return True
        self._mensagem("Sem permissão", "Professores podem alterar equipes próprias ou matérias atribuídas a eles.")
        return False

    def _exigir_internet(self, action):
        app = App.get_running_app()
        try:
            app.internet_service.require_online(offline_mode=app.settings.offline_mode, action=action)
            return True
        except ConnectionError as error:
            self._mensagem("Conexão necessária", str(error))
            return False

    def editar_materia(self, materia_id=None):
        materia = self._service.obter(materia_id) if materia_id else Materia()
        app = App.get_running_app()
        if not app.permission_service.perfil_pode_gerenciar_materias(
            self._perfil(), materia.criado_por_email if materia_id else None
        ):
            self._mensagem("Acesso restrito", "Professores podem criar e administrar as próprias equipes; moderadores podem administrar todas.")
            return
        fields = self._fields((("Nome da equipe", materia.nome), ("Categoria", materia.categoria), ("Descrição", materia.descricao), ("Status", materia.status)))
        def save():
            materia.nome, materia.categoria, materia.descricao, materia.status = [field.text for field in fields]
            if materia_id is None and not materia.criado_por_email:
                materia.criado_por_email = self._email().strip().casefold()
            self._salvar(lambda: self._service.salvar_materia(materia), popup, self.mostrar_equipes if materia_id is None else partial(self.abrir_equipe, materia.id, "info"))
        popup = self._popup("Criar equipe" if materia_id is None else "Configurar equipe", fields, save)
    def editar_publicacao(self, materia_id, post_id, tipo_inicial=None):
        is_new = post_id is None
        if not is_new and not self.exigir_edicao(materia_id):
            return
        if is_new and not self.pode_editar and tipo_inicial != "pergunta":
            self._mensagem("Acesso restrito", "Alunos podem iniciar perguntas; aulas e avisos são publicados pelo professor.")
            return
        materia = self._service.obter(materia_id)
        post = next((p for p in materia.publicacoes if p.id == post_id), Publicacao(autor=self._autor(), tipo=tipo_inicial or "aviso"))
        fields = self._fields((("Título", post.titulo), ("Mensagem", post.mensagem)))
        tipo = None
        status = None
        if self.pode_editar:
            type_labels = {"aula": "Aula", "aviso": "Aviso", "recado": "Recado", "conteudo": "Material", "tarefa": "Atividade"}
            selected_type = post.tipo if post.tipo in type_labels else (tipo_inicial if tipo_inicial in type_labels else "aviso")
            fields.append(self._text("Tipo de publicação", 22, True, color=(.84, .91, 1, 1), size="12sp"))
            tipo = Spinner(text=type_labels[selected_type], values=tuple(type_labels.values()), size_hint_y=None, height=dp(42))
            fields.append(tipo)
            fields.append(self._text("Visibilidade", 22, True, color=(.84, .91, 1, 1), size="12sp"))
            status = Spinner(text="Rascunho" if post.status == "rascunho" else "Publicado", values=("Publicado", "Rascunho"), size_hint_y=None, height=dp(42))
            fields.append(status)

        attachment_checks = {}
        if self.pode_editar and materia.arquivos:
            title = Label(text="Anexar arquivos da turma", size_hint_y=None, height=dp(28), color=(.88, .93, 1, 1), bold=True, halign="left")
            title.bind(width=lambda item, width: setattr(item, "text_size", (width, None)))
            fields.append(title)
            for shared_file in materia.arquivos:
                row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
                check = CheckBox(active=shared_file.id in post.arquivos_ids, size_hint_x=None, width=dp(34))
                row.add_widget(check)
                row.add_widget(self._text(f"{shared_file.nome}  ·  {self._tamanho(shared_file.tamanho)}", 30, color=(.84, .90, .99, 1), size="12sp"))
                attachment_checks[shared_file.id] = check
                fields.append(row)
        elif self.pode_editar:
            fields.append(self._text("Para anexar materiais, envie-os primeiro pela aba Arquivos.", 38, color=(.72, .82, .97, 1), size="12sp"))

        def save():
            if not self.pode_editar and (not is_new or tipo_inicial != "pergunta"):
                self._mensagem("Acesso restrito", "Você não tem permissão para publicar esse conteúdo.")
                return
            post.titulo, post.mensagem = fields[0].text, fields[1].text
            if tipo is not None:
                type_codes = {label.casefold(): value for value, label in type_labels.items()}
                type_codes.update({"lesson": "aula", "announcement": "aviso", "message": "recado", "assignment": "tarefa"})
                post.tipo = type_codes.get(tipo.text.casefold(), selected_type)
            elif is_new:
                post.tipo = "pergunta"
            post.autor = post.autor or self._autor()
            post.status = "rascunho" if status is not None and status.text.casefold() in {"rascunho", "draft"} else "publicado"
            if attachment_checks:
                post.arquivos_ids = [file_id for file_id, check in attachment_checks.items() if check.active]
            self._salvar(lambda: self._service.salvar_publicacao(materia_id, post), popup, partial(self.abrir_equipe, materia_id, "feed"))
        dialog_title = "Publicar aula" if is_new and tipo_inicial == "aula" else "Fazer uma pergunta" if is_new and tipo_inicial == "pergunta" else "Novo aviso" if is_new else "Editar publicação"
        popup = self._popup(dialog_title, fields, save)
    def comentar_publicacao(self, materia_id, post_id):
        field = CampoTexto(
            hint_text="Escreva sua resposta…",
            multiline=True,
            size_hint_y=None,
            height=dp(144),
            padding=(dp(14), dp(14)),
            font_size="14sp",
        )
        field.form_label = "Sua resposta"
        field.form_helper_text = "Mantenha a conversa respeitosa e relacionada à publicação."
        def save(): self._salvar(lambda: self._service.comentar_publicacao(materia_id, post_id, Comentario(autor=self._autor(), mensagem=field.text)), popup, partial(self.abrir_equipe, materia_id, "feed"))
        popup = self._popup("Responder publicação", [field], save)
    def editar_trabalho(self, materia_id, trabalho_id):
        if not self.exigir_edicao(materia_id): return
        materia = self._service.obter(materia_id); trabalho = next((t for t in materia.trabalhos if t.id == trabalho_id), Trabalho(criado_por=self._autor())); fields = self._fields((("Título", trabalho.titulo), ("Descrição", trabalho.descricao), ("Prazo (ex.: 30/08/2026)", trabalho.prazo), ("Categoria", trabalho.categoria), ("Status", trabalho.status), ("Anexos (nomes separados por vírgula)", ", ".join(trabalho.anexos))))
        def save():
            trabalho.titulo, trabalho.descricao, trabalho.prazo, trabalho.categoria, trabalho.status = [field.text for field in fields[:5]]
            trabalho.anexos = [name.strip() for name in fields[5].text.split(",") if name.strip()]
            self._salvar(lambda: self._service.salvar_trabalho(materia_id, trabalho), popup, partial(self.abrir_equipe, materia_id, "trabalhos"))
        popup = self._popup("Novo trabalho" if trabalho_id is None else "Editar trabalho", fields, save)
    def editar_topico(self, materia_id, topico_id):
        if not self.exigir_edicao(materia_id): return
        materia = self._service.obter(materia_id); is_new = topico_id is None; topico = next((t for t in materia.topicos if t.id == topico_id), Topico()); fields = self._fields((("Título do capítulo", topico.titulo), ("Descrição", topico.descricao), ("Status", topico.status)))
        def save():
            topico.titulo, topico.descricao, topico.status = [field.text for field in fields]
            def completed():
                self.abrir_equipe(materia_id, self.secao)
                if is_new: self.editar_conteudo(materia_id, topico.id, None)
            self._salvar(lambda: self._service.salvar_topico(materia_id, topico), popup, completed)
        popup = self._popup("Novo capítulo" if topico_id is None else "Editar capítulo", fields, save)
    def editar_conteudo(self, materia_id, topico_id, conteudo_id):
        if not self.exigir_edicao(materia_id): return
        topico = next(t for t in self._service.obter(materia_id).topicos if t.id == topico_id); content = next((c for c in topico.conteudos if c.id == conteudo_id), Conteudo(categoria=self.secao if self.secao in {"teorico", "testes"} else "teorico")); fields = self._fields((("Título", content.titulo), ("Descrição", content.descricao), ("Texto do capítulo", content.corpo), ("Status", content.status)))
        tipo = Spinner(text=content.categoria, values=("teorico", "testes"), size_hint_y=None, height=dp(38)); fields.insert(3, tipo)
        def save():
            content.titulo, content.descricao, content.corpo, content.categoria, content.status = fields[0].text, fields[1].text, fields[2].text, tipo.text, fields[4].text; self._salvar(lambda: self._service.salvar_conteudo(materia_id, topico_id, content), popup, partial(self.abrir_equipe, materia_id, self.secao))
        popup = self._popup("Adicionar conteúdo" if conteudo_id is None else "Editar conteúdo", fields, save)

    # Arquivos, entregas e remoções
    def selecionar_arquivo(self, materia_id):
        if not self.exigir_edicao(materia_id): return
        chooser = FileChooserListView(path=str(Path.home()), multiselect=False); box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8)); box.add_widget(chooser); popup = Popup(title="Enviar arquivo para a equipe", content=box, size_hint=(.8, .8)); box.add_widget(self._button("Enviar arquivo selecionado", lambda: self._enviar(materia_id, chooser, popup))); popup.open()
    def _enviar(self, materia_id, chooser, popup):
        if not chooser.selection: self._mensagem("Seleção necessária", "Escolha um arquivo para enviar."); return
        try: self._service.adicionar_arquivo_local(materia_id, chooser.selection[0], self._autor()); popup.dismiss(); self.abrir_equipe(materia_id, "arquivos")
        except (OSError, ValueError) as error: self._mensagem("Não foi possível enviar", str(error))
    def abrir_arquivo(self, caminho):
        try:
            if not Path(caminho).is_file(): raise FileNotFoundError("O arquivo local não está mais disponível.")
            os.startfile(caminho)
        except (OSError, FileNotFoundError) as error: self._mensagem("Não foi possível abrir", str(error))
    def entregar_trabalho(self, materia_id, trabalho_id):
        try: self._service.entregar_trabalho(materia_id, trabalho_id, self._email()); self.abrir_equipe(materia_id, "trabalhos")
        except (KeyError, ValueError) as error: self._mensagem("Não foi possível entregar", str(error))
    def _confirm(self, text, action):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10)); box.add_widget(Label(text=text, color=(.1, .1, .1, 1))); popup = Popup(title="Confirmar ação", content=box, size_hint=(.55, .3)); box.add_widget(self._button("Confirmar exclusão", lambda: (action(), popup.dismiss()), True)); popup.open()
    def confirmar_exclusao_materia(self, ident):
        materia = self._service.obter(ident)
        if not App.get_running_app().permission_service.perfil_pode_gerenciar_materias(
            self._perfil(), materia.criado_por_email
        ):
            self._mensagem("Acesso restrito", "Professores podem remover apenas equipes próprias.")
            return
        self._confirm("Excluir esta equipe e todos os seus dados?", lambda: self._excluir_materia(ident))

    def _excluir_materia(self, ident):
        materia = self._service.obter(ident)
        if not App.get_running_app().permission_service.perfil_pode_gerenciar_materias(
            self._perfil(), materia.criado_por_email
        ):
            return
        self._service.excluir_materia(ident)
        self.mostrar_equipes()
    def confirmar_exclusao_publicacao(self, mid, ident):
        if not self.exigir_edicao(mid): return
        self._confirm("Excluir esta publicação?", lambda: (self._service.excluir_publicacao(mid, ident), self.abrir_equipe(mid, "feed")))
    def confirmar_exclusao_arquivo(self, mid, ident):
        if not self.exigir_edicao(mid): return
        self._confirm("Remover este arquivo compartilhado?", lambda: (self._service.excluir_arquivo(mid, ident), self.abrir_equipe(mid, "arquivos")))
    def confirmar_exclusao_trabalho(self, mid, ident):
        if not self.exigir_edicao(mid): return
        self._confirm("Excluir este trabalho?", lambda: (self._service.excluir_trabalho(mid, ident), self.abrir_equipe(mid, "trabalhos")))
    def _fields(self, values):
        result = []
        for title, value in values:
            multi = title in {"Descrição", "Mensagem", "Texto do capítulo"}
            height = 52 if not multi else 252 if title == "Texto do capítulo" else 144 if title == "Mensagem" else 120
            hints = {
                "Descrição": "Dê um pouco de contexto…",
                "Mensagem": "Escreva sua mensagem para a turma…",
                "Texto do capítulo": "Desenvolva o conteúdo da aula…",
            }
            helpers = {
                "Descrição": "Uma descrição breve ajuda todos a entender o propósito.",
                "Mensagem": "Você pode usar mais de um parágrafo.",
                "Texto do capítulo": "Organize a explicação em parágrafos claros.",
            }
            field = CampoTexto(text=value or "", hint_text=hints.get(title, f"Digite {title.casefold()}…"),
                               multiline=multi, size_hint_y=None, height=dp(height),
                               padding=(dp(15), dp(13)), font_size="14sp", appearance="light")
            field.form_label = title
            field.form_helper_text = helpers.get(title, "")
            result.append(field)
        return result

    def _estilizar_campo_auxiliar(self, widget):
        if isinstance(widget, Spinner):
            widget.background_normal = ""
            widget.background_down = ""
            widget.background_color = (.94, .97, 1, 1)
            widget.color = (.12, .23, .38, 1)
            widget.font_size = "13sp"
            widget.size_hint_y = None
            widget.height = max(widget.height, dp(46))
            return
        if isinstance(widget, CheckBox):
            widget.color = (.12, .43, .80, 1)
            return
        if isinstance(widget, Label):
            widget.color = (.18, .29, .43, 1)
            widget.halign = "left"
            widget.valign = "middle"
            widget.bind(width=lambda item, width: setattr(item, "text_size", (max(1, width), None)))
            return
        for child in getattr(widget, "children", ()):
            self._estilizar_campo_auxiliar(child)

    def _popup(self, title, fields, save):
        box = BoxLayout(orientation="vertical", padding=(dp(22), dp(16)), spacing=dp(12))
        with box.canvas.before:
            Color(.02, .12, .28, .10)
            popup_shadow = RoundedRectangle(pos=(box.x + dp(3), box.y - dp(4)), size=box.size, radius=[dp(20)])
            Color(.98, .99, 1, 1)
            popup_background = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(20)])
            Color(.83, .90, .97, 1)
            popup_outline = Line(rounded_rectangle=(*box.pos, *box.size, dp(20)), width=dp(1))
        def update_box(_item, _value):
            popup_shadow.pos = (box.x + dp(3), box.y - dp(4))
            popup_shadow.size = box.size
            popup_background.pos = box.pos
            popup_background.size = box.size
            popup_outline.rounded_rectangle = (*box.pos, *box.size, dp(20))
        box.bind(pos=update_box, size=update_box)

        description = Label(text="Preencha os campos abaixo. Você poderá revisar antes de salvar.",
                            size_hint_y=None, height=dp(24), color=(.39, .49, .62, 1),
                            font_size="12sp", halign="left", valign="middle")
        description.bind(width=lambda item, width: setattr(item, "text_size", (max(1, width), None)))
        box.add_widget(description)
        form = GridLayout(cols=1, spacing=dp(14), size_hint_y=None, padding=(0, dp(4), dp(3), dp(8)))
        form.bind(minimum_height=form.setter("height"))
        for field in fields:
            if isinstance(field, TextInput):
                field.size_hint_y = None
                if field.height <= 0:
                    field.height = dp(144 if field.multiline else 48)
                field.size_hint_x = 1
                caption = Label(text=getattr(field, "form_label", field.hint_text),
                                size_hint_y=None, height=dp(21), color=(.12, .23, .38, 1),
                                bold=True, font_size="12sp", halign="left", valign="middle")
                caption.bind(width=lambda item, width: setattr(item, "text_size", (max(1, width), None)))
                helper_text = getattr(field, "form_helper_text", "")
                field_group = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
                field_group.bind(minimum_height=field_group.setter("height"))
                field_group.add_widget(caption)
                if helper_text:
                    helper = Label(text=helper_text, size_hint_y=None, height=dp(18),
                                   color=(.45, .55, .67, 1), font_size="10sp",
                                   halign="left", valign="middle")
                    helper.bind(width=lambda item, width: setattr(item, "text_size", (max(1, width), None)))
                    field_group.add_widget(helper)
                field_group.add_widget(field)
                form.add_widget(field_group)
            else:
                self._estilizar_campo_auxiliar(field)
                form.add_widget(field)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(6), scroll_type=["bars", "content"])
        scroll.add_widget(form)
        box.add_widget(scroll)
        footer = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        footer.add_widget(Label())
        cancel_button = self._button("Cancelar", lambda: popup.dismiss(), compact=True, variant="light")
        cancel_button.size_hint_x = None
        cancel_button.width = dp(128)
        action_labels = {
            "publicar aula": "Publicar aula",
            "novo aviso": "Publicar aviso",
            "fazer uma pergunta": "Publicar pergunta",
            "criar equipe": "Criar turma",
            "novo trabalho": "Criar atividade",
            "novo capítulo": "Criar módulo",
            "adicionar conteúdo": "Adicionar conteúdo",
        }
        save_label = action_labels.get(title.casefold(), "Salvar alterações")
        save_button = self._button(save_label, save, compact=True)
        save_button.size_hint_x = None
        save_button.width = dp(156)
        footer.add_widget(cancel_button)
        footer.add_widget(save_button)
        box.add_widget(footer)
        popup_size = (min(dp(880), max(dp(360), Window.width * .82)),
                      min(dp(760), max(dp(480), Window.height * .84)))
        popup = Popup(title=title, content=box, size_hint=(None, None), size=popup_size,
                      title_size="18sp", title_color=(.10, .22, .39, 1),
                      separator_color=(.12, .43, .80, 1), background_color=(.98, .99, 1, 1))
        popup.open(); return popup
    def _salvar(self, action, popup, success):
        try: action(); popup.dismiss(); success()
        except (ValueError, KeyError, OSError, ConnectionError) as error: self._mensagem("Verifique os dados", str(error))
    def _mensagem(self, title, text): Popup(title=title, content=Label(text=text, color=(.1, .1, .1, 1), halign="left", valign="top", text_size=(dp(520), None)), size_hint=(.6, .42)).open()
    @staticmethod
    def _data(value): return value[:10] if value else "sem data"
    @staticmethod
    def _horario(value):
        if not value:
            return ""
        return value.split("T", 1)[1][:5] if "T" in value else value[:5]
    @staticmethod
    def _tamanho(value): return f"{value / 1024:.1f} KB" if value < 1024 * 1024 else f"{value / (1024 * 1024):.1f} MB"


class TelaEquipe(TelaMaterias):
    """Tela dedicada à equipe selecionada; herda os componentes de trabalho."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.modo_equipe = True

    def on_kv_post(self, _base_widget):
        # A equipe é preenchida apenas após a seleção na lista de matérias.
        return

    def mostrar_equipes(self):
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="right", duration=.22)
        manager.current = "materias"
        manager.get_screen("materias").children[0].atualizar()

    def voltar(self):
        self.mostrar_equipes()
