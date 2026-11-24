"""Componentes HUD modernos e palcos animados passo a passo para os laboratórios de Redes I."""
from __future__ import annotations

import math
from functools import partial

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from model.componentes import BotaoAcao, IconeUI
from model.tema_praticas import paleta_praticas, registrar_cor_texto, registrar_fundo


def cor_contraste(bg_color) -> tuple[float, float, float, float]:
    """Escolhe texto escuro ou claro conforme a luminância do fundo."""
    lum = 0.2126 * bg_color[0] + 0.7152 * bg_color[1] + 0.0722 * bg_color[2]
    return (0.06, 0.10, 0.17, 1) if lum > 0.52 else (1, 1, 1, 1)


def _bind_rounded_bg(widget: Widget, bg_rect: RoundedRectangle, border_line: Line | None, radius: float):
    """Sincroniza fundo e borda arredondada quando pos/size do widget mudam."""
    def _sync(w, _val, s=bg_rect, b=border_line, r=radius):
        s.pos = w.pos
        s.size = w.size
        if b is not None:
            b.rounded_rectangle = (w.x, w.y, w.width, w.height, r)

    widget.bind(pos=_sync, size=_sync)


def criar_label(
    text: str,
    *,
    size: str = "12sp",
    color=None,
    bold: bool = False,
    height=dp(26),
    valign: str = "middle",
    halign: str = "left",
    auto_height: bool = False,
    markup: bool = False,
    role: str | None = None,
) -> Label:
    """Cria um Label padronizado com wrapping seguro e suporte a tema claro/escuro."""
    colors = paleta_praticas()
    cor_final = color if color is not None else colors[role or "text"]
    item = Label(
        text=text,
        size_hint_y=None,
        height=height,
        color=cor_final,
        bold=bold,
        font_size=size,
        halign=halign,
        valign=valign,
        markup=markup,
    )
    registrar_cor_texto(item, cor_final, role=role)
    item.bind(width=lambda widget, value: setattr(widget, "text_size", (max(1, value), None)))
    if auto_height:
        item.bind(
            texture_size=lambda widget, val, min_h=height: setattr(
                widget, "height", max(min_h, val[1] + dp(8))
            )
        )
    return item


def criar_pill(
    texto: str,
    bg_color,
    text_color,
    icone: str | None = None,
    height=dp(24),
    fixed_width=None,
    font_size: str = "10sp",
) -> BoxLayout:
    """Cápsula compacta de status ou tag."""
    pill = BoxLayout(
        orientation="horizontal",
        size_hint=(None, None),
        height=height,
        spacing=dp(4),
        padding=(dp(8), dp(2)),
    )
    with pill.canvas.before:
        Color(*bg_color)
        bg = RoundedRectangle(pos=pill.pos, size=pill.size, radius=[height / 2])
    _bind_rounded_bg(pill, bg, None, height / 2)

    if icone:
        pill.add_widget(
            IconeUI(
                nome=icone,
                size_hint=(None, None),
                size=(dp(14), height - dp(4)),
                font_size=dp(13),
                color=text_color,
                pos_hint={"center_y": 0.5},
            )
        )

    lbl = Label(
        text=texto,
        color=text_color,
        bold=True,
        font_size=font_size,
        size_hint=(None, None),
        height=height - dp(4),
        pos_hint={"center_y": 0.5},
    )
    if fixed_width is not None:
        pill.width = fixed_width
        lbl.size_hint_x = 1
        lbl.halign = "center"
        lbl.valign = "middle"
        lbl.bind(size=lambda item, val: setattr(item, "text_size", val))
    else:
        def _on_tex(_inst, val, p=pill, l=lbl, has_ic=bool(icone)):
            l.width = max(dp(8), val[0])
            ic_w = dp(18) if has_ic else dp(0)
            p.width = val[0] + dp(18) + ic_w

        lbl.bind(texture_size=_on_tex)
        ic_w = dp(18) if icone else dp(0)
        lbl.width = max(dp(12), len(texto) * dp(6.6))
        pill.width = lbl.width + dp(18) + ic_w

    pill.add_widget(lbl)
    return pill


def criar_card(*, padding=dp(12), spacing=dp(8), elevated: bool = False) -> GridLayout:
    """Card arredondado padrão com registro de tema."""
    colors = paleta_praticas()
    item = GridLayout(cols=1, padding=padding, spacing=spacing, size_hint_y=None)
    role = "card_elevated" if elevated else "card"
    with item.canvas.before:
        fill = Color(*colors[role])
        bg = RoundedRectangle(pos=item.pos, size=item.size, radius=[dp(12)])
        Color(*colors["border"])
        border = Line(
            rounded_rectangle=(item.x, item.y, item.width, item.height, dp(12)),
            width=dp(1),
        )
    registrar_fundo(item, fill, role)
    _bind_rounded_bg(item, bg, border, dp(12))
    item.bind(minimum_height=item.setter("height"))
    return item


def criar_botao(
    text: str,
    action,
    *,
    variant: str = "primary",
    height=dp(36),
    font_size: str = "11sp",
    icone: str | None = None,
    width=None,
) -> BotaoAcao:
    """Botão padronizado usando BotaoAcao."""
    item = BotaoAcao(
        text=text,
        variant=variant,
        size_hint_y=None,
        height=height,
        bold=True,
        font_size=font_size,
    )
    if width is not None:
        item.size_hint_x = None
        item.width = width
    if icone:
        item.icone = icone
        item.icon_position = "left"
    item.bind(on_release=lambda *_args: action())
    return item


def criar_chip_dado(chave: str, valor: str, cor_role: str = "accent", height=dp(30)) -> BoxLayout:
    """Micro-card Key-Value para substituir textos corridos por telemetria HUD legível."""
    colors = paleta_praticas()
    cor_val = colors.get(cor_role, colors["accent"])
    box = BoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=height,
        padding=(dp(8), dp(4)),
        spacing=dp(6),
    )
    with box.canvas.before:
        fill = Color(*colors["panel"])
        bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(8)])
        Color(*colors["tag_border"])
        bd = Line(rounded_rectangle=(box.x, box.y, box.width, box.height, dp(8)), width=dp(0.9))
    registrar_fundo(box, fill, "panel")
    _bind_rounded_bg(box, bg, bd, dp(8))

    lbl_k = Label(
        text=f"{chave}:",
        font_size="10sp",
        bold=True,
        color=colors["muted"],
        size_hint=(None, 1),
        halign="left",
        valign="middle",
    )
    lbl_k.bind(texture_size=lambda inst, sz: setattr(inst, "width", sz[0] + dp(2)))
    lbl_k.width = max(dp(36), len(chave) * dp(6.2))
    registrar_cor_texto(lbl_k, colors["muted"], "muted")

    lbl_v = Label(
        text=valor,
        font_size="10.5sp",
        bold=True,
        color=cor_val,
        size_hint=(1, 1),
        halign="left",
        valign="middle",
        shorten=True,
        shorten_from="right",
    )
    lbl_v.bind(size=lambda inst, sz: setattr(inst, "text_size", (max(1, sz[0]), sz[1])))
    registrar_cor_texto(lbl_v, cor_val, cor_role)

    box.add_widget(lbl_k)
    box.add_widget(lbl_v)
    return box


def criar_kpi_tile(titulo: str, valor: str, subtitulo: str = "", cor_role: str = "accent", height=dp(64)) -> BoxLayout:
    """Bloco KPI estruturado para barras de telemetria HUD."""
    colors = paleta_praticas()
    cor_val = colors.get(cor_role, colors["accent"])
    tile = BoxLayout(
        orientation="vertical",
        size_hint_y=None,
        height=height,
        padding=(dp(10), dp(6)),
        spacing=dp(2),
    )
    with tile.canvas.before:
        fill = Color(*colors["panel"])
        bg = RoundedRectangle(pos=tile.pos, size=tile.size, radius=[dp(9)])
        Color(*colors["border"])
        bd = Line(rounded_rectangle=(tile.x, tile.y, tile.width, tile.height, dp(9)), width=dp(1))
    registrar_fundo(tile, fill, "panel")
    _bind_rounded_bg(tile, bg, bd, dp(9))

    lbl_t = Label(
        text=titulo.upper(),
        font_size="8.5sp",
        bold=True,
        color=colors["muted"],
        size_hint_y=None,
        height=dp(13),
        halign="left",
        valign="middle",
        shorten=True,
    )
    lbl_t.bind(size=lambda i, sz: setattr(i, "text_size", sz))
    registrar_cor_texto(lbl_t, colors["muted"], "muted")
    tile.add_widget(lbl_t)

    lbl_v = Label(
        text=valor,
        font_size="12sp",
        bold=True,
        color=cor_val,
        size_hint_y=None,
        height=dp(22),
        halign="left",
        valign="middle",
        shorten=True,
        shorten_from="right",
    )
    lbl_v.bind(size=lambda i, sz: setattr(i, "text_size", sz))
    registrar_cor_texto(lbl_v, cor_val, cor_role)
    tile.add_widget(lbl_v)
    tile._lbl_valor = lbl_v

    lbl_s = Label(
        text=subtitulo,
        font_size="9sp",
        color=colors["text_secondary"],
        size_hint_y=None,
        height=dp(14),
        halign="left",
        valign="middle",
        shorten=True,
    )
    lbl_s.bind(size=lambda i, sz: setattr(i, "text_size", sz))
    registrar_cor_texto(lbl_s, colors["text_secondary"], "text_secondary")
    tile.add_widget(lbl_s)
    tile._lbl_sub = lbl_s
    return tile


def _criar_no_topologia(
    stage: RelativeLayout,
    titulo: str,
    sub: str,
    icone: str,
    role: str,
    cx: float,
    cy: float,
    *,
    width=dp(166),
    height=dp(56),
) -> BoxLayout:
    """Cria um nó visual padronizado para diagramas de topologia animada."""
    colors = paleta_praticas()
    card = BoxLayout(
        orientation="vertical",
        size_hint=(None, None),
        size=(width, height),
        pos_hint={"center_x": cx, "center_y": cy},
        padding=(dp(8), dp(5)),
        spacing=dp(2),
    )
    with card.canvas.before:
        fill = Color(*colors["card"])
        bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(10)])
        bd_col = Color(*colors["border"])
        bd = Line(rounded_rectangle=(card.x, card.y, card.width, card.height, dp(10)), width=dp(1.2))
    registrar_fundo(card, fill, "card")
    _bind_rounded_bg(card, bg, bd, dp(10))

    row = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(5))
    row.add_widget(
        IconeUI(
            nome=icone,
            size_hint=(None, None),
            size=(dp(15), dp(15)),
            font_size=dp(14),
            color=colors[role],
            pos_hint={"center_y": 0.5},
        )
    )
    lbl_t = Label(
        text=titulo,
        font_size="9.5sp",
        bold=True,
        color=colors["text"],
        halign="left",
        valign="middle",
        shorten=True,
    )
    lbl_t.bind(size=lambda i, sz: setattr(i, "text_size", sz))
    row.add_widget(lbl_t)
    card.add_widget(row)

    lbl_s = Label(
        text=sub,
        font_size="8.5sp",
        color=colors["muted"],
        halign="left",
        valign="middle",
        shorten=True,
    )
    lbl_s.bind(size=lambda i, sz: setattr(i, "text_size", sz))
    card.add_widget(lbl_s)

    card._bd_col = bd_col
    card._lbl_sub = lbl_s
    card._role = role
    stage.add_widget(card)
    return card


def _criar_pilula_pacote(
    stage: RelativeLayout,
    texto: str,
    icone: str,
    cx: float,
    cy: float,
    *,
    width=dp(106),
) -> BoxLayout:
    """Cria a cápsula animada que representa pacotes trafegando nos diagramas."""
    colors = paleta_praticas()
    cor_init = colors["primary"]
    txt_cor = cor_contraste(cor_init)
    pkt = BoxLayout(
        orientation="horizontal",
        size_hint=(None, None),
        size=(width, dp(26)),
        pos_hint={"center_x": cx, "center_y": cy},
        padding=(dp(8), dp(2)),
        spacing=dp(4),
    )
    with pkt.canvas.before:
        pkt_fill = Color(*cor_init)
        p_bg = RoundedRectangle(pos=pkt.pos, size=pkt.size, radius=[dp(13)])
        Color(1, 1, 1, 0.75)
        p_bd = Line(rounded_rectangle=(pkt.x, pkt.y, pkt.width, pkt.height, dp(13)), width=dp(1.2))
    _bind_rounded_bg(pkt, p_bg, p_bd, dp(13))

    ic_w = IconeUI(
        nome=icone,
        size_hint=(None, None),
        size=(dp(13), dp(13)),
        font_size=dp(12),
        color=txt_cor,
        pos_hint={"center_y": 0.5},
    )
    lbl_pkt = Label(text=texto, font_size="9.5sp", bold=True, color=txt_cor, halign="left", valign="middle")
    pkt.add_widget(ic_w)
    pkt.add_widget(lbl_pkt)
    pkt._fill = pkt_fill
    pkt._icon = ic_w
    pkt._label = lbl_pkt
    stage.add_widget(pkt)
    return pkt


class DrawerDumpBruto(BoxLayout):
    """Painel expansível para manter logs brutos (tcpdump, dig, ping, ip route) acessíveis sem poluir a tela."""

    def __init__(self, titulo: str = "Saída Técnica / Captura Bruta", icone: str = "code-tags", **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=dp(44),
            padding=(dp(10), dp(6)),
            spacing=dp(6),
            **kwargs,
        )
        self._aberto = False
        self._texto_bruto = ""
        colors = paleta_praticas()

        with self.canvas.before:
            self._fill = Color(*colors["panel"])
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(*colors["border"])
            self._border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(10)),
                width=dp(1),
            )
        registrar_fundo(self, self._fill, "panel")
        _bind_rounded_bg(self, self._bg, self._border, dp(10))

        top = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
        top.add_widget(
            IconeUI(
                nome=icone,
                size_hint=(None, None),
                size=(dp(18), dp(24)),
                font_size=dp(16),
                color=colors["accent"],
                pos_hint={"center_y": 0.5},
            )
        )
        lbl_titulo = Label(
            text=titulo,
            font_size="11sp",
            bold=True,
            color=colors["text"],
            halign="left",
            valign="middle",
        )
        lbl_titulo.bind(size=lambda inst, sz: setattr(inst, "text_size", sz))
        registrar_cor_texto(lbl_titulo, colors["text"], "text")
        top.add_widget(lbl_titulo)

        self._badge = criar_pill("Sem dados", colors["tag_bg"], colors["muted"], height=dp(22))
        top.add_widget(self._badge)

        self._btn_toggle = BotaoAcao(
            text="Ver Detalhes",
            variant="secondary",
            size_hint=(None, None),
            size=(dp(128), dp(28)),
            font_size="10sp",
            icone="chevron-down",
        )
        self._btn_toggle.bind(on_release=lambda *_a: self.alternar())
        top.add_widget(self._btn_toggle)
        self.add_widget(top)

        self._body = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=0,
            opacity=0,
            padding=(dp(8), dp(6)),
        )
        with self._body.canvas.before:
            Color(*colors["terminal"])
            term_bg = RoundedRectangle(pos=self._body.pos, size=self._body.size, radius=[dp(8)])
        _bind_rounded_bg(self._body, term_bg, None, dp(8))

        self._scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        self._lbl_dump = Label(
            text="",
            font_size="9.5sp",
            color=(0.78, 0.90, 0.99, 1),
            halign="left",
            valign="top",
            size_hint_y=None,
            height=dp(20),
            padding=(dp(4), dp(4)),
        )
        self._lbl_dump.bind(width=lambda inst, w: setattr(inst, "text_size", (max(1, w - dp(10)), None)))
        self._lbl_dump.bind(texture_size=lambda inst, sz: setattr(inst, "height", max(dp(20), sz[1] + dp(8))))
        self._scroll.add_widget(self._lbl_dump)
        self._body.add_widget(self._scroll)
        self.add_widget(self._body)

    def definir_conteudo(self, texto: str, badge_texto: str | None = None):
        self._texto_bruto = (texto or "").strip()
        self._lbl_dump.text = self._texto_bruto or "(Nenhum log capturado ainda)"
        linhas = len(self._texto_bruto.splitlines()) if self._texto_bruto else 0
        pill_txt = badge_texto or (f"{linhas} linhas" if linhas else "Vazio")
        self._badge.children[0].text = pill_txt
        if self._aberto:
            self._aplicar_estado_aberto(True)

    def alternar(self):
        self._aplicar_estado_aberto(not self._aberto)

    def _aplicar_estado_aberto(self, abrir: bool):
        self._aberto = abrir
        if abrir:
            linhas = max(3, min(14, len(self._texto_bruto.splitlines()) + 1)) if self._texto_bruto else 3
            body_h = min(dp(200), max(dp(64), linhas * dp(15)))
            self._body.height = body_h
            self._body.opacity = 1
            self.height = dp(44) + body_h + dp(6)
            self._btn_toggle.text = "Ocultar Log"
            self._btn_toggle.icone = "chevron-up"
        else:
            self._body.height = 0
            self._body.opacity = 0
            self.height = dp(44)
            self._btn_toggle.text = "Ver Detalhes"
            self._btn_toggle.icone = "chevron-down"


class PlayerPassoAPasso(BoxLayout):
    """Controlador interativo estilo player de vídeo com Play/Pause, Voltar, Seguir, Pular e Timeline."""

    progresso_ratio = NumericProperty(0.0)

    def __init__(self, palco_widget: Widget, intervalo_autoplay: float = 2.6, on_step_change=None, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, spacing=dp(8), **kwargs)
        self.palco = palco_widget
        self.intervalo_autoplay = intervalo_autoplay
        self.on_step_change = on_step_change
        self.passos: list[dict] = []
        self.indice: int = 0
        self.reproduzindo: bool = False
        self._clock_ev = None
        self._step_buttons: list[BotaoAcao] = []

        self.bind(minimum_height=self.setter("height"))
        self.add_widget(self.palco)

        colors = paleta_praticas()

        timeline_card = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(46), spacing=dp(6))
        self._bar_bg = Widget(size_hint_y=None, height=dp(6))
        with self._bar_bg.canvas.before:
            Color(*colors["border"])
            self._bar_track = RoundedRectangle(pos=self._bar_bg.pos, size=self._bar_bg.size, radius=[dp(3)])
            Color(*colors["primary"])
            self._bar_fill = RoundedRectangle(pos=self._bar_bg.pos, size=(0, dp(6)), radius=[dp(3)])
        self._bar_bg.bind(pos=self._sync_progress_bar, size=self._sync_progress_bar)
        self.bind(progresso_ratio=self._sync_progress_bar)
        timeline_card.add_widget(self._bar_bg)

        self._steps_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28), spacing=dp(5))
        timeline_card.add_widget(self._steps_row)
        self.add_widget(timeline_card)

        self._explicacao_card = criar_card(padding=(dp(12), dp(10)), spacing=dp(8), elevated=True)
        head_row = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        self._step_badge = criar_pill("PASSO 1", colors["tag_bg"], colors["accent"], height=dp(22))
        head_row.add_widget(self._step_badge)

        self._lbl_step_titulo = criar_label(
            "Aguardando início",
            size="13sp",
            bold=True,
            color=colors["text"],
            height=dp(24),
            role="text",
        )
        self._lbl_step_titulo.size_hint_x = 1
        head_row.add_widget(self._lbl_step_titulo)
        self._explicacao_card.add_widget(head_row)

        self._lbl_step_resumo = criar_label(
            "",
            size="11.5sp",
            color=colors["text_secondary"],
            height=dp(24),
            auto_height=True,
            valign="top",
            role="text_secondary",
        )
        self._explicacao_card.add_widget(self._lbl_step_resumo)

        self._grid_dados = GridLayout(cols=3, spacing=dp(6), size_hint_y=None)
        self._grid_dados.bind(minimum_height=self._grid_dados.setter("height"))
        self._explicacao_card.add_widget(self._grid_dados)
        self.add_widget(self._explicacao_card)

        controls = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            padding=(dp(8), dp(4)),
            spacing=dp(8),
        )
        with controls.canvas.before:
            ctrl_fill = Color(*colors["panel"])
            ctrl_bg = RoundedRectangle(pos=controls.pos, size=controls.size, radius=[dp(10)])
            Color(*colors["border"])
            ctrl_bd = Line(
                rounded_rectangle=(controls.x, controls.y, controls.width, controls.height, dp(10)),
                width=dp(1),
            )
        registrar_fundo(controls, ctrl_fill, "panel")
        _bind_rounded_bg(controls, ctrl_bg, ctrl_bd, dp(10))

        self._btn_reiniciar = criar_botao(
            "Reiniciar", self.reiniciar, variant="secondary", height=dp(34), font_size="10.5sp", icone="restart", width=dp(118)
        )
        self._btn_voltar = criar_botao(
            "Voltar", self.voltar, variant="secondary", height=dp(34), font_size="10.5sp", icone="skip-previous", width=dp(108)
        )
        self._btn_play = criar_botao(
            "Reproduzir", self.alternar_play, variant="primary", height=dp(34), font_size="10.5sp", icone="play", width=dp(136)
        )
        self._btn_seguir = criar_botao(
            "Seguir", self.seguir, variant="primary", height=dp(34), font_size="10.5sp", icone="skip-next", width=dp(110)
        )
        self._btn_pular = criar_botao(
            "Pular tudo", self.pular, variant="secondary", height=dp(34), font_size="10.5sp", icone="skip-forward", width=dp(124)
        )

        controls.add_widget(self._btn_reiniciar)
        controls.add_widget(self._btn_voltar)
        controls.add_widget(self._btn_play)
        controls.add_widget(self._btn_seguir)
        controls.add_widget(self._btn_pular)
        controls.add_widget(Widget())

        self._pill_contador = criar_pill("Passo 1 / 1", colors["tag_bg"], colors["accent"], height=dp(26))
        self._pill_contador.pos_hint = {"center_y": 0.5}
        controls.add_widget(self._pill_contador)

        self.add_widget(controls)

    def on_parent(self, _widget, parent):
        if parent is None:
            self.parar()

    def _sync_progress_bar(self, *_args):
        self._bar_track.pos = self._bar_bg.pos
        self._bar_track.size = self._bar_bg.size
        self._bar_fill.pos = self._bar_bg.pos
        self._bar_fill.size = (max(dp(6), self._bar_bg.width * self.progresso_ratio), self._bar_bg.height)

    def definir_passos(self, passos: list[dict], *, indice_inicial: int = 0, auto_play: bool = False):
        self.parar()
        self.passos = passos or []
        self._reconstruir_timeline()
        if self.passos:
            idx = max(0, min(indice_inicial, len(self.passos) - 1))
            self.ir_para(idx, animar=True)
            if auto_play and len(self.passos) > 1:
                self.reproduzir()

    def _reconstruir_timeline(self):
        self._steps_row.clear_widgets()
        self._step_buttons.clear()
        for idx, passo in enumerate(self.passos):
            curto = passo.get("curto", f"{idx + 1}")
            btn = BotaoAcao(
                text=curto,
                variant="secondary",
                size_hint=(1, None),
                height=dp(28),
                font_size="9.5sp",
                bold=True,
                padding=(dp(4), dp(4)),
            )
            btn.bind(on_release=partial(self._clique_timeline, idx))
            self._step_buttons.append(btn)
            self._steps_row.add_widget(btn)

    def _clique_timeline(self, idx: int, *_args):
        self.parar()
        self.ir_para(idx, animar=True)

    def ir_para(self, idx: int, animar: bool = True):
        if not self.passos:
            return
        idx = max(0, min(idx, len(self.passos) - 1))
        self.indice = idx
        passo = self.passos[idx]
        colors = paleta_praticas()

        ratio = (idx + 1) / float(len(self.passos))
        Animation.cancel_all(self, "progresso_ratio")
        if animar:
            Animation(progresso_ratio=ratio, d=0.25, t="out_quad").start(self)
        else:
            self.progresso_ratio = ratio

        for i, btn in enumerate(self._step_buttons):
            if i == idx:
                btn.variant = "primary"
            elif i < idx:
                btn.variant = "light"
            else:
                btn.variant = "secondary"

        self._step_badge.children[0].text = passo.get("badge", f"PASSO {idx + 1}/{len(self.passos)}")
        self._lbl_step_titulo.text = passo.get("titulo", "")
        cor_role = passo.get("cor", "text")
        registrar_cor_texto(self._lbl_step_titulo, colors.get(cor_role, colors["text"]), cor_role)
        self._lbl_step_resumo.text = passo.get("resumo", "")

        self._grid_dados.clear_widgets()
        dados = passo.get("dados") or []
        self._grid_dados.cols = 3 if len(dados) >= 3 else max(1, len(dados))
        for chave, valor, role_cor in dados:
            self._grid_dados.add_widget(criar_chip_dado(chave, str(valor), cor_role=role_cor))

        self._pill_contador.children[0].text = f"Passo {idx + 1} / {len(self.passos)}"
        self._btn_voltar.disabled = idx <= 0
        self._btn_voltar.opacity = 0.55 if idx <= 0 else 1.0
        self._btn_seguir.disabled = idx >= len(self.passos) - 1
        self._btn_seguir.opacity = 0.55 if idx >= len(self.passos) - 1 else 1.0
        self._btn_pular.disabled = idx >= len(self.passos) - 1
        self._btn_pular.opacity = 0.55 if idx >= len(self.passos) - 1 else 1.0

        if hasattr(self.palco, "definir_passo"):
            self.palco.definir_passo(idx, passo, animar=animar)
        if callable(self.on_step_change):
            self.on_step_change(idx, passo)

    def voltar(self):
        self.parar()
        if self.indice > 0:
            self.ir_para(self.indice - 1, animar=True)

    def seguir(self):
        self.parar()
        if self.indice < len(self.passos) - 1:
            self.ir_para(self.indice + 1, animar=True)

    def reiniciar(self):
        self.parar()
        self.ir_para(0, animar=True)

    def pular(self):
        self.parar()
        if self.passos:
            self.ir_para(len(self.passos) - 1, animar=True)

    def alternar_play(self):
        if self.reproduzindo:
            self.parar()
        else:
            self.reproduzir()

    def reproduzir(self):
        if not self.passos:
            return
        if self.indice >= len(self.passos) - 1:
            self.ir_para(0, animar=True)
        self.reproduzindo = True
        self._btn_play.text = "Pausar"
        self._btn_play.icone = "pause"
        if self._clock_ev is None:
            self._clock_ev = Clock.schedule_interval(self._avancar_autoplay, self.intervalo_autoplay)

    def parar(self):
        self.reproduzindo = False
        if self._clock_ev is not None:
            self._clock_ev.cancel()
            self._clock_ev = None
        if hasattr(self, "_btn_play"):
            self._btn_play.text = "Reproduzir"
            self._btn_play.icone = "play"

    def _avancar_autoplay(self, _dt):
        if not self.reproduzindo or not self.passos:
            self.parar()
            return False
        if self.indice < len(self.passos) - 1:
            self.ir_para(self.indice + 1, animar=True)
            return True
        self.parar()
        return False


class PalcoAnimadoOSI(RelativeLayout):
    """Diagrama animado mostrando Encapsulamento (PC-A), Travessia Física em Bits e Desencapsulamento (PC-B)."""

    wire_progress = NumericProperty(0.0)
    wave_phase = NumericProperty(0.0)

    CAMADAS = (
        (7, "C7 Aplicação", "success"),
        (6, "C6 Apresentação", "success"),
        (5, "C5 Sessão", "info"),
        (4, "C4 Transporte", "warning"),
        (3, "C3 Rede (IP)", "primary"),
        (2, "C2 Enlace (MAC)", "accent"),
        (1, "C1 Física (Bits)", "danger"),
    )

    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=dp(248), **kwargs)
        self._camada_ativa = 7
        self._lado_ativo = "A"
        self._wave_ev = None
        self._rows_a_colors: dict[int, tuple] = {}
        self._rows_b_colors: dict[int, tuple] = {}

        colors = paleta_praticas()
        with self.canvas.before:
            self._stage_fill = Color(*colors["shell"])
            self._stage_bg = RoundedRectangle(pos=(0, 0), size=self.size, radius=[dp(12)])
            Color(*colors["border"])
            self._stage_bd = Line(rounded_rectangle=(0, 0, self.width, self.height, dp(12)), width=dp(1))

            Color(*colors["border"])
            self._wire_line = Line(points=[0, 0, 10, 0], width=dp(3))
            self._wire_glow_color = Color(*colors["accent"])
            self._wire_pulse = Line(points=[0, 0, 10, 0], width=dp(2.5))
            self._signal_dot_color = Color(1, 1, 1, 0)
            self._signal_dot = Ellipse(pos=(0, 0), size=(dp(10), dp(10)))

        registrar_fundo(self, self._stage_fill, "shell")
        self.bind(
            size=self._redesenhar_fundo,
            pos=self._redesenhar_fundo,
            wire_progress=self._redesenhar_onda,
            wave_phase=self._redesenhar_onda,
        )
        self._construir_pilhas()

    def on_parent(self, _widget, parent):
        if parent is None and self._wave_ev is not None:
            self._wave_ev.cancel()
            self._wave_ev = None

    def _redesenhar_fundo(self, *_args):
        self._stage_bg.pos = (0, 0)
        self._stage_bg.size = self.size
        self._stage_bd.rounded_rectangle = (0, 0, self.width, self.height, dp(12))
        y_wire = self.height * 0.14
        self._wire_line.points = [self.width * 0.31, y_wire, self.width * 0.69, y_wire]
        self._redesenhar_onda()

    def _redesenhar_onda(self, *_args):
        colors = paleta_praticas()
        y_wire = self.height * 0.14
        x1 = self.width * 0.31
        x2 = self.width * 0.69
        if self._lado_ativo == "wire":
            self._wire_glow_color.rgba = colors["danger"]
            pts = []
            steps = 28
            for i in range(steps + 1):
                t = i / steps
                px = x1 + (x2 - x1) * t
                sq = 1.0 if math.sin((t * 6.0 - self.wave_phase) * math.pi * 2) >= 0 else -1.0
                pts.extend([px, y_wire + sq * dp(7)])
            self._wire_pulse.points = pts
            self._signal_dot_color.rgba = colors["warning"]
            dot_x = x1 + (x2 - x1) * self.wire_progress - dp(5)
            self._signal_dot.pos = (dot_x, y_wire - dp(5))
        else:
            self._wire_glow_color.rgba = (*colors["accent"][:3], 0.35)
            self._wire_pulse.points = [x1, y_wire, x2, y_wire]
            self._signal_dot_color.rgba = (1, 1, 1, 0)

    def _criar_coluna_pilha(self, lado: str, titulo: str, x_hint: float):
        colors = paleta_praticas()
        col = BoxLayout(
            orientation="vertical",
            size_hint=(0.27, 0.90),
            pos_hint={"x": x_hint, "center_y": 0.5},
            spacing=dp(3),
            padding=(dp(6), dp(6)),
        )
        with col.canvas.before:
            c_fill = Color(*colors["card"])
            c_bg = RoundedRectangle(pos=col.pos, size=col.size, radius=[dp(10)])
            Color(*colors["border"])
            c_bd = Line(rounded_rectangle=(col.x, col.y, col.width, col.height, dp(10)), width=dp(1))
        registrar_fundo(col, c_fill, "card")
        _bind_rounded_bg(col, c_bg, c_bd, dp(10))

        hdr = Label(
            text=titulo,
            font_size="10sp",
            bold=True,
            color=colors["accent"],
            size_hint_y=None,
            height=dp(18),
            halign="center",
            valign="middle",
        )
        hdr.bind(size=lambda i, sz: setattr(i, "text_size", sz))
        registrar_cor_texto(hdr, colors["accent"], "accent")
        col.add_widget(hdr)

        colors_map = self._rows_a_colors if lado == "A" else self._rows_b_colors
        for num, nome, role in self.CAMADAS:
            row = BoxLayout(size_hint=(1, 1), padding=(dp(6), dp(1)))
            with row.canvas.before:
                r_fill = Color(*colors["panel"])
                r_bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(5)])
                r_bd_col = Color(*colors["border"])
                r_bd = Line(rounded_rectangle=(row.x, row.y, row.width, row.height, dp(5)), width=dp(0.8))
            _bind_rounded_bg(row, r_bg, r_bd, dp(5))
            lbl = Label(
                text=nome,
                font_size="9.5sp",
                bold=True,
                color=colors["text_secondary"],
                halign="left",
                valign="middle",
            )
            lbl.bind(size=lambda i, sz: setattr(i, "text_size", sz))
            row.add_widget(lbl)
            col.add_widget(row)
            colors_map[num] = (r_fill, r_bd_col, lbl, role)

        self.add_widget(col)

    def _construir_pilhas(self):
        colors = paleta_praticas()
        self._criar_coluna_pilha("A", "PC-A • Transmissor", 0.03)
        self._criar_coluna_pilha("B", "PC-B • Receptor", 0.70)

        self._lbl_arena_acao = Label(
            text="ENCAPSULAMENTO NO TRANSMISSOR",
            font_size="10sp",
            bold=True,
            color=colors["accent"],
            size_hint=(0.36, None),
            height=dp(20),
            pos_hint={"center_x": 0.5, "top": 0.94},
            halign="center",
            valign="middle",
        )
        self._lbl_arena_acao.bind(size=lambda i, sz: setattr(i, "text_size", sz))
        self.add_widget(self._lbl_arena_acao)

        self._pdu_stack_box = BoxLayout(
            orientation="horizontal",
            size_hint=(0.35, None),
            height=dp(36),
            pos_hint={"center_x": 0.5, "center_y": 0.54},
            spacing=dp(3),
            padding=(dp(4), dp(4)),
        )
        with self._pdu_stack_box.canvas.before:
            Color(*colors["card_elevated"])
            pb = RoundedRectangle(pos=self._pdu_stack_box.pos, size=self._pdu_stack_box.size, radius=[dp(8)])
            Color(*colors["border"])
            pl = Line(
                rounded_rectangle=(
                    self._pdu_stack_box.x,
                    self._pdu_stack_box.y,
                    self._pdu_stack_box.width,
                    self._pdu_stack_box.height,
                    dp(8),
                ),
                width=dp(1),
            )
        _bind_rounded_bg(self._pdu_stack_box, pb, pl, dp(8))
        self.add_widget(self._pdu_stack_box)

        self._pacote_float = _criar_pilula_pacote(
            self, "PDU C7", "package-variant-closed", 0.165, 0.84, width=dp(88)
        )

        self._lbl_wire_info = Label(
            text="Meio Físico • Bridge Docker Ethernet",
            font_size="9sp",
            bold=True,
            color=colors["muted"],
            size_hint=(0.36, None),
            height=dp(18),
            pos_hint={"center_x": 0.5, "y": 0.02},
            halign="center",
            valign="middle",
        )
        self._lbl_wire_info.bind(size=lambda i, sz: setattr(i, "text_size", sz))
        self.add_widget(self._lbl_wire_info)

    def definir_passo(self, _idx: int, passo: dict, animar: bool = True):
        colors = paleta_praticas()
        anim = passo.get("anim", {})
        lado = anim.get("lado", "A")
        camada = int(anim.get("camada", 7))
        pdu_badges = anim.get("pdu_blocos", [("DADOS", "success")])
        self._lado_ativo = lado
        self._camada_ativa = camada
        self._lbl_arena_acao.text = anim.get("acao", "PROCESSANDO CAMADA")
        self._pacote_float._label.text = anim.get("pkt_label", f"PDU C{camada}")
        self._lbl_wire_info.text = anim.get("wire_info", "Meio Físico • Bridge Docker Ethernet")

        for num, (r_fill, r_bd, lbl, role) in self._rows_a_colors.items():
            ativo = lado == "A" and num == camada
            ja_passou = (lado == "A" and num > camada) or lado in ("wire", "B")
            if ativo:
                r_fill.rgba = colors[role]
                r_bd.rgba = (1, 1, 1, 0.85)
                lbl.color = cor_contraste(colors[role])
            elif ja_passou:
                r_fill.rgba = (*colors[role][:3], 0.18)
                r_bd.rgba = (*colors[role][:3], 0.55)
                lbl.color = colors["text"]
            else:
                r_fill.rgba = colors["panel"]
                r_bd.rgba = colors["border"]
                lbl.color = colors["text_secondary"]

        for num, (r_fill, r_bd, lbl, role) in self._rows_b_colors.items():
            ativo = lado == "B" and num == camada
            ja_passou = lado == "B" and num < camada
            if ativo:
                cor_b = colors["success"] if camada >= 4 else colors[role]
                r_fill.rgba = cor_b
                r_bd.rgba = (1, 1, 1, 0.85)
                lbl.color = cor_contraste(cor_b)
            elif ja_passou:
                r_fill.rgba = (*colors["success"][:3], 0.18)
                r_bd.rgba = (*colors["success"][:3], 0.55)
                lbl.color = colors["text"]
            else:
                r_fill.rgba = colors["panel"]
                r_bd.rgba = colors["border"]
                lbl.color = colors["text_secondary"]

        self._pdu_stack_box.clear_widgets()
        for b_txt, b_role in pdu_badges:
            bloco = BoxLayout(padding=(dp(3), dp(2)))
            cor_b = colors.get(b_role, colors["accent"])
            with bloco.canvas.before:
                Color(*cor_b)
                r = RoundedRectangle(pos=bloco.pos, size=bloco.size, radius=[dp(5)])
            _bind_rounded_bg(bloco, r, None, dp(5))
            bloco.add_widget(Label(text=b_txt, font_size="8.5sp", bold=True, color=cor_contraste(cor_b)))
            self._pdu_stack_box.add_widget(bloco)

        y_camada = 0.15 + ((camada - 1) / 6.0) * 0.66
        if lado == "A":
            target_x, target_y = 0.23, y_camada
            pkt_cor = colors.get(passo.get("cor", "primary"), colors["primary"])
        elif lado == "wire":
            target_x, target_y = 0.64, 0.15
            pkt_cor = colors["danger"]
        else:
            target_x, target_y = 0.77, y_camada
            pkt_cor = colors["success"]

        self._pacote_float._fill.rgba = pkt_cor
        txt_c = cor_contraste(pkt_cor)
        self._pacote_float._label.color = txt_c
        self._pacote_float._icon.color = txt_c

        Animation.cancel_all(self._pacote_float)
        if animar:
            if lado == "wire":
                self._pacote_float.pos_hint = {"center_x": 0.34, "center_y": 0.15}
                Animation(pos_hint={"center_x": target_x, "center_y": target_y}, d=0.75, t="in_out_cubic").start(
                    self._pacote_float
                )
            else:
                Animation(pos_hint={"center_x": target_x, "center_y": target_y}, d=0.45, t="out_cubic").start(
                    self._pacote_float
                )
        else:
            self._pacote_float.pos_hint = {"center_x": target_x, "center_y": target_y}

        if self._wave_ev is not None:
            self._wave_ev.cancel()
            self._wave_ev = None
        Animation.cancel_all(self, "wire_progress")
        if lado == "wire":
            self.wire_progress = 0.0
            Animation(wire_progress=1.0, d=0.9, t="linear").start(self)
            self._wave_ev = Clock.schedule_interval(self._tick_wave, 1 / 30.0)
        self._redesenhar_onda()

    def _tick_wave(self, dt):
        self.wave_phase = (self.wave_phase + dt * 1.4) % 1.0


class PalcoAnimadoRoteamento(RelativeLayout):
    """Topologia animada para explicar Bitwise AND, Switch L2 vs Roteador L3 e Máscara Assimétrica."""

    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=dp(236), **kwargs)
        colors = paleta_praticas()

        with self.canvas.before:
            self._stage_fill = Color(*colors["shell"])
            self._stage_bg = RoundedRectangle(pos=(0, 0), size=self.size, radius=[dp(12)])
            Color(*colors["border"])
            self._stage_bd = Line(rounded_rectangle=(0, 0, self.width, self.height, dp(12)), width=dp(1))

            self._c_a_sw = Color(*colors["border"])
            self._l_a_sw = Line(points=[0, 0, 10, 0], width=dp(2.5))
            self._c_sw_b = Color(*colors["border"])
            self._l_sw_b = Line(points=[0, 0, 10, 0], width=dp(2.5))
            self._c_sw_gw = Color(*colors["border"])
            self._l_sw_gw = Line(points=[0, 0, 10, 0], width=dp(2.5))
            self._c_gw_b = Color(*colors["border"])
            self._l_gw_b = Line(points=[0, 0, 10, 0], width=dp(2.2))

        registrar_fundo(self, self._stage_fill, "shell")
        self.bind(pos=self._sync_linhas, size=self._sync_linhas)

        self._node_a = _criar_no_topologia(self, "HOST A", "192.168.10.10/24", "laptop", "primary", 0.14, 0.50)
        self._node_gw = _criar_no_topologia(
            self, "GATEWAY / ROTEADOR L3", "Camada 3 • Salto de Rede", "router-wireless", "warning", 0.50, 0.80
        )
        self._node_sw = _criar_no_topologia(
            self, "SWITCH LOCAL L2", "Domínio Broadcast • ARP", "lan", "accent", 0.50, 0.24
        )
        self._node_b = _criar_no_topologia(self, "HOST B", "192.168.10.20/24", "server-network", "success", 0.86, 0.50)
        self._pkt = _criar_pilula_pacote(self, "Bitwise AND", "send", 0.14, 0.50, width=dp(108))

    def _sync_linhas(self, *_args):
        self._stage_bg.pos = (0, 0)
        self._stage_bg.size = self.size
        self._stage_bd.rounded_rectangle = (0, 0, self.width, self.height, dp(12))

        ax, ay = self.width * 0.14, self.height * 0.50
        sx, sy = self.width * 0.50, self.height * 0.24
        gx, gy = self.width * 0.50, self.height * 0.80
        bx, by = self.width * 0.86, self.height * 0.50

        self._l_a_sw.points = [ax, ay, sx, sy]
        self._l_sw_b.points = [sx, sy, bx, by]
        self._l_sw_gw.points = [sx, sy, gx, gy]
        self._l_gw_b.points = [gx, gy, bx, by]

    def configurar_hosts(self, host_a: str, host_b: str, modo: str):
        self._node_a._lbl_sub.text = host_a
        self._node_b._lbl_sub.text = host_b
        self._node_gw.opacity = 0.45 if modo == "local" else 1.0

    def definir_passo(self, _idx: int, passo: dict, animar: bool = True):
        colors = paleta_praticas()
        anim = passo.get("anim", {})
        cor_role = passo.get("cor", "primary")
        pkt_cor = colors.get(cor_role, colors["primary"])
        txt_c = cor_contraste(pkt_cor)

        self._pkt._label.text = anim.get("pkt_label", "Bitwise AND")
        self._pkt._fill.rgba = pkt_cor
        self._pkt._label.color = txt_c
        self._pkt._icon.color = txt_c

        ativos = set(anim.get("ativos", ("A",)))
        for node, key in ((self._node_a, "A"), (self._node_sw, "SW"), (self._node_gw, "GW"), (self._node_b, "B")):
            node._bd_col.rgba = colors[node._role] if key in ativos else colors["border"]

        c_off = (*colors["border"][:3], 0.45)
        edges = anim.get("edges", ())
        self._c_a_sw.rgba = pkt_cor if "A_SW" in edges else c_off
        self._c_sw_b.rgba = pkt_cor if "SW_B" in edges else c_off
        self._c_sw_gw.rgba = pkt_cor if "SW_GW" in edges else c_off
        self._c_gw_b.rgba = pkt_cor if "GW_B" in edges else c_off

        coords = {"A": (0.14, 0.50), "SW": (0.50, 0.24), "GW": (0.50, 0.80), "B": (0.86, 0.50)}
        origem = coords.get(anim.get("de", "A"), (0.14, 0.50))
        destino = coords.get(anim.get("para", "A"), (0.14, 0.50))

        Animation.cancel_all(self._pkt)
        if animar:
            self._pkt.pos_hint = {"center_x": origem[0], "center_y": origem[1]}
            Animation(pos_hint={"center_x": destino[0], "center_y": destino[1]}, d=0.65, t="in_out_cubic").start(self._pkt)
        else:
            self._pkt.pos_hint = {"center_x": destino[0], "center_y": destino[1]}


class PalcoAnimadoDNS(RelativeLayout):
    """Diagrama animado passo a passo da resolução hierárquica DNS."""

    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=dp(248), **kwargs)
        colors = paleta_praticas()

        with self.canvas.before:
            self._stage_fill = Color(*colors["shell"])
            self._stage_bg = RoundedRectangle(pos=(0, 0), size=self.size, radius=[dp(12)])
            Color(*colors["border"])
            self._stage_bd = Line(rounded_rectangle=(0, 0, self.width, self.height, dp(12)), width=dp(1))

            self._c_cli_res = Color(*colors["border"])
            self._l_cli_res = Line(points=[0, 0, 10, 0], width=dp(2.5))
            self._c_res_root = Color(*colors["border"])
            self._l_res_root = Line(points=[0, 0, 10, 0], width=dp(2.2))
            self._c_res_tld = Color(*colors["border"])
            self._l_res_tld = Line(points=[0, 0, 10, 0], width=dp(2.2))
            self._c_res_auth = Color(*colors["border"])
            self._l_res_auth = Line(points=[0, 0, 10, 0], width=dp(2.2))

        registrar_fundo(self, self._stage_fill, "shell")
        self.bind(pos=self._sync_linhas, size=self._sync_linhas)

        self._nodes = {
            "CLI": _criar_no_topologia(self, "PC-A (Cliente)", "Cache Local SO", "laptop", "primary", 0.14, 0.50, height=dp(54)),
            "RES": _criar_no_topologia(self, "Resolver Recursivo", "ISP / DNS Local", "dns", "accent", 0.44, 0.50, height=dp(54)),
            "ROOT": _criar_no_topologia(self, "Root Server (.)", "Raiz Global DNS", "web", "warning", 0.82, 0.80, height=dp(54)),
            "TLD": _criar_no_topologia(self, "Servidor TLD", "Ex: .com / .local", "layers-outline", "info", 0.82, 0.50, height=dp(54)),
            "AUTH": _criar_no_topologia(self, "Autoritativo (NS1)", "Zona Oficial", "server-network", "success", 0.82, 0.20, height=dp(54)),
        }
        self._pkt = _criar_pilula_pacote(self, "QUERY", "dns", 0.14, 0.50, width=dp(108))

    def _sync_linhas(self, *_args):
        self._stage_bg.pos = (0, 0)
        self._stage_bg.size = self.size
        self._stage_bd.rounded_rectangle = (0, 0, self.width, self.height, dp(12))

        x_cli, y_cli = self.width * 0.14, self.height * 0.50
        x_res, y_res = self.width * 0.44, self.height * 0.50
        x_srv = self.width * 0.82

        self._l_cli_res.points = [x_cli, y_cli, x_res, y_res]
        self._l_res_root.points = [x_res, y_res, x_srv, self.height * 0.80]
        self._l_res_tld.points = [x_res, y_res, x_srv, self.height * 0.50]
        self._l_res_auth.points = [x_res, y_res, x_srv, self.height * 0.20]

    def definir_passo(self, _idx: int, passo: dict, animar: bool = True):
        colors = paleta_praticas()
        anim = passo.get("anim", {})
        cor_role = passo.get("cor", "primary")
        pkt_cor = colors.get(cor_role, colors["primary"])
        txt_c = cor_contraste(pkt_cor)

        self._pkt._label.text = anim.get("pkt_label", "QUERY")
        self._pkt._fill.rgba = pkt_cor
        self._pkt._label.color = txt_c
        self._pkt._icon.color = txt_c

        for key, text in anim.get("subs", {}).items():
            if key in self._nodes:
                self._nodes[key]._lbl_sub.text = text

        ativos = set(anim.get("ativos", ("CLI",)))
        for key, node in self._nodes.items():
            node._bd_col.rgba = colors[node._role] if key in ativos else colors["border"]

        c_off = (*colors["border"][:3], 0.45)
        edge = anim.get("edge", "")
        self._c_cli_res.rgba = pkt_cor if edge == "CLI_RES" else c_off
        self._c_res_root.rgba = pkt_cor if edge == "RES_ROOT" else c_off
        self._c_res_tld.rgba = pkt_cor if edge == "RES_TLD" else c_off
        self._c_res_auth.rgba = pkt_cor if edge == "RES_AUTH" else c_off

        coords = {
            "CLI": (0.14, 0.50),
            "RES": (0.44, 0.50),
            "ROOT": (0.82, 0.80),
            "TLD": (0.82, 0.50),
            "AUTH": (0.82, 0.20),
        }
        origem = coords.get(anim.get("de", "CLI"), (0.14, 0.50))
        destino = coords.get(anim.get("para", "CLI"), (0.14, 0.50))

        Animation.cancel_all(self._pkt)
        if animar:
            self._pkt.pos_hint = {"center_x": origem[0], "center_y": origem[1]}
            Animation(pos_hint={"center_x": destino[0], "center_y": destino[1]}, d=0.65, t="in_out_cubic").start(self._pkt)
        else:
            self._pkt.pos_hint = {"center_x": destino[0], "center_y": destino[1]}


def construir_visualizador_bits_ipv4(ip_bytes: bytes, prefixlen: int, titulo: str, valor_decimal: str) -> BoxLayout:
    """Cria uma barra HUD colorida dividindo bits de Rede (Azul) vs bits de Host (Verde) nos 4 octetos."""
    colors = paleta_praticas()
    row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32), spacing=dp(8))

    lbl_t = Label(
        text=titulo,
        font_size="10sp",
        bold=True,
        color=colors["muted"],
        size_hint=(None, 1),
        width=dp(95),
        halign="left",
        valign="middle",
    )
    lbl_t.bind(size=lambda i, sz: setattr(i, "text_size", sz))
    registrar_cor_texto(lbl_t, colors["muted"], "muted")
    row.add_widget(lbl_t)

    bits_all = "".join(f"{b:08b}" for b in ip_bytes)
    octetos_box = GridLayout(cols=4, spacing=dp(6), size_hint=(1, 1))
    for oct_idx in range(4):
        start = oct_idx * 8
        oct_bits = bits_all[start:start + 8]
        markup_parts = []
        for bit_i, bit_ch in enumerate(oct_bits):
            pos_global = start + bit_i
            if pos_global < prefixlen:
                markup_parts.append(f"[color=4c9aff]{bit_ch}[/color]")
            else:
                markup_parts.append(f"[color=38d399]{bit_ch}[/color]")
        oct_box = BoxLayout(padding=(dp(4), dp(2)))
        with oct_box.canvas.before:
            Color(*colors["terminal"])
            bg = RoundedRectangle(pos=oct_box.pos, size=oct_box.size, radius=[dp(6)])
        _bind_rounded_bg(oct_box, bg, None, dp(6))
        lbl_oct = Label(text="".join(markup_parts), markup=True, font_size="10.5sp", bold=True, halign="center", valign="middle")
        oct_box.add_widget(lbl_oct)
        octetos_box.add_widget(oct_box)
    row.add_widget(octetos_box)

    lbl_dec = criar_pill(valor_decimal, colors["tag_bg"], colors["text"], height=dp(26), fixed_width=dp(122), font_size="9.5sp")
    lbl_dec.pos_hint = {"center_y": 0.5}
    row.add_widget(lbl_dec)
    return row
