"""Experiência de equipes educacionais para a área de matérias."""
from __future__ import annotations

import os
from functools import partial
from pathlib import Path

from kivy.app import App
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import SlideTransition

from model.componentes import LayoutFundo
from model.materias import Comentario, Conteudo, Materia, Publicacao, Topico, Trabalho


class TeamCard(ButtonBehavior, BoxLayout):
    """Card clicável que abre a equipe ao tocar nele."""

    pass


class TelaMaterias(LayoutFundo):
    """Lista equipes e renderiza uma experiência interna em seções."""

    titulo = StringProperty("Equipes e matérias")
    status_texto = StringProperty("Carregando dados locais...")
    pode_editar = BooleanProperty(False)
    papel = StringProperty("aluno")
    equipe_id = StringProperty("")
    secao = StringProperty("feed")
    modo_equipe = BooleanProperty(False)
    documento_topico_id = StringProperty("")
    documento_conteudo_id = StringProperty("")
    SECOES = (("feed", "▣  Publicações"), ("arquivos", "▤  Arquivos"),
              ("trabalhos", "✓  Trabalhos"), ("teorico", "☰  Conteúdo teórico"),
              ("testes", "📝  Provas e testes"), ("info", "ⓘ  Informações"))

    def on_kv_post(self, _base_widget): self.atualizar()
    @property
    def _service(self): return App.get_running_app().materias_service
    def _perfil(self): return App.get_running_app().session_manager.user or {}
    def _autor(self):
        profile = self._perfil(); return profile.get("name") or profile.get("email") or "Usuário local"
    def _email(self): return self._perfil().get("email") or ""

    def atualizar(self):
        permissions = App.get_running_app().permission_service
        self.papel = permissions.papel_do_perfil(self._perfil()).value
        self.pode_editar = permissions.perfil_pode_editar_materias(self._perfil())
        self.mostrar_equipes()

    def voltar(self):
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="right", duration=.25); manager.current = "principal"

    def _clear(self):
        self.ids.conteudo.clear_widgets(); return self.ids.conteudo
    def _button(self, text, action, danger=False, compact=False):
        button = Button(text=text, size_hint_y=None, height=dp(31 if compact else 38), background_normal="",
            background_color=(.73, .18, .20, 1) if danger else (.06, .34, .72, 1), color=(1, 1, 1, 1), font_size="13sp")
        button.bind(on_release=lambda _instance: action()); return button
    def _text(self, value, height=28, bold=False, color=(.91, .95, 1, 1), size="14sp"):
        # A maior parte dos textos antigos usava tinta escura sobre o fundo claro.
        # Converte tons escuros para a paleta clara desta experiência de equipes.
        if color[0] < .3 and color[1] < .4 and color[2] < .55:
            color = (.87, .92, .99, 1)
        label = Label(text=value, size_hint_y=None, height=dp(height), color=color, bold=bold, font_size=size, halign="left", valign="middle")
        label.bind(width=lambda item, width: setattr(item, "text_size", (width, None))); return label
    def _empty(self, value): return Label(text=value, color=(.67, .75, .89, 1), halign="center", valign="middle", text_size=(dp(720), None))
    def _card(self, height):
        card = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(height), padding=dp(12), spacing=dp(5))
        with card.canvas.before:
            Color(.125, .125, .14, 1)
            background = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
        card.bind(pos=lambda item, value: setattr(background, "pos", value), size=lambda item, value: setattr(background, "size", value))
        return card

    def _team_card(self, height, action):
        card = TeamCard(orientation="vertical", size_hint_y=None, height=dp(height), padding=dp(12), spacing=dp(5))
        with card.canvas.before:
            Color(.125, .125, .14, 1)
            background = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
        card.bind(pos=lambda item, value: setattr(background, "pos", value), size=lambda item, value: setattr(background, "size", value))
        card.bind(on_release=lambda *_args: action())
        return card
    def _center(self, panel, widget):
        """Mantém o feed em uma coluna de leitura, como uma conversa de equipe."""
        row = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=widget.height)
        widget.size_hint_x = .68
        row.add_widget(widget); panel.add_widget(row)

    # Lista de equipes/matérias
    def mostrar_equipes(self):
        self.equipe_id = ""; self.titulo = "Equipes e matérias"
        materias = self._service.listar(); area = self._clear()
        area.cols = 3
        self.status_texto = f"{len(materias)} equipe(s) local(is)  •  papel: {self.papel}"
        if not materias:
            area.cols = 1
            area.add_widget(self._empty("Nenhuma equipe criada ainda.\nProfessores e moderadores podem criar a primeira matéria.")); return
        for materia in materias:
            card = self._team_card(172, partial(self.abrir_equipe, materia.id))
            team_header = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(10))
            initials = "".join(word[0] for word in materia.nome.split()[:2]).upper() or "PM"
            badge = Button(text=initials, disabled=True, size_hint_x=None, width=dp(52), background_normal="", background_color=(.06, .42, .82, 1), color=(1, 1, 1, 1), font_size="18sp")
            team_header.add_widget(badge)
            labels = BoxLayout(orientation="vertical", spacing=dp(1))
            labels.add_widget(self._text(materia.nome, 28, True, size="16sp"))
            labels.add_widget(self._text(materia.categoria, 18, color=(.48, .66, .94, 1), size="12sp"))
            team_header.add_widget(labels); card.add_widget(team_header)
            card.add_widget(self._text(f"{materia.status}  •  {len(materia.topicos)} capítulos  •  {len(materia.publicacoes)} posts", 22, color=(.64, .72, .86, 1), size="12sp"))
            card.add_widget(self._text(materia.descricao or "Equipe sem descrição.", 33, color=(.72, .78, .89, 1), size="12sp"))
            if self.pode_editar:
                actions = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
                actions.add_widget(self._button("Editar", partial(self.editar_materia, materia.id), compact=True))
                actions.add_widget(self._button("Excluir", partial(self.confirmar_exclusao_materia, materia.id), True, True))
                card.add_widget(actions)
            area.add_widget(card)

    # Navegação interna da equipe
    def abrir_equipe(self, materia_id, secao="feed"):
        if secao == "pratico":
            secao = "testes"
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
        self.status_texto = f"Equipe • {materia.categoria} • {materia.status} • dados locais"
        area = self._clear(); area.cols = 1
        # A faixa contextual reproduz a organização de canal da referência: equipe,
        # canal e duas abas principais; a navegação detalhada permanece à esquerda.
        header = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10), padding=(dp(8), 0))
        with header.canvas.before:
            Color(.075, .075, .085, 1)
            header_background = RoundedRectangle(pos=header.pos, size=header.size, radius=[dp(6)])
        header.bind(pos=lambda item, value: setattr(header_background, "pos", value), size=lambda item, value: setattr(header_background, "size", value))
        header.add_widget(self._button("‹  Todas as equipes", self.mostrar_equipes, compact=True))
        emblem = Button(text="".join(word[0] for word in materia.nome.split()[:2]).upper() or "PM", disabled=True, size_hint_x=None, width=dp(34), background_normal="", background_color=(.06, .42, .82, 1), color=(1, 1, 1, 1))
        header.add_widget(emblem); header.add_widget(self._text("Geral", 35, True, size="17sp"))
        for key, title in (("feed", "Postagens"), ("arquivos", "Compartilhado")):
            selected = key == self.secao
            tab = Button(text=title, size_hint_x=None, width=dp(120), background_normal="", background_color=(.075, .075, .085, 1), color=(.47, .70, 1, 1) if selected else (.82, .86, .93, 1), font_size="13sp")
            tab.bind(on_release=lambda _item, section=key: self.abrir_equipe(materia_id, section)); header.add_widget(tab)
        header.add_widget(Label()); area.add_widget(header)
        shell = BoxLayout(size_hint_y=None, height=dp(548), spacing=dp(12)); nav = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(330), spacing=dp(4), padding=dp(10))
        with nav.canvas.before:
            Color(.055, .09, .15, 1)
            nav_background = RoundedRectangle(pos=nav.pos, size=nav.size, radius=[dp(12)])
        nav.bind(pos=lambda item, value: setattr(nav_background, "pos", value), size=lambda item, value: setattr(nav_background, "size", value))
        side_badge = Button(text="".join(word[0] for word in materia.nome.split()[:2]).upper() or "PM", disabled=True, size_hint_y=None, height=dp(64), background_normal="", background_color=(.06, .42, .82, 1), color=(1, 1, 1, 1), font_size="22sp")
        nav.add_widget(side_badge); nav.add_widget(self._text(materia.nome.upper(), 38, True, size="15sp"))
        nav.add_widget(self._text("ESPAÇOS DA EQUIPE", 22, True, color=(.48, .62, .86, 1), size="11sp"))
        for key, name in self.SECOES:
            selected = key == self.secao
            item = Button(text="   " + name.split("  ")[-1], size_hint_y=None, height=dp(35), background_normal="", background_color=(.16, .16, .18, 1) if selected else (.075, .075, .085, 1), color=(1, 1, 1, 1), halign="left", font_size="13sp")
            item.bind(on_release=lambda _item, section=key: self.abrir_equipe(materia_id, section)); nav.add_widget(item)
        nav.add_widget(self._text("CANAIS", 30, True, color=(.48, .62, .86, 1), size="11sp")); nav.add_widget(self._text("   #  Geral", 28, color=(.9, .93, 1, 1), size="13sp"))
        nav.add_widget(Label()); nav.add_widget(self._text(f"Papel atual: {self.papel}", 28, color=(.60, .70, .87, 1), size="12sp"))
        shell.add_widget(nav)
        panel_scroll = ScrollView(do_scroll_x=False, bar_width=dp(7))
        panel = GridLayout(cols=1, spacing=dp(8), padding=dp(8), size_hint_y=None)
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
        # Feed central: publicação primeiro, conversa em seguida, igual à área de canal.
        composer = None
        if self.pode_editar:
            composer = self._card(118)
            composer.add_widget(self._text(self._autor().upper(), 20, True, size="12sp"))
            composer.add_widget(self._text("Adicionar um assunto", 25, color=(.65, .73, .88, 1), size="15sp"))
            composer.add_widget(self._text("Escreva um aviso, conteúdo ou recado para a equipe.", 24, color=(.50, .60, .75, 1), size="12sp"))
            line = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8)); line.add_widget(self._text("☺   ⌕   +", 24, color=(.70, .78, .92, 1))); line.add_widget(self._button("Postar", partial(self.editar_publicacao, materia.id, None), compact=True)); composer.add_widget(line)
        if not materia.publicacoes:
            panel.add_widget(self._empty(" "))
            panel.add_widget(self._empty("O mural desta equipe está vazio.\nAs publicações aparecerão nesta conversa."))
            if composer: self._center(panel, composer)
            return
        for post in reversed(materia.publicacoes):
            card = self._card(175 + 25 * min(2, len(post.comentarios)))
            author = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
            avatar = Button(text=(post.autor[:2] or "PM").upper(), disabled=True, size_hint_x=None, width=dp(30), background_normal="", background_color=(.31, .43, .77, 1), color=(1, 1, 1, 1), font_size="11sp")
            author.add_widget(avatar); author.add_widget(self._text(post.autor.upper(), 28, True, size="12sp")); author.add_widget(self._text(self._data(post.criado_em), 28, color=(.54, .62, .74, 1), size="11sp")); author.add_widget(Label()); author.add_widget(self._text(post.tipo.upper(), 28, True, color=(.43, .65, 1, 1), size="10sp")); card.add_widget(author)
            card.add_widget(self._text(post.titulo, 30, True, size="18sp"))
            card.add_widget(self._text(post.mensagem, 56, color=(.89, .92, .97, 1), size="13sp"))
            if post.anexos: card.add_widget(self._text("⌕  " + "   ".join(post.anexos), 20, color=(.43, .65, 1, 1), size="12sp"))
            for comment in post.comentarios[-2:]: card.add_widget(self._text(f"↳ {comment.autor}: {comment.mensagem}", 22, color=(.22, .32, .45, 1), size="12sp"))
            actions = BoxLayout(size_hint_y=None, height=dp(29), spacing=dp(6)); actions.add_widget(self._button("Responder", partial(self.comentar_publicacao, materia.id, post.id), compact=True))
            if self.pode_editar:
                actions.add_widget(self._button("Editar", partial(self.editar_publicacao, materia.id, post.id), compact=True))
                actions.add_widget(self._button("Excluir", partial(self.confirmar_exclusao_publicacao, materia.id, post.id), True, True))
            card.add_widget(actions); self._center(panel, card)
        if composer: self._center(panel, composer)

    def _render_arquivos(self, materia, panel):
        self._toolbar(panel, ("+ Enviar arquivo", partial(self.selecionar_arquivo, materia.id)))
        if not materia.arquivos: 
            # Widget vazio para dar espaço ao botão de envio de arquivo no topo do painel.
            panel.add_widget(self._empty(" "));
            panel.add_widget(self._empty("Nenhum arquivo compartilhado nesta equipe.")); 
            return
        for arquivo in materia.arquivos:
            card = self._card(82); card.add_widget(self._text(f"▤  {arquivo.nome}", 26, True, size="16sp"))
            card.add_widget(self._text(f"{arquivo.tipo} • {self._tamanho(arquivo.tamanho)} • enviado por {arquivo.autor} • {self._data(arquivo.criado_em)}", 20, color=(.24, .35, .48, 1), size="12sp"))
            actions = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6)); actions.add_widget(self._button("Abrir / baixar", partial(self.abrir_arquivo, arquivo.caminho_local), compact=True))
            if self.pode_editar: actions.add_widget(self._button("Remover", partial(self.confirmar_exclusao_arquivo, materia.id, arquivo.id), True, True))
            card.add_widget(actions); panel.add_widget(card)

    def _render_trabalhos(self, materia, panel):
        self._toolbar(panel, ("+ Novo trabalho", partial(self.editar_trabalho, materia.id, None)))
        panel.add_widget(self._empty(" "))
        if not materia.trabalhos: panel.add_widget(self._empty("Nenhum trabalho delegado nesta equipe.")); return
        for trabalho in materia.trabalhos:
            card = self._card(132); entregue = self._email() in trabalho.entregue_por
            card.add_widget(self._text(f"{trabalho.categoria.upper()}  •  {trabalho.status}", 20, True, color=(.07, .34, .72, 1), size="12sp"))
            card.add_widget(self._text(trabalho.titulo, 26, True, size="16sp")); card.add_widget(self._text(trabalho.descricao or "Sem descrição.", 30))
            card.add_widget(self._text(f"Prazo: {trabalho.prazo}  •  {len(trabalho.entregue_por)} entrega(s)", 20, color=(.25, .35, .48, 1), size="12sp"))
            if trabalho.anexos: card.add_widget(self._text("Anexos: " + ", ".join(trabalho.anexos), 18, color=(.07, .34, .72, 1), size="12sp"))
            actions = BoxLayout(size_hint_y=None, height=dp(29), spacing=dp(6))
            if not self.pode_editar and not entregue: actions.add_widget(self._button("Marcar como entregue", partial(self.entregar_trabalho, materia.id, trabalho.id), compact=True))
            elif entregue: actions.add_widget(self._text("✓ Entregue por você", 24, color=(.08, .48, .29, 1), size="12sp"))
            if self.pode_editar:
                actions.add_widget(self._button("Editar", partial(self.editar_trabalho, materia.id, trabalho.id), compact=True)); actions.add_widget(self._button("Excluir", partial(self.confirmar_exclusao_trabalho, materia.id, trabalho.id), True, True))
            card.add_widget(actions); panel.add_widget(card)

    # Conteúdo no formato de documentação
    def _render_teorico(self, materia, panel): self._render_documentacao(materia, panel, "teorico", "Documentação didática")
    def _render_testes(self, materia, panel): self._render_documentacao(materia, panel, "testes", "Provas e testes")
    def _render_documentacao(self, materia, panel, categoria, heading):
        toolbar = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8)); toolbar.add_widget(self._text(heading, 30, True, size="17sp"))
        if self.pode_editar: toolbar.add_widget(self._button("+ Capítulo", partial(self.editar_topico, materia.id, None), compact=True))
        panel.add_widget(toolbar)
        chapters = [(topico, content) for topico in materia.topicos for content in topico.conteudos if content.categoria == categoria]
        if not chapters: panel.add_widget(self._empty("\n")); panel.add_widget(self._empty("\n")); panel.add_widget(self._empty("Ainda não existem capítulos publicados nesta seção.\nProfessores podem criar tópicos e adicionar conteúdo.")); return
        chosen_topico, chosen = next((item for item in chapters if item[1].id == self.documento_conteudo_id), chapters[0])
        self.documento_topico_id = chosen_topico.id
        self.documento_conteudo_id = chosen.id

        doc = BoxLayout(size_hint_y=None, height=dp(470), spacing=dp(10), padding=dp(10))

        index_panel = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(290), spacing=dp(8), padding=dp(8))
        with index_panel.canvas.before:
            Color(.05, .06, .08, 1)
            index_background = RoundedRectangle(pos=index_panel.pos, size=index_panel.size, radius=[dp(12)])
        index_panel.bind(pos=lambda item, value: setattr(index_background, "pos", value), size=lambda item, value: setattr(index_background, "size", value))
        index_panel.add_widget(self._text("Capítulos", 26, True, size="14sp"))
        index_scroll = ScrollView(do_scroll_x=False, bar_width=dp(6))
        index_list = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        index_list.bind(minimum_height=index_list.setter("height"))
        for topico, content in chapters:
            active = content.id == chosen.id
            button = self._button(f"{topico.titulo}\n{content.titulo}", partial(self.ver_documento, materia.id, content.id), compact=True)
            button.background_color = (.11, .48, .92, 1) if active else (.08, .12, .20, 1)
            index_list.add_widget(button)
        index_scroll.add_widget(index_list)
        index_panel.add_widget(index_scroll)

        body_panel = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        with body_panel.canvas.before:
            Color(.06, .10, .16, 1)
            body_background = RoundedRectangle(pos=body_panel.pos, size=body_panel.size, radius=[dp(12)])
        body_panel.bind(pos=lambda item, value: setattr(body_background, "pos", value), size=lambda item, value: setattr(body_background, "size", value))
        body_panel.add_widget(self._text(chosen.titulo, 32, True, size="21sp"))
        body_panel.add_widget(self._text(f"Capítulo: {chosen_topico.titulo}  •  {chosen.status}", 22, color=(.25, .35, .48, 1), size="12sp"))
        body_panel.add_widget(self._text(chosen.descricao, 30, color=(.74, .82, .92, 1)))
        body_panel.add_widget(self._text(chosen.corpo or "Este capítulo ainda não possui texto. Edite o conteúdo para inserir explicações, exemplos e exercícios.", 180, color=(.91, .95, 1, 1), size="13sp"))
        steps = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(8))
        steps.add_widget(self._button("← Capítulo anterior", lambda: None, compact=True))
        steps.add_widget(self._button("Próximo capítulo →", lambda: None, compact=True))
        body_panel.add_widget(steps)
        if self.pode_editar: body_panel.add_widget(self._button("Editar capítulo", partial(self.editar_conteudo, materia.id, chosen_topico.id, chosen.id), compact=True))

        body_scroll = ScrollView(do_scroll_x=False, bar_width=dp(7))
        body_content = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=dp(0))
        body_content.bind(minimum_height=body_content.setter("height"))
        body_content.add_widget(body_panel)
        body_scroll.add_widget(body_content)

        doc.add_widget(index_panel); doc.add_widget(body_scroll); panel.add_widget(doc)
    def ver_documento(self, materia_id, conteudo_id):
        self.documento_conteudo_id = conteudo_id
        self.abrir_equipe(materia_id, self.secao)

    def _render_info(self, materia, panel):
        self._toolbar(panel, ("Editar informações", partial(self.editar_materia, materia.id)))
        panel.add_widget(self._empty(" "))
        card = self._card(200); card.add_widget(self._text("Sobre esta equipe", 32, True, size="19sp")); card.add_widget(self._text(materia.descricao or "Sem descrição.", 55))
        card.add_widget(self._text(f"Categoria: {materia.categoria}\nStatus: {materia.status}\nCriada em: {self._data(materia.criado_em)}\n{len(materia.topicos)} tópicos, {len(materia.publicacoes)} publicações, {len(materia.arquivos)} arquivos e {len(materia.trabalhos)} trabalhos.", 90, color=(.18, .30, .45, 1))); panel.add_widget(card)

    # Formulários de gestão estilizados e reutilizáveis
    def exigir_edicao(self):
        if self.pode_editar: return True
        self._mensagem("Sem permissão", "Seu perfil é aluno. Professor ou moderador pode administrar esta equipe."); return False
    def editar_materia(self, materia_id=None):
        if not self.exigir_edicao(): return
        materia = self._service.obter(materia_id) if materia_id else Materia(); fields = self._fields((("Nome da equipe", materia.nome), ("Categoria", materia.categoria), ("Descrição", materia.descricao), ("Status", materia.status)))
        def save():
            materia.nome, materia.categoria, materia.descricao, materia.status = [field.text for field in fields]; self._salvar(lambda: self._service.salvar_materia(materia), popup, self.mostrar_equipes if materia_id is None else partial(self.abrir_equipe, materia.id, "info"))
        popup = self._popup("Criar equipe" if materia_id is None else "Configurar equipe", fields, save)
    def editar_publicacao(self, materia_id, post_id):
        if not self.exigir_edicao(): return
        materia = self._service.obter(materia_id); post = next((p for p in materia.publicacoes if p.id == post_id), Publicacao(autor=self._autor())); fields = self._fields((("Título", post.titulo), ("Mensagem", post.mensagem), ("Status", post.status), ("Anexos (nomes separados por vírgula)", ", ".join(post.anexos))))
        tipo = Spinner(text=post.tipo, values=("aviso", "conteudo", "tarefa", "recado"), size_hint_y=None, height=dp(38)); fields.insert(2, tipo)
        def save():
            post.titulo, post.mensagem, post.tipo, post.status = fields[0].text, fields[1].text, tipo.text, fields[3].text or "publicado"
            post.anexos = [name.strip() for name in fields[4].text.split(",") if name.strip()]
            self._salvar(lambda: self._service.salvar_publicacao(materia_id, post), popup, partial(self.abrir_equipe, materia_id, "feed"))
        popup = self._popup("Nova publicação" if post_id is None else "Editar publicação", fields, save)
    def comentar_publicacao(self, materia_id, post_id):
        field = TextInput(hint_text="Escreva uma resposta para a equipe", multiline=True)
        def save(): self._salvar(lambda: self._service.comentar_publicacao(materia_id, post_id, Comentario(autor=self._autor(), mensagem=field.text)), popup, partial(self.abrir_equipe, materia_id, "feed"))
        popup = self._popup("Responder publicação", [field], save)
    def editar_trabalho(self, materia_id, trabalho_id):
        if not self.exigir_edicao(): return
        materia = self._service.obter(materia_id); trabalho = next((t for t in materia.trabalhos if t.id == trabalho_id), Trabalho(criado_por=self._autor())); fields = self._fields((("Título", trabalho.titulo), ("Descrição", trabalho.descricao), ("Prazo (ex.: 30/08/2026)", trabalho.prazo), ("Categoria", trabalho.categoria), ("Status", trabalho.status), ("Anexos (nomes separados por vírgula)", ", ".join(trabalho.anexos))))
        def save():
            trabalho.titulo, trabalho.descricao, trabalho.prazo, trabalho.categoria, trabalho.status = [field.text for field in fields[:5]]
            trabalho.anexos = [name.strip() for name in fields[5].text.split(",") if name.strip()]
            self._salvar(lambda: self._service.salvar_trabalho(materia_id, trabalho), popup, partial(self.abrir_equipe, materia_id, "trabalhos"))
        popup = self._popup("Novo trabalho" if trabalho_id is None else "Editar trabalho", fields, save)
    def editar_topico(self, materia_id, topico_id):
        if not self.exigir_edicao(): return
        materia = self._service.obter(materia_id); is_new = topico_id is None; topico = next((t for t in materia.topicos if t.id == topico_id), Topico()); fields = self._fields((("Título do capítulo", topico.titulo), ("Descrição", topico.descricao), ("Status", topico.status)))
        def save():
            topico.titulo, topico.descricao, topico.status = [field.text for field in fields]
            def completed():
                self.abrir_equipe(materia_id, self.secao)
                if is_new: self.editar_conteudo(materia_id, topico.id, None)
            self._salvar(lambda: self._service.salvar_topico(materia_id, topico), popup, completed)
        popup = self._popup("Novo capítulo" if topico_id is None else "Editar capítulo", fields, save)
    def editar_conteudo(self, materia_id, topico_id, conteudo_id):
        if not self.exigir_edicao(): return
        topico = next(t for t in self._service.obter(materia_id).topicos if t.id == topico_id); content = next((c for c in topico.conteudos if c.id == conteudo_id), Conteudo(categoria=self.secao if self.secao in {"teorico", "testes"} else "teorico")); fields = self._fields((("Título", content.titulo), ("Descrição", content.descricao), ("Texto do capítulo", content.corpo), ("Status", content.status)))
        tipo = Spinner(text=content.categoria, values=("teorico", "testes"), size_hint_y=None, height=dp(38)); fields.insert(3, tipo)
        def save():
            content.titulo, content.descricao, content.corpo, content.categoria, content.status = fields[0].text, fields[1].text, fields[2].text, tipo.text, fields[4].text; self._salvar(lambda: self._service.salvar_conteudo(materia_id, topico_id, content), popup, partial(self.abrir_equipe, materia_id, self.secao))
        popup = self._popup("Adicionar conteúdo" if conteudo_id is None else "Editar conteúdo", fields, save)

    # Arquivos, entregas e remoções
    def selecionar_arquivo(self, materia_id):
        if not self.exigir_edicao(): return
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
    def confirmar_exclusao_materia(self, ident): self._confirm("Excluir esta equipe e todos os seus dados?", lambda: (self._service.excluir_materia(ident), self.mostrar_equipes()))
    def confirmar_exclusao_publicacao(self, mid, ident): self._confirm("Excluir esta publicação?", lambda: (self._service.excluir_publicacao(mid, ident), self.abrir_equipe(mid, "feed")))
    def confirmar_exclusao_arquivo(self, mid, ident): self._confirm("Remover este arquivo compartilhado?", lambda: (self._service.excluir_arquivo(mid, ident), self.abrir_equipe(mid, "arquivos")))
    def confirmar_exclusao_trabalho(self, mid, ident): self._confirm("Excluir este trabalho?", lambda: (self._service.excluir_trabalho(mid, ident), self.abrir_equipe(mid, "trabalhos")))
    def _fields(self, values):
        result = []
        for title, value in values:
            multi = title in {"Descrição", "Mensagem", "Texto do capítulo"}; result.append(TextInput(text=value or "", hint_text=title, multiline=multi, size_hint_y=None, height=dp(96 if multi else 38)))
        return result
    def _popup(self, title, fields, save):
        box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        with box.canvas.before:
            Color(.065, .105, .17, 1)
            popup_background = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(12)])
        box.bind(pos=lambda item, value: setattr(popup_background, "pos", value), size=lambda item, value: setattr(popup_background, "size", value))
        for field in fields:
            if isinstance(field, TextInput):
                field.foreground_color = (.94, .97, 1, 1); field.hint_text_color = (.54, .66, .85, 1)
                field.background_normal = ""; field.background_active = ""; field.background_color = (.12, .18, .29, 1)
            box.add_widget(field)
        popup = Popup(title=title, content=box, size_hint=(.72, .8), title_color=(.90, .95, 1, 1), separator_color=(.11, .42, .82, 1))
        box.add_widget(self._button("Salvar alterações", save)); popup.open(); return popup
    def _salvar(self, action, popup, success):
        try: action(); popup.dismiss(); success()
        except (ValueError, KeyError, OSError) as error: self._mensagem("Verifique os dados", str(error))
    def _mensagem(self, title, text): Popup(title=title, content=Label(text=text, color=(.1, .1, .1, 1), halign="left", valign="top", text_size=(dp(520), None)), size_hint=(.6, .42)).open()
    @staticmethod
    def _data(value): return value[:10] if value else "sem data"
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
