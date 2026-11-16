"""Laboratórios interativos e práticos de Redes I e Modelo OSI com integração Docker."""
from __future__ import annotations

import binascii
import ipaddress
import random
import threading
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from model.componentes import BotaoAcao, CampoTexto, IconeUI
from model.tema_praticas import aplicar_tema_arvore, paleta_praticas, registrar_cor_texto, registrar_fundo, tema_escuro
from service.docker_service import DockerService
from service.network_lab_docker import DockerNetworkLab


def _label(text: str, *, size="12sp", color=None, bold=False, height=dp(28), valign="middle", halign="left", auto_height=False):
    if color is None:
        color = paleta_praticas()["text"]
    item = Label(text=text, size_hint_y=None, height=height, color=color, bold=bold,
                 font_size=size, halign=halign, valign=valign)
    registrar_cor_texto(item, color)
    item.bind(width=lambda widget, value: setattr(widget, "text_size", (max(1, value), None)))
    if auto_height:
        item.bind(texture_size=lambda widget, val: setattr(widget, "height", max(height, val[1] + dp(8))))
    return item


def _badge_pill(texto: str, bg_color, text_color, icone: str | None = None, height=dp(24), fixed_width=None):
    pill = BoxLayout(orientation="horizontal", size_hint=(None, None), height=height,
                     spacing=dp(5), padding=(dp(8), dp(2)))
    with pill.canvas.before:
        fill = Color(*bg_color)
        bg = RoundedRectangle(pos=pill.pos, size=pill.size, radius=[height / 2])
    pill.bind(pos=lambda item, value: setattr(bg, "pos", value),
              size=lambda item, value: setattr(bg, "size", value))
    if icone:
        pill.add_widget(IconeUI(nome=icone, size_hint=(None, None), size=(dp(14), height),
                                font_size=dp(13), color=text_color))

    lbl = Label(text=texto, color=text_color, bold=True, font_size="10sp",
                size_hint=(None, None), height=height)

    if fixed_width is not None:
        pill.width = fixed_width
        lbl.size_hint_x = 1
        lbl.halign = "center"
        lbl.valign = "middle"
        lbl.bind(size=lambda item, val: setattr(item, "text_size", val))
    else:
        def _on_texture_size(instance, value):
            lbl.width = value[0]
            icon_w = dp(19) if icone else dp(0)
            pill.width = value[0] + dp(18) + icon_w

        lbl.bind(texture_size=_on_texture_size)
        icon_w = dp(19) if icone else dp(0)
        approx_w = max(dp(28), len(texto) * dp(7) + dp(18) + icon_w)
        pill.width = approx_w
        lbl.width = max(dp(10), len(texto) * dp(7))

    pill.add_widget(lbl)
    return pill


def _card(*, padding=dp(14), spacing=dp(8), elevated=False):
    colors = paleta_praticas()
    item = GridLayout(cols=1, padding=padding, spacing=spacing, size_hint_y=None)
    card_bg = colors["card_elevated"] if elevated else colors["card"]
    with item.canvas.before:
        fill = Color(*card_bg)
        bg = RoundedRectangle(pos=item.pos, size=item.size, radius=[dp(12)])
        border_col = Color(*colors["border"])
        border = Line(rounded_rectangle=(item.x, item.y, item.width, item.height, dp(12)), width=dp(1))
    registrar_fundo(item, fill, "card_elevated" if elevated else "card")
    item.bind(pos=lambda widget, value: (setattr(bg, "pos", value),
                                         setattr(border, "rounded_rectangle", (value[0], value[1], widget.width, widget.height, dp(12)))),
              size=lambda widget, value: (setattr(bg, "size", value),
                                          setattr(border, "rounded_rectangle", (widget.x, widget.y, value[0], value[1], dp(12)))))
    item.bind(minimum_height=item.setter("height"))
    return item


def _bloco_pdu(titulo: str, subtitulo: str, cor_titulo, height=dp(52)):
    colors = paleta_praticas()
    bloco = BoxLayout(orientation="vertical", size_hint_y=None, height=height,
                      padding=(dp(4), dp(4)), spacing=dp(1))
    with bloco.canvas.before:
        fill = Color(*colors["card"])
        bg = RoundedRectangle(pos=bloco.pos, size=bloco.size, radius=[dp(8)])
        Color(*colors["border"])
        border = Line(rounded_rectangle=(bloco.x, bloco.y, bloco.width, bloco.height, dp(8)), width=dp(1))
    bloco.bind(pos=lambda item, value: (setattr(bg, "pos", value),
                                        setattr(border, "rounded_rectangle", (value[0], value[1], item.width, item.height, dp(8)))),
               size=lambda item, value: (setattr(bg, "size", value),
                                         setattr(border, "rounded_rectangle", (item.x, item.y, value[0], value[1], dp(8)))))

    lbl_top = Label(text=titulo, bold=True, font_size="9sp", color=cor_titulo,
                    halign="center", valign="middle", size_hint=(1, 0.55))
    lbl_top.bind(size=lambda item, val: setattr(item, "text_size", val))

    lbl_sub = Label(text=subtitulo, font_size="8sp", color=colors["muted"],
                    halign="center", valign="middle", size_hint=(1, 0.45))
    lbl_sub.bind(size=lambda item, val: setattr(item, "text_size", val))

    bloco.add_widget(lbl_top)
    bloco.add_widget(lbl_sub)
    return bloco


def _button(text: str, action, *, variant="primary", height=dp(38), font_size="11sp", icone=None):
    item = BotaoAcao(text=text, variant=variant, size_hint_y=None, height=height,
                     color=(1, 1, 1, 1), bold=True, font_size=font_size,
                     padding=(dp(10), dp(6)))
    if icone:
        item.icone = icone
        item.icon_position = "left"
    item.bind(on_release=lambda *_args: action())
    return item


def _campo(rotulo: str, dica: str, *, appearance="light", multiline=False, height=dp(38)):
    wrapper = BoxLayout(orientation="vertical", spacing=dp(3), size_hint_y=None,
                        height=height + dp(23))
    wrapper.add_widget(_label(rotulo, size="10sp", color=paleta_praticas()["muted"], bold=True, height=dp(18)))
    wrapper.input = CampoTexto(hint_text=dica, appearance="dark" if tema_escuro() else appearance, multiline=multiline,
                               size_hint_y=None, height=height, font_size="11sp")
    wrapper.input._tema_aparencia = True
    wrapper.add_widget(wrapper.input)
    return wrapper


def _header(voltar, titulo: str, subtitulo: str, icone: str = "lan"):
    colors = paleta_praticas()
    area = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(72))
    bar = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(10))

    btn_voltar = _button("Voltar para Redes I", voltar, variant="secondary", height=dp(36), icone="arrow-left")
    btn_voltar.size_hint_x = None
    btn_voltar.width = dp(175)
    bar.add_widget(btn_voltar)

    bar.add_widget(IconeUI(nome=icone, size_hint=(None, None), size=(dp(30), dp(36)),
                           font_size=dp(24), color=colors["accent"]))
    lbl_title = _label(titulo, size="17sp", color=colors["text"], bold=True, height=dp(36))
    lbl_title.size_hint_x = 1
    bar.add_widget(lbl_title)

    badge = _badge_pill("LABORATÓRIO PRÁTICO", colors["tag_bg"], colors["accent"], "flask-outline", height=dp(26))
    bar.add_widget(badge)

    area.add_widget(bar)
    desc_label = _label(subtitulo, size="11sp", color=colors["muted"], height=dp(22))
    area.add_widget(desc_label)
    return area


class LaboratorioEnderecoIP(BoxLayout):
    """Laboratório interativo completo de Redes I: Simulador de Encapsulamento OSI,
    Bancada de Roteamento Bitwise AND e Calculadora CIDR com execução real via Docker.
    """

    PRESETS_PACOTE = {
        "http": {
            "nome": "HTTP · Porta 80",
            "app_proto": "HTTP",
            "transporte": "TCP",
            "porta_orig": "51234",
            "porta_dest": "80",
            "ip_orig": "192.168.10.10",
            "ip_dest": "192.168.10.20",
            "mac_orig": "02:42:C0:A8:0A:0A",
            "mac_dest": "02:42:C0:A8:0A:14",
            "payload": "GET /index.html HTTP/1.1\r\nHost: redes.local",
            "descricao": "Requisição Web padrão não criptografada trafegando via TCP 3-way handshake.",
        },
        "https": {
            "nome": "HTTPS · Porta 443",
            "app_proto": "HTTPS / TLS",
            "transporte": "TCP",
            "porta_orig": "52400",
            "porta_dest": "443",
            "ip_orig": "192.168.10.10",
            "ip_dest": "192.168.10.20",
            "mac_orig": "02:42:C0:A8:0A:0A",
            "mac_dest": "02:42:C0:A8:0A:14",
            "payload": "TLSv1.3 ClientHello [Cipher: TLS_AES_256_GCM_SHA384, SNI: seguro.local]",
            "descricao": "Negociação criptográfica TLS sobre TCP para estabelecer canal seguro.",
        },
        "dns": {
            "nome": "DNS · Porta 53",
            "app_proto": "DNS",
            "transporte": "UDP",
            "porta_orig": "53100",
            "porta_dest": "53",
            "ip_orig": "192.168.10.10",
            "ip_dest": "192.168.10.1",
            "mac_orig": "02:42:C0:A8:0A:0A",
            "mac_dest": "02:42:C0:A8:0A:01",
            "payload": "Standard query 0x1A2B A pm-painel.local",
            "descricao": "Consulta de resolução de nomes rápida e sem conexão usando datagrama UDP.",
        },
        "ssh": {
            "nome": "SSH · Porta 22",
            "app_proto": "SSH",
            "transporte": "TCP",
            "porta_orig": "49800",
            "porta_dest": "22",
            "ip_orig": "192.168.10.10",
            "ip_dest": "192.168.10.20",
            "mac_orig": "02:42:C0:A8:0A:0A",
            "mac_dest": "02:42:C0:A8:0A:14",
            "payload": "SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u2",
            "descricao": "Canal de terminal remoto seguro e autenticado via TCP.",
        },
        "icmp": {
            "nome": "Ping · ICMP Echo",
            "app_proto": "ICMP",
            "transporte": "ICMP",
            "porta_orig": "N/A",
            "porta_dest": "N/A",
            "ip_orig": "192.168.10.10",
            "ip_dest": "192.168.10.20",
            "mac_orig": "02:42:C0:A8:0A:0A",
            "mac_dest": "02:42:C0:A8:0A:14",
            "payload": "Echo (ping) request id=0x0001 seq=1 timestamp=1731600000",
            "descricao": "Diagnóstico de conectividade na Camada 3 de Rede sem portas de transporte.",
        },
    }

    def __init__(self, on_voltar, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(8), **kwargs)
        self.on_voltar = on_voltar
        self._aba_ativa = "osi"  # 'osi', 'roteamento', 'calculadora'

        # Estado da simulação OSI e Docker
        self._preset_atual = "http"
        self.docker_service = DockerService()
        self.docker_lab = DockerNetworkLab()
        self._docker_ativo = False
        self._lab_pronto = False
        self._iniciando_docker = False
        self._executando_experimento = False
        self._dados_experimento = {}
        self._macs_reais = {"A": "02:42:C0:A8:0A:0A", "B": "02:42:C0:A8:0A:14"}

        # Cabeçalho
        self.add_widget(_header(
            self.on_voltar,
            "Bancada Prática de Redes I & Modelo OSI",
            "Simulação interativa e execução real em containers Debian: encapsulamento OSI, cálculo bitwise AND e analisador CIDR.",
            icone="lan-connect"
        ))

        # Barra de status e conectividade do Docker Engine
        self._barra_docker = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
        self.add_widget(self._barra_docker)
        self._atualizar_barra_docker()

        # Barra de abas
        self._barra_abas = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        self.add_widget(self._barra_abas)

        # Contêiner de conteúdo dinâmico
        self._area_conteudo = BoxLayout(orientation="vertical", size_hint=(1, 1))
        self.add_widget(self._area_conteudo)

        self._atualizar_abas()

        # Inicia verificação do Docker e inicialização de background
        threading.Thread(target=self._verificar_docker_background, daemon=True).start()

    def aplicar_tema(self):
        aplicar_tema_arvore(self)

    def _verificar_docker_background(self):
        try:
            running, _msg = self.docker_service.is_running(timeout=2.0)
            self._docker_ativo = running
            if running:
                Clock.schedule_once(lambda _dt: self._atualizar_barra_docker(), 0)
                if not self.docker_lab.esta_pronto():
                    self.docker_lab.iniciar({"A": "192.168.10.10/24", "B": "192.168.10.20/24"})
                self._lab_pronto = self.docker_lab.esta_pronto()
                if self._lab_pronto:
                    self._macs_reais = self.docker_lab.obter_macs()
                    for p in self.PRESETS_PACOTE.values():
                        p["mac_orig"] = self._macs_reais.get("A", "02:42:C0:A8:0A:0A")
                        p["mac_dest"] = self._macs_reais.get("B", "02:42:C0:A8:0A:14")
            Clock.schedule_once(lambda _dt: self._atualizar_barra_docker(), 0)
            if self._aba_ativa == "osi":
                Clock.schedule_once(lambda _dt: self._atualizar_abas(), 0)
        except Exception:
            self._docker_ativo = False
            self._lab_pronto = False
            Clock.schedule_once(lambda _dt: self._atualizar_barra_docker(), 0)

    def _iniciar_docker_desktop(self):
        if self._iniciando_docker:
            return
        self._iniciando_docker = True
        self._atualizar_barra_docker()
        def worker():
            sucesso, _msg = self.docker_service.start_docker_service(timeout=60)
            self._iniciando_docker = False
            if sucesso:
                self._verificar_docker_background()
            else:
                Clock.schedule_once(lambda _dt: self._atualizar_barra_docker(), 0)
        threading.Thread(target=worker, daemon=True).start()

    def _atualizar_barra_docker(self):
        colors = paleta_praticas()
        self._barra_docker.clear_widgets()
        if self._lab_pronto:
            badge_lab = _badge_pill("DOCKER ENGINE REAL: ATIVO", colors["success_bg"], colors["success"], "docker", height=dp(26))
            badge_net = _badge_pill("LAN BRIDGE: 192.168.10.0/24", colors["tag_bg"], colors["accent"], "lan-connect", height=dp(26))
            mac_a_curto = self._macs_reais.get("A", "PC-A")[-8:]
            mac_b_curto = self._macs_reais.get("B", "PC-B")[-8:]
            badge_pcs = _badge_pill(f"PC-A ({mac_a_curto}) ↔ PC-B ({mac_b_curto})", colors["tag_bg"], colors["muted"], "devices", height=dp(26))
            badge_live = _badge_pill("DADOS REAIS EM TEMPO REAL", colors["tag_bg"], colors["primary"], "check-decagram", height=dp(26))
            self._barra_docker.add_widget(badge_lab)
            self._barra_docker.add_widget(badge_net)
            self._barra_docker.add_widget(badge_pcs)
            self._barra_docker.add_widget(badge_live)
        elif self._iniciando_docker:
            badge_iniciando = _badge_pill("INICIANDO DOCKER DESKTOP... AGUARDE", colors["tag_bg"], colors["warning"], "loading", height=dp(26))
            self._barra_docker.add_widget(badge_iniciando)
        elif self._docker_ativo:
            badge_starting = _badge_pill("INICIALIZANDO CONTAINERS DEBIAN EM BACKGROUND...", colors["tag_bg"], colors["warning"], "loading", height=dp(26))
            self._barra_docker.add_widget(badge_starting)
        else:
            badge_offline = _badge_pill("MODO SIMULAÇÃO LOCAL (DOCKER OFFLINE)", colors["tag_bg"], colors["muted"], "help-circle-outline", height=dp(26))
            btn_start = _button("Iniciar Docker Desktop para Dados Reais", self._iniciar_docker_desktop, variant="secondary", height=dp(26), font_size="9sp", icone="docker")
            btn_start.size_hint_x = None
            btn_start.width = dp(260)
            self._barra_docker.add_widget(badge_offline)
            self._barra_docker.add_widget(btn_start)

    def _trocar_aba(self, nova_aba: str):
        if self._aba_ativa != nova_aba:
            self._aba_ativa = nova_aba
            self._atualizar_abas()

    def _atualizar_abas(self):
        colors = paleta_praticas()
        self._barra_abas.clear_widgets()

        abas = (
            ("osi", "Encapsulamento OSI", "package-variant-closed"),
            ("roteamento", "Roteamento & Máscaras", "routes"),
            ("calculadora", "Calculadora CIDR & IP", "calculator-variant"),
        )
        for chave, titulo, icone in abas:
            ativa = self._aba_ativa == chave
            btn = _button(
                titulo,
                partial(self._trocar_aba, chave),
                variant="primary" if ativa else "secondary",
                height=dp(36),
                icone=icone,
                font_size="11sp"
            )
            self._barra_abas.add_widget(btn)

        self._area_conteudo.clear_widgets()
        if self._aba_ativa == "osi":
            self._area_conteudo.add_widget(self._montar_tela_osi())
        elif self._aba_ativa == "roteamento":
            self._area_conteudo.add_widget(self._montar_tela_roteamento())
        elif self._aba_ativa == "calculadora":
            self._area_conteudo.add_widget(self._montar_tela_calculadora())

    # =========================================================================
    # ABA 1: SIMULADOR DE ENCAPSULAMENTO E PILHA OSI (PDU INSPECTOR)
    # =========================================================================

    def _montar_tela_osi(self):
        colors = paleta_praticas()
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5), scroll_type=["bars", "content"])
        container = GridLayout(cols=1, spacing=dp(10), padding=(dp(2), dp(4)), size_hint_y=None)
        container.bind(minimum_height=container.setter("height"))

        preset = self.PRESETS_PACOTE[self._preset_atual]

        # 1. Seletor de Tráfego e Presets Rápidos
        card_presets = _card(padding=dp(12), spacing=dp(8))
        header_presets = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        header_presets.add_widget(_label("1. Seleção de Tráfego Prático (Gerador de Pacotes)", size="13sp", bold=True, color=colors["text"]))
        header_presets.add_widget(Widget())
        header_presets.add_widget(_badge_pill(preset["transporte"], colors["tag_bg"], colors["accent"]))
        card_presets.add_widget(header_presets)

        row_chips = GridLayout(cols=5, spacing=dp(6), size_hint_y=None, height=dp(34))
        for key, p in self.PRESETS_PACOTE.items():
            selecionado = key == self._preset_atual
            btn_chip = _button(
                p["nome"],
                partial(self._selecionar_preset_osi, key),
                variant="primary" if selecionado else "secondary",
                height=dp(32),
                font_size="10sp"
            )
            row_chips.add_widget(btn_chip)
        card_presets.add_widget(row_chips)
        card_presets.add_widget(_label(f"Contexto: {preset['descricao']}", size="11sp", color=colors["muted"], height=dp(20)))
        container.add_widget(card_presets)

        # 2. Visualizador Gráfico de Frame Ethernet (PDU Layout)
        card_frame = _card(padding=dp(12), spacing=dp(8), elevated=True)
        frame_header = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        frame_header.add_widget(_label("2. Estrutura do Quadro em Tempo Real (Frame Layout)", size="13sp", bold=True, color=colors["text"]))
        frame_header.add_widget(Widget())

        payload_bytes = len(preset["payload"].encode("utf-8"))
        header_transp_bytes = 20 if preset["transporte"] == "TCP" else (8 if preset["transporte"] == "UDP" else 0)
        total_bytes = 14 + 20 + header_transp_bytes + payload_bytes + 4

        frame_header.add_widget(_badge_pill(f"TOTAL: {total_bytes} BYTES", colors["success_bg"], colors["success"], "package-variant"))
        frame_header.add_widget(_badge_pill(f"MTU: 1500 B", colors["tag_bg"], colors["muted"]))
        card_frame.add_widget(frame_header)

        # Barra visual dos blocos do pacote
        layout_blocos = GridLayout(cols=5, spacing=dp(8), size_hint_y=None, height=dp(52))
        layout_blocos.add_widget(_bloco_pdu("Ethernet II (L2)", "14 bytes", colors["accent"]))
        layout_blocos.add_widget(_bloco_pdu("IPv4 Header (L3)", "20 bytes • TTL 64", colors["primary"]))
        transp_cor = (1, .75, .22, 1) if colors["shell"][0] < .5 else (.85, .55, .08, 1)
        layout_blocos.add_widget(_bloco_pdu(f"{preset['transporte']} Header (L4)", f"{header_transp_bytes} bytes", transp_cor))
        layout_blocos.add_widget(_bloco_pdu(f"Payload ({preset['app_proto']})", f"{payload_bytes} bytes de dados", colors["success"]))
        layout_blocos.add_widget(_bloco_pdu("FCS Trailer (CRC-32)", "4 bytes checagem", colors["danger"]))
        card_frame.add_widget(layout_blocos)

        # Botão de ação prática: Transmissão Real via Docker ou Simulação
        row_acoes = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        texto_btn = (
            "Transmitir Pacote Real via Docker (Executar no Container & Capturar com tcpdump)"
            if self._lab_pronto
            else "Transmitir Pacote pelo Meio Físico (Simular Desencapsulamento)"
        )
        btn_transmitir = _button(
            texto_btn,
            self._transmitir_pacote_osi,
            variant="primary",
            height=dp(38),
            font_size="11sp",
            icone="docker" if self._lab_pronto else "send"
        )
        row_acoes.add_widget(btn_transmitir)
        card_frame.add_widget(row_acoes)

        # Log de transmissão em container estilizado
        self.osi_log_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(48), padding=(dp(8), dp(6)))
        with self.osi_log_box.canvas.before:
            fill_log = Color(*colors["panel"])
            bg_log = RoundedRectangle(pos=self.osi_log_box.pos, size=self.osi_log_box.size, radius=[dp(8)])
        self.osi_log_box.bind(pos=lambda item, val: setattr(bg_log, "pos", val),
                              size=lambda item, val: setattr(bg_log, "size", val))

        msg_inicial = (
            "Clique em 'Transmitir Pacote Real' para executar o tráfego de rede diretamente no container Debian e capturar o quadro Ethernet ao vivo."
            if self._lab_pronto else
            "Clique em 'Transmitir Pacote' para observar a modulação em bits, travessia do meio físico e o desencapsulamento passo a passo no destino."
        )
        self.osi_log_label = Label(
            text=msg_inicial,
            font_size="10sp",
            color=colors["muted"],
            halign="left",
            valign="top",
            size_hint=(1, None),
            height=dp(34)
        )
        self.osi_log_label.bind(width=lambda item, val: setattr(item, "text_size", (max(1, val), None)))
        self.osi_log_label.bind(texture_size=lambda item, val: (
            setattr(item, "height", val[1]),
            setattr(self.osi_log_box, "height", val[1] + dp(14))
        ))
        self.osi_log_box.add_widget(self.osi_log_label)
        card_frame.add_widget(self.osi_log_box)

        # Container para Frame Dump (tcpdump) real
        self.osi_frame_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(0), padding=(dp(8), dp(6)), spacing=dp(2))
        self.osi_frame_box.opacity = 0
        with self.osi_frame_box.canvas.before:
            Color(*colors["shell"])
            f_bg = RoundedRectangle(pos=self.osi_frame_box.pos, size=self.osi_frame_box.size, radius=[dp(8)])
        self.osi_frame_box.bind(pos=lambda item, val: setattr(f_bg, "pos", val),
                                size=lambda item, val: setattr(f_bg, "size", val))
        self.osi_frame_box.add_widget(_label("Captura Real de Pacotes (tcpdump -XX no Container Receptor):", size="9sp", bold=True, color=colors["accent"], height=dp(16)))
        self.osi_frame_label = Label(
            text="",
            font_size="9sp",
            color=colors["text_secondary"],
            halign="left",
            valign="top",
            size_hint=(1, None),
            height=dp(20)
        )
        self.osi_frame_label.bind(width=lambda item, val: setattr(item, "text_size", (max(1, val), None)))
        self.osi_frame_label.bind(texture_size=lambda item, val: (
            setattr(item, "height", val[1]),
            setattr(self.osi_frame_box, "height", val[1] + dp(28)) if self.osi_frame_box.opacity > 0 else None
        ))
        self.osi_frame_box.add_widget(self.osi_frame_label)
        card_frame.add_widget(self.osi_frame_box)

        container.add_widget(card_frame)

        # 3. As 7 Camadas OSI em Inspeção Prática
        card_camadas = _card(padding=dp(12), spacing=dp(6))
        card_camadas.add_widget(_label("3. Inspeção Prática das 7 Camadas OSI (Transmissor -> Receptor)", size="13sp", bold=True, color=colors["text"]))

        camadas_info = [
            (7, "Aplicação", "Dados", f"Protocolo: {preset['app_proto']} • Payload: '{preset['payload'][:45]}...'", colors["success"]),
            (6, "Apresentação", "Codificação", f"UTF-8 Hex: {binascii.hexlify(preset['payload'][:14].encode()).decode()} • Criptografia: {'Ativa (TLS 1.3)' if 'TLS' in preset['payload'] else 'Texto Claro'}", colors["success"]),
            (5, "Sessão", "Diálogo", f"Sessão ID: #48291 • Modo: Full-Duplex • Gerenciamento de portas e canais lógicos", colors["info"]),
            (4, "Transporte", "Segmento", f"Protocolo: {preset['transporte']} • Porta Origem: {preset['porta_orig']} -> Destino: {preset['porta_dest']} • Checksum L4 OK", transp_cor),
            (3, "Rede", "Pacote IP", f"IPv4 • Origem: {preset['ip_orig']} -> Destino: {preset['ip_dest']} • TTL: 64 • Protocolo L4: {6 if preset['transporte'] == 'TCP' else (17 if preset['transporte'] == 'UDP' else 1)}", colors["primary"]),
            (2, "Enlace", "Quadro/Frame", f"Ethernet II • MAC Origem: {preset['mac_orig']} -> Destino: {preset['mac_dest']} • EtherType: 0x0800 • CRC-32", colors["accent"]),
            (1, "Física", "Bits no Meio", f"Sinalização: {''.join(f'{b:08b} ' for b in preset['payload'][:5].encode())}... (Pulsos elétricos na bridge Docker)", colors["danger"]),
        ]

        for num, nome, pdu, detalhes, cor in camadas_info:
            linha_c = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
            badge_num = _badge_pill(f"C{num}", colors["tag_bg"], cor, height=dp(26), fixed_width=dp(42))
            badge_pdu = _badge_pill(f"{nome} · {pdu}", colors["tag_bg"], colors["text"], height=dp(26), fixed_width=dp(175))
            linha_c.add_widget(badge_num)
            linha_c.add_widget(badge_pdu)
            lbl_det = _label(detalhes, size="10sp", color=colors["text_secondary"], height=dp(26))
            lbl_det.size_hint_x = 1
            linha_c.add_widget(lbl_det)
            card_camadas.add_widget(linha_c)

        container.add_widget(card_camadas)

        scroll.add_widget(container)
        return scroll

    def _selecionar_preset_osi(self, preset_key: str):
        self._preset_atual = preset_key
        self._atualizar_abas()

    def _transmitir_pacote_osi(self):
        colors = paleta_praticas()
        if self._lab_pronto:
            self.osi_log_label.text = "⚡ Executando tráfego real no container Debian PC-A ➔ PC-B e capturando quadro Ethernet com tcpdump..."
            self.osi_log_label.color = colors["warning"]

            def worker():
                dados = self.docker_lab.executar_experimento_osi(self._preset_atual)
                Clock.schedule_once(partial(self._on_experimento_osi_concluido, dados), 0)

            threading.Thread(target=worker, daemon=True).start()
        else:
            preset = self.PRESETS_PACOTE[self._preset_atual]
            linhas_log = [
                f"[MEIO FÍSICO]: Quadro transmitido via pulsos elétricos na interface.",
                f"1. FÍSICA: Placa de rede detectou preâmbulo e recebeu fluxo binário.",
                f"2. ENLACE: MAC destino {preset['mac_dest']} confere com a interface. CRC-32 válido. Cabeçalho L2 removido.",
                f"3. REDE: IP destino {preset['ip_dest']} validado. TTL decrementado (64 -> 63). Cabeçalho IPv4 removido.",
                f"4. TRANSPORTE: {preset['transporte']} Porta {preset['porta_dest']} aceitou conexão. Cabeçalho L4 removido.",
                f"5. APLICAÇÃO: Processo {preset['app_proto']} recebeu o payload '{preset['payload'][:35]}...' com sucesso! Status: 200 OK."
            ]
            self.osi_log_label.text = "\n".join(linhas_log)
            self.osi_log_label.color = colors["success"]

    def _on_experimento_osi_concluido(self, dados, _dt):
        colors = paleta_praticas()
        if not dados:
            return
        linhas_log = [
            f"[EXECUÇÃO REAL NO KERNEL LINUX VIA CONTAINER DEBIAN - INTERFACE eth0]:",
            f"• Status: {dados.get('status', 'OK')} | RTT Real: {dados.get('rtt', '0.08 ms')} | TTL: {dados.get('ttl', 64)}",
            f"1. FÍSICA: Placa detectou preâmbulo no meio físico bridge virtual da LAN.",
            f"2. ENLACE: MAC Origem {dados.get('mac_orig')} -> MAC Destino {dados.get('mac_dest')}. Quadro Ethernet II aceito.",
            f"3. REDE: IP Origem {dados.get('ip_orig')} -> IP Destino {dados.get('ip_dest')}. Protocolo L4: {dados.get('camada4')}.",
            f"4. TRANSPORTE: Segmento aceito na Porta {dados.get('porta_dest')}. Handshake L4 verificado.",
            f"5. APLICAÇÃO: Protocolo {dados.get('protocolo')} processou o payload com sucesso! ({dados.get('detalhes')})",
        ]
        self.osi_log_label.text = "\n".join(linhas_log)
        self.osi_log_label.color = colors["success"]

        if hasattr(self, "osi_frame_box") and dados.get("frame_dump"):
            self.osi_frame_box.opacity = 1
            self.osi_frame_label.text = dados["frame_dump"][:650]

    # =========================================================================
    # ABA 2: BANCADA DE ROTEAMENTO, MÁSCARAS E BITWISE AND (ROUTE TESTER)
    # =========================================================================

    def _montar_tela_roteamento(self):
        colors = paleta_praticas()
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5), scroll_type=["bars", "content"])
        container = GridLayout(cols=1, spacing=dp(10), padding=(dp(2), dp(4)), size_hint_y=None)
        container.bind(minimum_height=container.setter("height"))

        # Card de Cenários Práticos Rápidos
        card_cenarios = _card(padding=dp(12), spacing=dp(8))
        card_cenarios.add_widget(_label("Cenários Práticos de Roteamento e Sub-redes", size="13sp", bold=True, color=colors["text"]))

        cenarios = (
            ("Mesma Sub-rede /24 (Comunicação Direta)", "192.168.10.10/24", "192.168.10.20/24"),
            ("Sub-redes Diferentes /25 (Necessita Roteador L3)", "192.168.10.10/25", "192.168.10.130/25"),
            ("Máscara Incompatível (/24 vs /26)", "192.168.10.10/24", "192.168.10.130/26"),
            ("Rede Local vs Internet Pública", "192.168.10.10/24", "8.8.8.8/32"),
        )
        grid_cen = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(76))
        for titulo, ip_a, ip_b in cenarios:
            btn_cen = _button(
                titulo,
                partial(self._aplicar_cenario_roteamento, ip_a, ip_b),
                variant="secondary",
                height=dp(34),
                font_size="10sp"
            )
            grid_cen.add_widget(btn_cen)
        card_cenarios.add_widget(grid_cen)
        container.add_widget(card_cenarios)

        # Configuração dos Hosts
        card_hosts = _card(padding=dp(12), spacing=dp(8), elevated=True)
        card_hosts.add_widget(_label("Configuração dos Hosts para Teste de Rota", size="13sp", bold=True, color=colors["text"]))

        grid_inputs = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(68))
        self.rot_host_a = _campo("Host A (IP/Prefixo)", "Ex.: 192.168.10.10/24")
        self.rot_host_a.input.text = "192.168.10.10/24"
        self.rot_host_b = _campo("Host B (IP/Prefixo)", "Ex.: 192.168.10.20/24")
        self.rot_host_b.input.text = "192.168.10.20/24"
        grid_inputs.add_widget(self.rot_host_a)
        grid_inputs.add_widget(self.rot_host_b)
        card_hosts.add_widget(grid_inputs)

        btn_analisar = _button(
            "Analisar Rota & Executar Cálculo Bitwise AND",
            self._analisar_roteamento,
            variant="primary",
            height=dp(36),
            icone="routes"
        )
        card_hosts.add_widget(btn_analisar)
        container.add_widget(card_hosts)

        # Painel de Diagnóstico e Demonstração da Operação Bit-a-Bit & Rota no Kernel
        card_diag = _card(padding=dp(12), spacing=dp(8))
        card_diag.add_widget(_label("Demonstração Prática do Cálculo Bitwise AND & Rota no Kernel", size="13sp", bold=True, color=colors["text"]))

        self.rot_resultado_label = _label(
            "Preencha os endereços e clique em Analisar para ver o cálculo binário AND realizado pelo hardware de rede.",
            size="11sp",
            color=colors["text"],
            height=dp(60),
            auto_height=True,
            valign="top"
        )
        card_diag.add_widget(self.rot_resultado_label)
        container.add_widget(card_diag)

        # Painel Dedicado ao Teste Prático de Conectividade ICMP (Ping)
        card_ping = _card(padding=dp(12), spacing=dp(8), elevated=True)
        card_ping.add_widget(_label("Teste Prático de Conectividade ICMP (Ping Real entre Hosts)", size="13sp", bold=True, color=colors["text"]))

        texto_ping = "Executar Teste de Ping ICMP Real (Container PC-A)" if self._lab_pronto else "Executar Teste de Ping ICMP (4 Pacotes)"
        btn_ping = _button(texto_ping, self._executar_ping_cenario, variant="primary", height=dp(36), icone="network")
        card_ping.add_widget(btn_ping)

        self.rot_ping_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(44), padding=(dp(8), dp(6)))
        with self.rot_ping_box.canvas.before:
            fill_p = Color(*colors["panel"])
            bg_p = RoundedRectangle(pos=self.rot_ping_box.pos, size=self.rot_ping_box.size, radius=[dp(8)])
        self.rot_ping_box.bind(pos=lambda item, val: setattr(bg_p, "pos", val),
                               size=lambda item, val: setattr(bg_p, "size", val))

        self.rot_ping_label = _label("Clique no botão acima para disparar 4 pacotes ICMP e medir a latência real.",
                                     size="10sp", color=colors["muted"], height=dp(30), auto_height=True, valign="top")
        self.rot_ping_label.bind(texture_size=lambda item, val: setattr(self.rot_ping_box, "height", max(dp(44), val[1] + dp(14))))
        self.rot_ping_box.add_widget(self.rot_ping_label)
        card_ping.add_widget(self.rot_ping_box)
        container.add_widget(card_ping)

        scroll.add_widget(container)
        Clock.schedule_once(lambda _dt: self._analisar_roteamento(), 0)
        return scroll

    def _aplicar_cenario_roteamento(self, ip_a: str, ip_b: str):
        if hasattr(self, "rot_host_a") and hasattr(self, "rot_host_b"):
            self.rot_host_a.input.text = ip_a
            self.rot_host_b.input.text = ip_b
            self._analisar_roteamento()

    def _analisar_roteamento(self):
        colors = paleta_praticas()
        try:
            iface_a = ipaddress.ip_interface(self.rot_host_a.input.text.strip())
            iface_b = ipaddress.ip_interface(self.rot_host_b.input.text.strip())
        except ValueError:
            self.rot_resultado_label.text = "Erro: Digite endereços IPv4 válidos com prefixo CIDR (ex: 192.168.10.10/24)."
            registrar_cor_texto(self.rot_resultado_label, colors["danger"], "danger")
            return

        rede_a = iface_a.network
        rede_b = iface_b.network

        ip_a_bin = ".".join(f"{b:08b}" for b in iface_a.ip.packed)
        mask_a_bin = ".".join(f"{b:08b}" for b in rede_a.netmask.packed)
        net_a_bin = ".".join(f"{b:08b}" for b in rede_a.network_address.packed)

        ip_b_bin = ".".join(f"{b:08b}" for b in iface_b.ip.packed)
        mask_b_bin = ".".join(f"{b:08b}" for b in rede_b.netmask.packed)
        net_b_bin = ".".join(f"{b:08b}" for b in rede_b.network_address.packed)

        ip_b_na_mascara_de_a = ipaddress.ip_network(f"{iface_b.ip}/{rede_a.prefixlen}", strict=False)
        a_enxerga_b_local = (ip_b_na_mascara_de_a.network_address == rede_a.network_address)

        ip_a_na_mascara_de_b = ipaddress.ip_network(f"{iface_a.ip}/{rede_b.prefixlen}", strict=False)
        b_enxerga_a_local = (ip_a_na_mascara_de_b.network_address == rede_b.network_address)

        linhas = [
            f"[CÁLCULO BITWISE AND DO HOST A]:",
            f"  IP Host A:   {ip_a_bin}  ({iface_a.ip})",
            f"  Máscara:     {mask_a_bin}  (/{rede_a.prefixlen})",
            f"  AND = Rede:  {net_a_bin}  ({rede_a.network_address})\n",
            f"[CÁLCULO BITWISE AND DO HOST B]:",
            f"  IP Host B:   {ip_b_bin}  ({iface_b.ip})",
            f"  Máscara:     {mask_b_bin}  (/{rede_b.prefixlen})",
            f"  AND = Rede:  {net_b_bin}  ({rede_b.network_address})\n",
        ]

        if rede_a == rede_b:
            linhas.append(f"✓ DIAGNÓSTICO: MESMA SUB-REDE ({rede_a})")
            linhas.append("  • Comunicação DIRETA na Camada 2 (Enlace) via Switch local.")
            linhas.append("  • Host A envia broadcast ARP para descobrir o endereço MAC de Host B e transmite o quadro sem passar por roteador.")
            registrar_cor_texto(self.rot_resultado_label, colors["success"], "success")
        elif a_enxerga_b_local and not b_enxerga_a_local:
            linhas.append("⚡ DIAGNÓSTICO: MÁSCARA ASSIMÉTRICA / INCOMPATÍVEL!")
            linhas.append(f"  • Host A acha que B é local (Rede {rede_a}), mas Host B sabe que A está em outra sub-rede ({rede_b}).")
            linhas.append("  • Host A tentará ARP direto e Host B responderá via Gateway, causando falha de comunicação.")
            registrar_cor_texto(self.rot_resultado_label, colors["warning"], "warning")
        else:
            linhas.append("⚡ DIAGNÓSTICO: SUB-REDES DIFERENTES (ROTEAMENTO L3 OBRIGATÓRIO)")
            linhas.append(f"  • Rede A: {rede_a}  ≠  Rede B: {rede_b}")
            linhas.append("  • O pacote NÃO pode ser entregue diretamente pelo switch.")
            linhas.append("  • Host A encaminha o pacote para o MAC do Gateway Padrão (Roteador), que inspeciona o cabeçalho IP e faz o salto de rede.")
            registrar_cor_texto(self.rot_resultado_label, colors["text"], "text")

        self.rot_resultado_label.text = "\n".join(linhas)

        if self._lab_pronto:
            def worker():
                ok_r, out_r = self.docker_lab.consultar_rota_kernel(str(iface_b.ip))
                arp_out = self.docker_lab.consultar_vizinhos_arp()
                Clock.schedule_once(partial(self._on_rota_kernel_concluida, ok_r, out_r, arp_out, str(iface_b.ip)), 0)
            threading.Thread(target=worker, daemon=True).start()

    def _on_rota_kernel_concluida(self, ok, out_route, arp_out, ip_destino, _dt):
        if not hasattr(self, "rot_resultado_label"):
            return
        base_text = self.rot_resultado_label.text
        if "[CONSULTA REAL AO KERNEL LINUX" not in base_text:
            extra = [
                "",
                "[CONSULTA REAL À TABELA FIB DO KERNEL LINUX - CONTAINER PC-A]:",
                f"# ip route get {ip_destino}",
                f"  {out_route}",
                f"# Tabela ARP (ip neigh): {arp_out or 'Sem vizinho pré-armazenado no cache'}",
            ]
            self.rot_resultado_label.text = base_text + "\n" + "\n".join(extra)

    def _executar_ping_cenario(self):
        colors = paleta_praticas()
        try:
            iface_a = ipaddress.ip_interface(self.rot_host_a.input.text.strip())
            iface_b = ipaddress.ip_interface(self.rot_host_b.input.text.strip())
        except ValueError:
            return

        if self._lab_pronto:
            self.rot_ping_label.text = f"⚡ Executando ping -c 4 no container Debian PC-A em direção a {iface_b.ip}..."
            self.rot_ping_label.color = colors["warning"]

            def worker():
                ok, output = self.docker_lab.executar_ping_real(str(iface_b.ip), contagem=4)
                Clock.schedule_once(partial(self._on_ping_real_concluido, ok, output, iface_a, iface_b), 0)

            threading.Thread(target=worker, daemon=True).start()
        else:
            self._simular_ping()

    def _on_ping_real_concluido(self, ok, output, iface_a, iface_b, _dt):
        colors = paleta_praticas()
        badge = "[PING REAL NO KERNEL LINUX - CONTAINER DEBIAN PC-A]"
        self.rot_ping_label.text = f"{badge}\n{output}"
        self.rot_ping_label.color = colors["success"] if ok else colors["danger"]

    def _simular_ping(self):
        try:
            iface_a = ipaddress.ip_interface(self.rot_host_a.input.text.strip())
            iface_b = ipaddress.ip_interface(self.rot_host_b.input.text.strip())
        except ValueError:
            return

        mesma_rede = (iface_a.network == iface_b.network)
        rtt_base = 0.6 if mesma_rede else 14.2
        linhas = [f"PING {iface_b.ip} a partir de {iface_a.ip} com 32 bytes de dados ICMP (Simulado):"]

        for seq in range(1, 5):
            rtt = rtt_base + random.uniform(0.1, 0.4)
            ttl = 64 if mesma_rede else 63
            linhas.append(f"Resposta de {iface_b.ip}: bytes=32 tempo={rtt:.2f}ms TTL={ttl} seq={seq}")

        linhas.append(f"Estatísticas: 4 pacotes transmitidos, 4 recebidos, 0% perda ({'Tráfego local LAN' if mesma_rede else 'Roteamento L3 via Gateway'}).")
        self.rot_ping_label.text = "\n".join(linhas)

    # =========================================================================
    # ABA 3: CALCULADORA CIDR & CONVERSOR IP PROFISSIONAL
    # =========================================================================

    def _montar_tela_calculadora(self):
        colors = paleta_praticas()
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5), scroll_type=["bars", "content"])
        container = GridLayout(cols=1, spacing=dp(10), padding=(dp(2), dp(4)), size_hint_y=None)
        container.bind(minimum_height=container.setter("height"))

        # Card de Entrada
        card_input = _card(padding=dp(12), spacing=dp(8))
        header_calc = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        header_calc.add_widget(_label("Calculadora de Sub-redes CIDR & Conversor IP", size="13sp", bold=True, color=colors["text"]))
        header_calc.add_widget(Widget())
        header_calc.add_widget(_badge_pill("IPv4 & IPv6", colors["tag_bg"], colors["accent"], icone="calculator-variant"))
        card_input.add_widget(header_calc)

        # Chips de exemplos rápidos com proporção moderna
        row_chips = GridLayout(cols=5, spacing=dp(8), size_hint_y=None, height=dp(36))
        exemplos = ("192.168.10.0/24", "10.0.0.0/8", "172.16.0.0/16", "192.168.10.128/26", "2001:db8::/64")
        for ex in exemplos:
            btn_ex = _button(ex, partial(self._aplicar_exemplo_calc, ex), variant="secondary", height=dp(34), font_size="11sp")
            row_chips.add_widget(btn_ex)
        card_input.add_widget(row_chips)

        row_calc = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        self.calc_input = CampoTexto(
            hint_text="Digite IP/prefixo CIDR (ex: 192.168.10.34/24 ou 10.0.0.0/16)...",
            appearance="dark" if tema_escuro() else "light",
            size_hint_y=None,
            height=dp(42),
            font_size="12sp"
        )
        self.calc_input.text = "192.168.10.34/24"
        self.calc_input.size_hint_x = 0.74
        row_calc.add_widget(self.calc_input)

        btn_calc = _button("Calcular Sub-rede", self._calcular_cidr, variant="primary", height=dp(42), icone="calculator")
        btn_calc.size_hint_x = 0.26
        row_calc.add_widget(btn_calc)
        card_input.add_widget(row_calc)
        container.add_widget(card_input)

        # Painel de Métricas da Rede em Grid Estruturado
        card_metricas = _card(padding=dp(12), spacing=dp(8), elevated=True)
        header_met = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        header_met.add_widget(_label("Métricas e Faixas de Endereçamento Calculadas", size="13sp", bold=True, color=colors["text"]))
        header_met.add_widget(Widget())
        self.calc_badge_resumo = _badge_pill("IPv4 • /24", colors["success_bg"], colors["success"])
        header_met.add_widget(self.calc_badge_resumo)
        card_metricas.add_widget(header_met)

        self.calc_grid_metricas = GridLayout(cols=3, spacing=dp(8), size_hint_y=None)
        self.calc_grid_metricas.bind(minimum_height=self.calc_grid_metricas.setter("height"))
        card_metricas.add_widget(self.calc_grid_metricas)
        container.add_widget(card_metricas)

        # Conversão Binária, Hexadecimal e Sintaxe do Kernel Linux
        card_conv = _card(padding=dp(12), spacing=dp(8))
        card_conv.add_widget(_label("Representação Binária e Comandos Reais do Kernel Linux (iproute2)", size="13sp", bold=True, color=colors["text"]))

        # Sub-bloco binário
        self.calc_box_binario = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(100),
                                          padding=(dp(12), dp(8)), spacing=dp(4))
        with self.calc_box_binario.canvas.before:
            Color(*colors["shell"])
            bg_bin = RoundedRectangle(pos=self.calc_box_binario.pos, size=self.calc_box_binario.size, radius=[dp(8)])
            Color(*colors["border"])
            b_bin = Line(rounded_rectangle=(self.calc_box_binario.x, self.calc_box_binario.y, self.calc_box_binario.width, self.calc_box_binario.height, dp(8)), width=dp(1))
        self.calc_box_binario.bind(
            pos=lambda item, val, s=bg_bin, ln=b_bin: (setattr(s, "pos", val), setattr(ln, "rounded_rectangle", (val[0], val[1], item.width, item.height, dp(8)))),
            size=lambda item, val, s=bg_bin, ln=b_bin: (setattr(s, "size", val), setattr(ln, "rounded_rectangle", (item.x, item.y, val[0], val[1], dp(8))))
        )
        self.calc_label_bin = _label("", size="11sp", color=colors["text"], height=dp(84))
        self.calc_box_binario.add_widget(self.calc_label_bin)
        card_conv.add_widget(self.calc_box_binario)

        # Sub-bloco terminal Linux iproute2
        self.calc_box_term = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(120),
                                       padding=(dp(12), dp(8)), spacing=dp(4))
        with self.calc_box_term.canvas.before:
            Color(*colors["shell"])
            bg_term = RoundedRectangle(pos=self.calc_box_term.pos, size=self.calc_box_term.size, radius=[dp(8)])
            Color(0.2, 0.45, 0.8, 0.35)
            b_term = Line(rounded_rectangle=(self.calc_box_term.x, self.calc_box_term.y, self.calc_box_term.width, self.calc_box_term.height, dp(8)), width=dp(1))
        self.calc_box_term.bind(
            pos=lambda item, val, s=bg_term, ln=b_term: (setattr(s, "pos", val), setattr(ln, "rounded_rectangle", (val[0], val[1], item.width, item.height, dp(8)))),
            size=lambda item, val, s=bg_term, ln=b_term: (setattr(s, "size", val), setattr(ln, "rounded_rectangle", (item.x, item.y, val[0], val[1], dp(8))))
        )
        term_header = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(6))
        term_header.add_widget(IconeUI(nome="console", size_hint=(None, None), size=(dp(16), dp(16)), font_size="13sp", color=colors["success"]))
        term_header.add_widget(_label("Terminal Linux Kernel • iproute2", size="10sp", bold=True, color=colors["muted"]))
        self.calc_box_term.add_widget(term_header)

        self.calc_label_term = _label("", size="10sp", color=colors["text_secondary"], height=dp(88), auto_height=True)
        self.calc_box_term.add_widget(self.calc_label_term)
        card_conv.add_widget(self.calc_box_term)

        container.add_widget(card_conv)

        scroll.add_widget(container)
        Clock.schedule_once(lambda _dt: self._calcular_cidr(), 0)
        return scroll

    def _aplicar_exemplo_calc(self, ex: str):
        if hasattr(self, "calc_input"):
            self.calc_input.text = ex
            self._calcular_cidr()

    def _criar_tile_metrica(self, title: str, value: str, sub: str, cor_val) -> BoxLayout:
        colors = paleta_praticas()
        tile = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(70),
                         padding=(dp(12), dp(6)), spacing=dp(2))
        with tile.canvas.before:
            fill = Color(*colors["card"])
            bg = RoundedRectangle(pos=tile.pos, size=tile.size, radius=[dp(8)])
            Color(*colors["border"])
            b = Line(rounded_rectangle=(tile.x, tile.y, tile.width, tile.height, dp(8)), width=dp(1))
        tile.bind(
            pos=lambda item, val, s=bg, ln=b: (setattr(s, "pos", val), setattr(ln, "rounded_rectangle", (val[0], val[1], item.width, item.height, dp(8)))),
            size=lambda item, val, s=bg, ln=b: (setattr(s, "size", val), setattr(ln, "rounded_rectangle", (item.x, item.y, val[0], val[1], dp(8))))
        )
        lbl_t = Label(text=title.upper(), font_size="9sp", bold=True, color=colors["muted"],
                      size_hint_y=None, height=dp(14), halign="left", valign="middle")
        lbl_t.bind(size=lambda item, sz: setattr(item, "text_size", sz))
        tile.add_widget(lbl_t)

        lbl_v = Label(text=value, font_size="13sp", bold=True, color=cor_val,
                      size_hint_y=None, height=dp(24), halign="left", valign="middle")
        lbl_v.bind(size=lambda item, sz: setattr(item, "text_size", sz))
        tile.add_widget(lbl_v)

        lbl_s = Label(text=sub, font_size="10sp", color=colors["text_secondary"],
                      size_hint_y=None, height=dp(14), halign="left", valign="middle")
        lbl_s.bind(size=lambda item, sz: setattr(item, "text_size", sz))
        tile.add_widget(lbl_s)
        return tile

    def _calcular_cidr(self):
        colors = paleta_praticas()
        texto = self.calc_input.text.strip()
        try:
            rede = ipaddress.ip_network(texto, strict=False)
        except ValueError:
            self.calc_grid_metricas.clear_widgets()
            erro_box = _label("Endereço ou máscara inválida. Utilize notação CIDR válida (ex.: 192.168.10.0/24 ou 2001:db8::/64).",
                              size="12sp", color=colors["danger"], height=dp(40))
            self.calc_grid_metricas.add_widget(erro_box)
            return

        self.calc_grid_metricas.clear_widgets()

        if rede.version == 4:
            hosts = list(rede.hosts()) if rede.num_addresses <= 256 else None
            primeiro = hosts[0] if hosts else (rede.network_address if rede.prefixlen >= 31 else rede.network_address + 1)
            ultimo = hosts[-1] if hosts else (rede.broadcast_address if rede.prefixlen >= 31 else rede.broadcast_address - 1)
            hosts_uteis = max(0, rede.num_addresses - 2) if rede.prefixlen < 31 else rede.num_addresses
            escopo = "Privado (RFC 1918)" if rede.is_private else ("Loopback" if rede.is_loopback else "Público / Internet")

            self.calc_badge_resumo.children[0].text = f"IPv4 • /{rede.prefixlen} • {rede.num_addresses:,} IPs"

            # 6 tiles estruturados
            self.calc_grid_metricas.add_widget(self._criar_tile_metrica(
                "Endereço de Rede", f"{rede.network_address}/{rede.prefixlen}", "Primeiro IP • ID do segmento", colors["primary"]
            ))
            self.calc_grid_metricas.add_widget(self._criar_tile_metrica(
                "Máscara de Sub-rede", f"{rede.netmask}", f"Prefixo CIDR: /{rede.prefixlen}", colors["text"]
            ))
            self.calc_grid_metricas.add_widget(self._criar_tile_metrica(
                "Faixa de Hosts Úteis", f"{primeiro} ➔ {ultimo}", f"{hosts_uteis:,} hosts utilizáveis", colors["accent"]
            ))
            self.calc_grid_metricas.add_widget(self._criar_tile_metrica(
                "Endereço de Broadcast", f"{rede.broadcast_address}", "Último IP • Difusão na rede", colors["danger"]
            ))
            self.calc_grid_metricas.add_widget(self._criar_tile_metrica(
                "Máscara Curinga (Wildcard)", f"{rede.hostmask}", "Inverso da máscara (ACL / OSPF)", colors["text"]
            ))
            self.calc_grid_metricas.add_widget(self._criar_tile_metrica(
                "Escopo e Alocação", f"{escopo}", f"Total de {rede.num_addresses:,} IPs alocados", colors["success"]
            ))

            octetos_bin = " . ".join(f"{b:08b}" for b in rede.network_address.packed)
            mask_bin = " . ".join(f"{b:08b}" for b in rede.netmask.packed)
            octetos_hex = " . ".join(f"{b:02X}" for b in rede.network_address.packed)

            self.calc_label_bin.text = (
                f"Endereço de Rede em Binário:  {octetos_bin}\n"
                f"Máscara de Rede em Binário:   {mask_bin}\n"
                f"Endereço em Hexadecimal:      {octetos_hex}\n"
                f"Alocação de Bits no Endereço: {rede.prefixlen} bits de Rede (Net ID)  •  {32 - rede.prefixlen} bits de Host (Host ID)"
            )

            self.calc_label_term.text = (
                f"# 1. Configurar endereço e máscara na interface de rede:\n"
                f"ip addr add {rede.network_address + 1}/{rede.prefixlen} dev eth0\n"
                f"# 2. Ativar interface e adicionar rota do segmento de rede:\n"
                f"ip link set eth0 up && ip route add {rede.network_address}/{rede.prefixlen} dev eth0\n"
                f"# 3. Inspecionar endereços e rotas ativas no kernel Linux:\n"
                f"ip -br addr show dev eth0  &&  ip route show"
            )
        else:
            self.calc_badge_resumo.children[0].text = f"IPv6 • /{rede.prefixlen}"
            self.calc_grid_metricas.add_widget(self._criar_tile_metrica(
                "Endereço de Rede IPv6", f"{rede.network_address}/{rede.prefixlen}", "Prefixo Global de Roteamento", colors["primary"]
            ))
            self.calc_grid_metricas.add_widget(self._criar_tile_metrica(
                "Tamanho do Prefixo", f"/{rede.prefixlen} bits", f"Tamanho de Sub-rede padrão", colors["text"]
            ))
            self.calc_grid_metricas.add_widget(self._criar_tile_metrica(
                "Faixa Total de Alocação", f"{rede.network_address} ➔ {rede.broadcast_address}", "Espaço de endereçamento IPv6", colors["accent"]
            ))
            self.calc_grid_metricas.add_widget(self._criar_tile_metrica(
                "Escopo do Bloco", f"{'Privado / ULA' if rede.is_private else 'Global Unicast'}", "Padrão RFC 4193 / IANA", colors["success"]
            ))

            self.calc_label_bin.text = (
                f"Formato Expandido:  {rede.network_address.exploded}\n"
                f"Formato Comprimido: {rede.network_address.compressed}\n"
                f"Bits de Prefixo: /{rede.prefixlen}  |  Bits de Interface ID: {128 - rede.prefixlen}"
            )

            self.calc_label_term.text = (
                f"# 1. Atribuir endereço IPv6 na interface:\n"
                f"ip -6 addr add {rede.network_address}1/{rede.prefixlen} dev eth0\n"
                f"# 2. Visualizar endereços IPv6 ativos no terminal:\n"
                f"ip -6 -br addr show dev eth0"
            )


class LaboratorioDocker(BoxLayout):
    """Laboratório de rede local com dois containers Debian e consoles interativos."""

    def __init__(self, on_voltar, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(8), **kwargs)
        self.on_voltar = on_voltar
        self.docker_lab = DockerNetworkLab()
        self.terminal_server = None
        self._terminal_error = ""
        self._console_button = None

        try:
            app = App.get_running_app()
            self.terminal_server = getattr(app, "_terminal_web_server", None)
            if self.terminal_server is None:
                from service.web_terminal import TerminalWebServer

                self.terminal_server = TerminalWebServer(self.docker_lab)
                self.terminal_server.start()
                app._terminal_web_server = self.terminal_server
                app.browser_manager.register_resource_releaser(self.terminal_server.stop)
            else:
                self.terminal_server.set_docker_lab(self.docker_lab)
                self.terminal_server.start()
        except Exception as error:
            self._terminal_error = str(error)

        self.nos = {
            "A": {"nome": "PC-A", "interface": ipaddress.ip_interface("192.168.10.10/24")},
            "B": {"nome": "PC-B", "interface": ipaddress.ip_interface("192.168.10.20/24")},
        }
        self.statuses = {}
        self.titulos = {}
        self.terminal_addresses = {}
        self.terminal_statuses = {}
        self.enderecos = {}
        self._iniciando = False
        self._encerrando = False
        self._encerramento_pendente = None
        self._pronto = False

        self.add_widget(_header(
            self._voltar,
            "Rede Local com Containers Debian • Laboratório Docker",
            "Dois consoles executam comandos Bash reais em containers Debian conectados por uma rede de bridge interna.",
            icone="docker"
        ))

        # Configuração de IPs
        self.add_widget(self._montar_configuracao())

        # Controles Principais
        self.add_widget(self._montar_controles())

        # Botões de Ações Rápidas de Rede Real
        self.add_widget(self._montar_acoes_rapidas())

        # Cards dos Terminais e Comandos Recomendados
        grid_painel = GridLayout(cols=2, spacing=dp(10), size_hint=(1, 1))
        grid_painel.add_widget(self._montar_terminal("A"))
        grid_painel.add_widget(self._montar_terminal("B"))
        self.add_widget(grid_painel)

        # Guia Prático de Comandos
        card_guia = _card(padding=dp(8), spacing=dp(4))
        card_guia.height = dp(52)
        card_guia.add_widget(_label("Comandos práticos recomendados no terminal:", size="10sp", bold=True, color=paleta_praticas()["accent"], height=dp(18)))
        card_guia.add_widget(_label("• Teste de conectividade: ping -c 4 192.168.10.20   |   • Interfaces: ip a   |   • Captura: tcpdump -c 5 -i eth0",
                                    size="10sp", color=paleta_praticas()["muted"], height=dp(20)))
        self.add_widget(card_guia)

    def aplicar_tema(self):
        aplicar_tema_arvore(self)

    def _montar_configuracao(self):
        colors = paleta_praticas()
        area = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(106))
        for key in ("A", "B"):
            node = self.nos[key]
            card = _card(padding=dp(8), spacing=dp(4), elevated=True)
            card.height = dp(106)
            card.add_widget(_label(f"Endereçamento de {node['nome']}", size="11sp", bold=True, color=colors["text"], height=dp(20)))
            address = _campo("IPv4 com prefixo CIDR", "192.168.10.10/24", height=dp(32))
            address.input.text = str(node["interface"])
            self.enderecos[key] = address.input
            card.add_widget(address)
            status = _label("Aguardando início do laboratório.", size="9sp", color=colors["muted"], height=dp(16))
            self.statuses[key] = status
            card.add_widget(status)
            area.add_widget(card)
        return area

    def _montar_controles(self):
        colors = paleta_praticas()
        area = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        area.add_widget(_button("Iniciar / Aplicar IPs", self._iniciar, height=dp(36), font_size="10sp", icone="play"))

        self._console_button = _button("Abrir Terminais Interativos", self._abrir_terminais,
                                       variant="primary", height=dp(36), font_size="10sp", icone="open-in-new")
        self._console_button.disabled = True
        area.add_widget(self._console_button)

        area.add_widget(_button("Encerrar Laboratório", self._encerrar, variant="secondary",
                                height=dp(36), font_size="10sp", icone="stop"))

        self.status_lab = _label(
            self._terminal_error or "Inicie a rede para liberar os consoles Linux interativos.",
            size="9sp", color=colors["muted"], height=dp(36), valign="middle")
        area.add_widget(self.status_lab)
        return area

    def _montar_acoes_rapidas(self):
        row_acoes = GridLayout(cols=4, spacing=dp(8), size_hint_y=None, height=dp(34))
        row_acoes.add_widget(_button("⚡ Ping Real A➔B", lambda: self._executar_acao_rapida("ping -c 3 192.168.10.20", "Ping PC-A ➔ PC-B"), variant="secondary", height=dp(32), font_size="9sp", icone="network"))
        row_acoes.add_widget(_button("📡 Capturar tcpdump", lambda: self._executar_acao_rapida("timeout 3 tcpdump -c 3 -nn -XX -l -Z root -i eth0 2>&1", "Captura tcpdump PC-B", target_pc="B"), variant="secondary", height=dp(32), font_size="9sp", icone="file-document-outline"))
        row_acoes.add_widget(_button("📋 Tabela ARP (ip neigh)", lambda: self._executar_acao_rapida("ip neigh show", "Tabela ARP (PC-A)"), variant="secondary", height=dp(32), font_size="9sp", icone="format-list-bulleted"))
        row_acoes.add_widget(_button("🗺️ Rotas (ip route)", lambda: self._executar_acao_rapida("ip route show", "Tabela de Rotas (PC-A)"), variant="secondary", height=dp(32), font_size="9sp", icone="routes"))
        return row_acoes

    def _executar_acao_rapida(self, comando: str, titulo: str, target_pc="A"):
        colors = paleta_praticas()
        if not self._pronto:
            self.status_lab.text = "Inicie os containers antes de executar comandos rápidos."
            return
        self.status_lab.text = f"⚡ Executando '{titulo}' no container {target_pc}..."
        self.status_lab.color = colors["warning"]

        def worker():
            try:
                res = self.docker_lab.executar_comando(target_pc, comando)
                out = (res.stdout or res.stderr).strip()
                Clock.schedule_once(lambda _dt: self._on_acao_rapida_concluida(titulo, out), 0)
            except Exception as error:
                Clock.schedule_once(lambda _dt: self._on_acao_rapida_concluida(titulo, f"Erro: {error}"), 0)

        threading.Thread(target=worker, daemon=True).start()

    def _on_acao_rapida_concluida(self, titulo, out):
        colors = paleta_praticas()
        self.status_lab.text = f"[{titulo}]: {out[:120]}..."
        self.status_lab.color = colors["success"]

    def _montar_terminal(self, key):
        colors = paleta_praticas()
        node = self.nos[key]
        panel = _card(padding=dp(10), spacing=dp(6), elevated=False)
        heading = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        heading.add_widget(IconeUI(nome="console", size_hint=(None, None), size=(dp(24), dp(24)),
                                   font_size=dp(20), color=colors["accent"]))
        title = _label(node["nome"], size="13sp", bold=True, color=colors["text"], height=dp(26))
        heading.add_widget(title)
        self.titulos[key] = title
        panel.add_widget(heading)

        address = _label(f"IP: {node['interface'].ip}/{node['interface'].network.prefixlen}",
                         size="10sp", color=colors["primary"], bold=True, height=dp(20))
        self.terminal_addresses[key] = address
        panel.add_widget(address)

        status = _label("Aguardando início do container.", size="10sp", color=colors["muted"], height=dp(22))
        self.terminal_statuses[key] = status
        panel.add_widget(status)

        panel.add_widget(_label("Shell Bash Debian completo com TTY, comandos iproute2, ping, traceroute e tcpdump.",
                                size="10sp", color=colors["muted"], height=dp(42), valign="top"))
        return panel

    def _abrir_terminais(self):
        app = App.get_running_app()
        if not self._pronto:
            self.status_lab.text = "Inicie os containers antes de abrir os terminais."
            return
        if self.terminal_server is None:
            self.status_lab.text = self._terminal_error or "A interface de terminal não está disponível."
            return
        try:
            app.browser_manager.open_url(
                self.terminal_server.url,
                title="PM-Painel · Terminais de Redes I",
                app_mode=True,
                window_size=(1440, 900),
            )
            self.status_lab.text = "PC-A e PC-B abertos na janela de terminal interativo."
        except Exception as error:
            self.status_lab.text = f"Não foi possível abrir a janela do terminal: {error}"

    def _atualizar_titulos(self):
        for key, node in self.nos.items():
            self.titulos[key].text = node["nome"]
            self.terminal_addresses[key].text = f"IP: {node['interface'].ip}/{node['interface'].network.prefixlen}"

    def _iniciar(self):
        if self._iniciando or self._encerrando:
            return
        addresses = {key: self.enderecos[key].text.strip() for key in ("A", "B")}
        self._iniciando = True
        self._console_button.disabled = True
        self.status_lab.text = "Preparando a rede interna e containers Debian…"
        for key in ("A", "B"):
            self.statuses[key].text = "Conectando ao Docker…"
            self.terminal_statuses[key].text = "Preparando container…"

        def worker():
            try:
                message = self.docker_lab.iniciar(addresses)
                Clock.schedule_once(partial(self._inicio_concluido, addresses, message, None), 0)
            except Exception as error:
                Clock.schedule_once(partial(self._inicio_concluido, addresses, None, str(error)), 0)

        threading.Thread(target=worker, daemon=True, name="pm-painel-docker-start").start()

    def _inicio_concluido(self, addresses, message, error, _dt):
        self._iniciando = False
        if error:
            self._pronto = False
            self._console_button.disabled = True
            self.status_lab.text = error
            for key in ("A", "B"):
                self.statuses[key].text = "Container não iniciado."
                self.terminal_statuses[key].text = "Aguardando início do laboratório."
            self._processar_encerramento_pendente()
            return

        self._pronto = True
        self._console_button.disabled = not bool(self.terminal_server)
        for key in ("A", "B"):
            self.nos[key]["interface"] = ipaddress.ip_interface(addresses[key])
            self.statuses[key].text = "Container ativo • rede bridge"
            self.terminal_statuses[key].text = "Pronto para abrir o terminal interativo."
        self._atualizar_titulos()
        self.status_lab.text = message or "Laboratório ativo."
        if self.terminal_server is None and self._terminal_error:
            self.status_lab.text += f" Interface xterm indisponível: {self._terminal_error}"
        self._processar_encerramento_pendente()

    def _processar_encerramento_pendente(self):
        if self._encerramento_pendente is not None:
            navegar = self._encerramento_pendente
            self._encerramento_pendente = None
            Clock.schedule_once(lambda _dt: self._encerrar_async(navegar=navegar), 0)

    def _encerrar(self):
        self._encerrar_async(navegar=False)

    def _voltar(self):
        self._encerrar_async(navegar=True)

    def _encerrar_async(self, *, navegar):
        if self._encerrando:
            return
        if self._iniciando:
            self._encerramento_pendente = navegar
            self.status_lab.text = "Aguarde a inicialização terminar; depois o laboratório será encerrado."
            return
        self._encerrando = True
        self._console_button.disabled = True
        self.status_lab.text = "Encerrando containers e rede interna…"

        def worker():
            try:
                message = self.docker_lab.encerrar()
                error = None
            except Exception as exception:
                message = None
                error = str(exception)
            Clock.schedule_once(partial(self._encerramento_concluido, message, error, navegar), 0)

        threading.Thread(target=worker, daemon=True, name="pm-painel-docker-stop").start()

    def _encerramento_concluido(self, message, error, navegar, _dt):
        self._encerrando = False
        self._pronto = False
        self._console_button.disabled = True
        for key in ("A", "B"):
            self.statuses[key].text = "Container encerrado." if not error else "Estado do Docker não confirmado."
            self.terminal_statuses[key].text = "Aguardando início do laboratório."
        self.status_lab.text = error or message or "Laboratório encerrado."
        if navegar:
            self.on_voltar()
