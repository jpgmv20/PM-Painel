"""Laboratórios interativos e práticos de Redes I, Modelo OSI, Roteamento e DNS com integração Docker."""
from __future__ import annotations

import binascii
import ipaddress
import random
import re
import threading
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from model.componentes import BotaoAcao, CampoTexto, IconeUI
from model.redes_hud import (
    DrawerDumpBruto,
    PlayerPassoAPasso,
    PalcoAnimadoDNS,
    PalcoAnimadoOSI,
    PalcoAnimadoRoteamento,
    construir_visualizador_bits_ipv4,
    criar_botao,
    criar_card,
    criar_chip_dado,
    criar_kpi_tile,
    criar_label,
    criar_pill,
)
from model.tema_praticas import (
    aplicar_tema_arvore,
    paleta_praticas,
    registrar_cor_texto,
    registrar_fundo,
    tema_escuro,
)
from service.docker_service import DockerService
from service.network_lab_docker import DockerNetworkLab


def _bloco_pdu(titulo: str, subtitulo: str, cor_titulo, height=dp(52), destaque: bool = False):
    """Bloco proporcional representando um cabeçalho/seção dentro do Frame Ethernet."""
    colors = paleta_praticas()
    bloco = BoxLayout(
        orientation="vertical",
        size_hint_y=None,
        height=height,
        padding=(dp(6), dp(4)),
        spacing=dp(1),
    )
    with bloco.canvas.before:
        fill = Color(*colors["card_elevated" if destaque else "card"])
        bg = RoundedRectangle(pos=bloco.pos, size=bloco.size, radius=[dp(8)])
        bd_col = Color(*(cor_titulo if destaque else colors["border"]))
        border = Line(
            rounded_rectangle=(bloco.x, bloco.y, bloco.width, bloco.height, dp(8)),
            width=dp(1.6 if destaque else 1.0),
        )
    registrar_fundo(bloco, fill, "card_elevated" if destaque else "card")
    bloco.bind(
        pos=lambda item, value, s=bg, b=border: (
            setattr(s, "pos", value),
            setattr(b, "rounded_rectangle", (value[0], value[1], item.width, item.height, dp(8))),
        ),
        size=lambda item, value, s=bg, b=border: (
            setattr(s, "size", value),
            setattr(b, "rounded_rectangle", (item.x, item.y, value[0], value[1], dp(8))),
        ),
    )

    lbl_top = Label(
        text=titulo,
        bold=True,
        font_size="9.5sp",
        color=cor_titulo,
        halign="center",
        valign="middle",
        size_hint=(1, 0.55),
    )
    lbl_top.bind(size=lambda item, val: setattr(item, "text_size", val))

    lbl_sub = Label(
        text=subtitulo,
        font_size="8.5sp",
        color=colors["muted"],
        halign="center",
        valign="middle",
        size_hint=(1, 0.45),
    )
    lbl_sub.bind(size=lambda item, val: setattr(item, "text_size", val))

    bloco.add_widget(lbl_top)
    bloco.add_widget(lbl_sub)
    bloco._bd_col = bd_col
    bloco._cor_titulo = cor_titulo
    return bloco


def _campo(rotulo: str, dica: str, *, appearance="light", multiline=False, height=dp(38)):
    wrapper = BoxLayout(orientation="vertical", spacing=dp(3), size_hint_y=None, height=height + dp(23))
    wrapper.add_widget(criar_label(rotulo, size="10sp", color=paleta_praticas()["muted"], bold=True, height=dp(18), role="muted"))
    wrapper.input = CampoTexto(
        hint_text=dica,
        appearance="dark" if tema_escuro() else appearance,
        multiline=multiline,
        size_hint_y=None,
        height=height,
        font_size="11sp",
    )
    wrapper.input._tema_aparencia = True
    wrapper.add_widget(wrapper.input)
    return wrapper


def _header(voltar, titulo: str, subtitulo: str, icone: str = "lan"):
    colors = paleta_praticas()
    area = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(70))
    bar = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(10))

    btn_voltar = criar_botao(
        "Voltar para Redes I", voltar, variant="secondary", height=dp(36), icone="arrow-left", width=dp(178)
    )
    bar.add_widget(btn_voltar)

    bar.add_widget(
        IconeUI(nome=icone, size_hint=(None, None), size=(dp(30), dp(36)), font_size=dp(24), color=colors["accent"])
    )
    lbl_title = criar_label(titulo, size="17sp", color=colors["text"], bold=True, height=dp(36), role="text")
    lbl_title.size_hint_x = 1
    bar.add_widget(lbl_title)

    badge = criar_pill("LABORATÓRIO PRÁTICO", colors["tag_bg"], colors["accent"], "flask-outline", height=dp(26))
    bar.add_widget(badge)

    area.add_widget(bar)
    desc_label = criar_label(subtitulo, size="11sp", color=colors["muted"], height=dp(22), role="muted")
    area.add_widget(desc_label)
    return area


class _BotaoCamadaInterativo(BoxLayout):
    """Linha HUD interativa para inspecionar uma camada OSI e saltar o vídeo para ela."""

    def __init__(self, on_select, **kwargs):
        super().__init__(**kwargs)
        self._on_select = on_select

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and callable(self._on_select):
            self._on_select()
            return True
        return super().on_touch_down(touch)


class LaboratorioEnderecoIP(BoxLayout):
    """Laboratório interativo de Redes I com HUD limpo e animações passo a passo:
    Encapsulamento OSI, Roteamento Bitwise AND, Resolução DNS e Calculadora CIDR.
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
            "ip_dest": "192.168.10.20",
            "mac_orig": "02:42:C0:A8:0A:0A",
            "mac_dest": "02:42:C0:A8:0A:14",
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

    PRESETS_DNS = (
        ("pm-painel.local", "A"),
        ("www.google.com", "A"),
        ("mail.empresa.com.br", "MX"),
        ("cdn.app.io", "CNAME"),
        ("pc-b.redes.lab", "AAAA"),
    )

    def __init__(self, on_voltar, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(8), **kwargs)
        self.on_voltar = on_voltar
        self._aba_ativa = "osi"  # 'osi', 'roteamento', 'dns', 'calculadora'

        self._preset_atual = "http"
        self._dns_dominio_atual = "pm-painel.local"
        self._dns_tipo_atual = "A"
        self._dns_autoplay_pendente = False

        self.docker_service = DockerService()
        self.docker_lab = DockerNetworkLab()
        self._docker_ativo = False
        self._lab_pronto = False
        self._iniciando_docker = False
        self._macs_reais = {"A": "02:42:C0:A8:0A:0A", "B": "02:42:C0:A8:0A:14"}
        self._ips_reais = {"A": "192.168.10.10", "B": "192.168.10.20"}
        self._dados_experimento_osi: dict = {}
        self._ultimo_ping_simulacao: dict = {}

        self.add_widget(_header(
            self.on_voltar,
            "Bancada Prática de Redes I & Modelo OSI",
            "Visualização HUD sem poluição visual + animações passo a passo de Modelo OSI, Roteamento, DNS e CIDR.",
            icone="lan-connect",
        ))

        self._barra_docker = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
        self.add_widget(self._barra_docker)
        self._atualizar_barra_docker()

        self._barra_abas = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        self.add_widget(self._barra_abas)

        self._area_conteudo = BoxLayout(orientation="vertical", size_hint=(1, 1))
        self.add_widget(self._area_conteudo)

        self._atualizar_abas()
        threading.Thread(target=self._verificar_docker_background, daemon=True).start()

    def aplicar_tema(self):
        aplicar_tema_arvore(self)
        self._atualizar_abas()

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
                    self._ips_reais = self.docker_lab.obter_ips()
                    for p in self.PRESETS_PACOTE.values():
                        p["mac_orig"] = self._macs_reais.get("A", "02:42:C0:A8:0A:0A")
                        p["mac_dest"] = self._macs_reais.get("B", "02:42:C0:A8:0A:14")
                        p["ip_orig"] = self._ips_reais.get("A", "192.168.10.10")
                        p["ip_dest"] = self._ips_reais.get("B", "192.168.10.20")
            Clock.schedule_once(lambda _dt: self._atualizar_barra_docker(), 0)
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
            mac_a_curto = self._macs_reais.get("A", "PC-A")[-8:]
            mac_b_curto = self._macs_reais.get("B", "PC-B")[-8:]
            self._barra_docker.add_widget(
                criar_pill("DOCKER ENGINE REAL: ATIVO", colors["success_bg"], colors["success"], "docker", height=dp(26))
            )
            self._barra_docker.add_widget(
                criar_pill("LAN BRIDGE: 192.168.10.0/24", colors["tag_bg"], colors["accent"], "lan-connect", height=dp(26))
            )
            self._barra_docker.add_widget(
                criar_pill(f"PC-A ({mac_a_curto}) ↔ PC-B ({mac_b_curto})", colors["tag_bg"], colors["muted"], "lan", height=dp(26))
            )
            self._barra_docker.add_widget(
                criar_pill("DADOS REAIS + ANIMAÇÕES", colors["tag_bg"], colors["primary"], "play", height=dp(26))
            )
        elif self._iniciando_docker:
            self._barra_docker.add_widget(
                criar_pill("INICIANDO DOCKER DESKTOP... AGUARDE", colors["tag_bg"], colors["warning"], "refresh", height=dp(26))
            )
        elif self._docker_ativo:
            self._barra_docker.add_widget(
                criar_pill("PREPARANDO CONTAINERS DEBIAN EM BACKGROUND...", colors["tag_bg"], colors["warning"], "refresh", height=dp(26))
            )
        else:
            self._barra_docker.add_widget(
                criar_pill("MODO SIMULAÇÃO LOCAL (DOCKER OFFLINE)", colors["tag_bg"], colors["muted"], "layers-outline", height=dp(26))
            )
            btn_start = criar_botao(
                "Iniciar Docker Desktop para Dados Reais",
                self._iniciar_docker_desktop,
                variant="secondary",
                height=dp(26),
                font_size="9.5sp",
                icone="docker",
                width=dp(270),
            )
            self._barra_docker.add_widget(btn_start)

    def _trocar_aba(self, nova_aba: str):
        if self._aba_ativa != nova_aba:
            self._aba_ativa = nova_aba
            self._atualizar_abas()

    def _atualizar_abas(self):
        self._barra_abas.clear_widgets()
        abas = (
            ("osi", "Encapsulamento OSI", "package-variant-closed"),
            ("roteamento", "Roteamento & Máscaras", "routes"),
            ("dns", "Resolução DNS", "dns"),
            ("calculadora", "Calculadora CIDR & IP", "calculator-variant"),
        )
        for chave, titulo, icone in abas:
            ativa = self._aba_ativa == chave
            btn = criar_botao(
                titulo,
                partial(self._trocar_aba, chave),
                variant="primary" if ativa else "secondary",
                height=dp(36),
                icone=icone,
                font_size="11sp",
            )
            self._barra_abas.add_widget(btn)

        self._area_conteudo.clear_widgets()
        if self._aba_ativa == "osi":
            self._area_conteudo.add_widget(self._montar_tela_osi())
        elif self._aba_ativa == "roteamento":
            self._area_conteudo.add_widget(self._montar_tela_roteamento())
        elif self._aba_ativa == "dns":
            self._area_conteudo.add_widget(self._montar_tela_dns())
        elif self._aba_ativa == "calculadora":
            self._area_conteudo.add_widget(self._montar_tela_calculadora())

    # =========================================================================
    # ABA 1: SIMULADOR ANIMADO DE ENCAPSULAMENTO OSI (HUD + VÍDEO PASSO A PASSO)
    # =========================================================================

    def _passos_osi(self, preset: dict, dados_reais: dict | None = None) -> list[dict]:
        proto_l4 = preset["transporte"]
        proto_num = 6 if proto_l4 == "TCP" else (17 if proto_l4 == "UDP" else 1)
        payload_curto = preset["payload"].replace("\r\n", " ")[:48]
        utf8_hex = binascii.hexlify(preset["payload"][:10].encode()).decode()
        bits_prev = "".join(f"{b:08b} " for b in preset["payload"][:4].encode()).strip()

        ip_o = (dados_reais or {}).get("ip_orig") or preset["ip_orig"]
        ip_d = (dados_reais or {}).get("ip_dest") or preset["ip_dest"]
        mac_o = (dados_reais or {}).get("mac_orig") or preset["mac_orig"]
        mac_d = (dados_reais or {}).get("mac_dest") or preset["mac_dest"]
        p_dest = (dados_reais or {}).get("porta_dest") or preset["porta_dest"]
        status_final = (dados_reais or {}).get("status") or ("200 OK / Recebido" if proto_l4 != "ICMP" else "Echo Reply OK")
        rtt_val = (dados_reais or {}).get("rtt") or "0.14 ms"
        detalhe_final = (dados_reais or {}).get("detalhes") or (
            f"Processo {preset['app_proto']} validou a entrega na porta {p_dest} com sucesso."
        )
        cripto_txt = "TLS 1.3 (AES-GCM)" if "TLS" in preset["payload"] else "Texto Claro (UTF-8)"

        return [
            {
                "curto": "1. C7-C5 App",
                "badge": "PASSO 1/8 • CAMADAS 7, 6 e 5 (PC-A)",
                "titulo": f"Geração de Dados ({preset['app_proto']}), Apresentação e Sessão",
                "resumo": (
                    f"No transmissor PC-A, a aplicação gera o payload '{payload_curto}'. "
                    f"A Camada 6 aplica codificação {cripto_txt} e a Camada 5 abre o canal Full-Duplex (#48291)."
                ),
                "cor": "success",
                "dados": [
                    ("Protocolo L7", preset["app_proto"], "success"),
                    ("Codificação C6", f"{utf8_hex}...", "info"),
                    ("Sessão C5", "#48291 Full-Duplex", "accent"),
                ],
                "anim": {
                    "lado": "A",
                    "camada": 7,
                    "acao": "C7-C5 • CRIANDO DADOS NA ORIGEM",
                    "pkt_label": "Dados L7",
                    "pdu_blocos": [("DADOS APP", "success")],
                    "wire_info": "Camadas superiores preparando payload antes do transporte",
                },
            },
            {
                "curto": "2. C4 Transp",
                "badge": "PASSO 2/8 • CAMADA 4 TRANSPORTE (PC-A)",
                "titulo": f"Segmentação {proto_l4} e Endereçamento por Portas",
                "resumo": (
                    f"A Camada 4 encapsula os dados adicionando cabeçalho {proto_l4}. "
                    f"Define Porta Origem {preset['porta_orig']} -> Destino {p_dest} e calcula o Checksum de integridade."
                ),
                "cor": "warning",
                "dados": [
                    ("Transporte", proto_l4, "warning"),
                    ("Portas", f"{preset['porta_orig']} ➔ {p_dest}", "accent"),
                    ("Integridade", "Checksum L4 OK", "success"),
                ],
                "anim": {
                    "lado": "A",
                    "camada": 4,
                    "acao": f"C4 • ANEXANDO CABEÇALHO {proto_l4}",
                    "pkt_label": "Segmento L4",
                    "pdu_blocos": [(proto_l4, "warning"), ("DADOS", "success")],
                    "wire_info": f"PDU agora chamada Segmento/Datagrama ({proto_l4})",
                },
            },
            {
                "curto": "3. C3 Rede",
                "badge": "PASSO 3/8 • CAMADA 3 REDE (PC-A)",
                "titulo": "Empacotamento IPv4 e Atribuição de TTL",
                "resumo": (
                    f"A Camada 3 encapsula o segmento em um Pacote IPv4 de {ip_o} para {ip_d}, "
                    f"define TTL=64 (limite de saltos) e marca Protocolo L4 = {proto_num}."
                ),
                "cor": "primary",
                "dados": [
                    ("IPv4 Origem", ip_o, "primary"),
                    ("IPv4 Destino", ip_d, "accent"),
                    ("TTL / Proto", f"TTL 64 • Proto {proto_num}", "info"),
                ],
                "anim": {
                    "lado": "A",
                    "camada": 3,
                    "acao": "C3 • ADICIONANDO CABEÇALHO IPv4",
                    "pkt_label": "Pacote IP",
                    "pdu_blocos": [("IPv4", "primary"), (proto_l4, "warning"), ("DADOS", "success")],
                    "wire_info": f"Roteamento lógico: {ip_o} ➔ {ip_d}",
                },
            },
            {
                "curto": "4. C2 Enlace",
                "badge": "PASSO 4/8 • CAMADA 2 ENLACE (PC-A)",
                "titulo": "Montagem do Quadro Ethernet II e Trailer CRC-32",
                "resumo": (
                    f"A Camada 2 adiciona os endereços físicos MAC ({mac_o[-8:]} ➔ {mac_d[-8:]}), "
                    "EtherType 0x0800 (IPv4) e calcula o trailer FCS CRC-32 de 4 bytes ao final do quadro."
                ),
                "cor": "accent",
                "dados": [
                    ("MAC Origem", mac_o, "accent"),
                    ("MAC Destino", mac_d, "accent"),
                    ("Frame Check", "0x0800 + CRC-32", "danger"),
                ],
                "anim": {
                    "lado": "A",
                    "camada": 2,
                    "acao": "C2 • MONTANDO QUADRO ETHERNET II",
                    "pkt_label": "Quadro L2",
                    "pdu_blocos": [("MAC", "accent"), ("IP", "primary"), (proto_l4, "warning"), ("DADOS", "success"), ("FCS", "danger")],
                    "wire_info": "Quadro pronto com cabeçalho MAC + trailer CRC-32",
                },
            },
            {
                "curto": "5. C1 Fio",
                "badge": "PASSO 5/8 • CAMADA 1 FÍSICA (MEIO DE TRANSMISSÃO)",
                "titulo": "Modulação em Fluxo de Bits e Travessia até PC-B",
                "resumo": (
                    f"A placa de rede converte o quadro completo em pulsos binários ({bits_prev}...) "
                    "e transmite pelo meio físico (bridge Ethernet virtual entre os containers)."
                ),
                "cor": "danger",
                "dados": [
                    ("Fluxo Binário", f"{bits_prev}...", "danger"),
                    ("Meio Físico", "eth0 • Bridge LAN", "accent"),
                    ("Direção", "PC-A ➔ PC-B", "success"),
                ],
                "anim": {
                    "lado": "wire",
                    "camada": 1,
                    "acao": "C1 • TRANSMITINDO BITS NO CABO",
                    "pkt_label": "010011...",
                    "pdu_blocos": [("BITS 0/1 NO MEIO FÍSICO (PREÂMBULO + QUADRO)", "danger")],
                    "wire_info": f"Pulsos binários atravessando a bridge: {bits_prev}",
                },
            },
            {
                "curto": "6. RX C2",
                "badge": "PASSO 6/8 • DESENCAPSULAMENTO ENLACE (PC-B)",
                "titulo": "Validação de MAC Destino e CRC-32 em PC-B",
                "resumo": (
                    f"A interface eth0 de PC-B detecta o preâmbulo, confirma seu MAC ({mac_d[-8:]}), "
                    "valida o CRC-32 sem erros e remove o cabeçalho Ethernet II entregando o Pacote IP à Camada 3."
                ),
                "cor": "accent",
                "dados": [
                    ("MAC Validado", mac_d, "success"),
                    ("CRC-32", "Válido (0 erros)", "success"),
                    ("Ação C2", "Remove Header MAC", "accent"),
                ],
                "anim": {
                    "lado": "B",
                    "camada": 2,
                    "acao": "PC-B (C2) • VALIDANDO MAC E CRC-32",
                    "pkt_label": "Remove L2",
                    "pdu_blocos": [("IPv4", "primary"), (proto_l4, "warning"), ("DADOS", "success")],
                    "wire_info": "Quadro Ethernet II desencapsulado em PC-B",
                },
            },
            {
                "curto": "7. RX C3",
                "badge": "PASSO 7/8 • DESENCAPSULAMENTO REDE (PC-B)",
                "titulo": "Conferência de IPv4 Destino e Decréscimo de TTL",
                "resumo": (
                    f"O kernel de PC-B verifica o IP destino {ip_d}, decrementa o TTL (64 -> 63) "
                    f"e despacha o segmento para o protocolo {proto_l4} na Camada 4."
                ),
                "cor": "primary",
                "dados": [
                    ("IP Destino", f"{ip_d} OK", "success"),
                    ("TTL / Proto", f"63 • L4={proto_num}", "info"),
                    ("Ação C3", "Remove Header IP", "primary"),
                ],
                "anim": {
                    "lado": "B",
                    "camada": 3,
                    "acao": "PC-B (C3) • VALIDANDO IP E TTL",
                    "pkt_label": "Remove IP",
                    "pdu_blocos": [(proto_l4, "warning"), ("DADOS", "success")],
                    "wire_info": "Cabeçalho IPv4 removido; segmento segue para L4",
                },
            },
            {
                "curto": "8. RX OK!",
                "badge": "PASSO 8/8 • ENTREGA FINAL C4 -> C7 (PC-B)",
                "titulo": f"Entrega Concluída: {status_final}",
                "resumo": (
                    f"A Camada 4 entrega na porta {p_dest} ({proto_l4}) e as camadas superiores (C5-C7) "
                    f"processam a requisição. {detalhe_final}"
                ),
                "cor": "success",
                "dados": [
                    ("Resultado", status_final, "success"),
                    ("Porta / Proto", f"{proto_l4} :{p_dest}", "accent"),
                    ("Latência RTT", rtt_val, "primary"),
                ],
                "anim": {
                    "lado": "B",
                    "camada": 7,
                    "acao": f"C7 • ENTREGUE COM SUCESSO ({status_final})",
                    "pkt_label": "Entregue OK",
                    "pdu_blocos": [(f"PAYLOAD {preset['app_proto']} ENTREGUE", "success")],
                    "wire_info": f"Comunicação concluída em {rtt_val}",
                },
            },
        ]

    def _montar_tela_osi(self):
        colors = paleta_praticas()
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5), scroll_type=["bars", "content"])
        container = GridLayout(cols=1, spacing=dp(10), padding=(dp(2), dp(4)), size_hint_y=None)
        container.bind(minimum_height=container.setter("height"))

        preset = self.PRESETS_PACOTE[self._preset_atual]
        dados_reais = self._dados_experimento_osi if self._dados_experimento_osi.get("_preset") == self._preset_atual else None

        # 1. Gerador de Pacotes e Frame Layout
        card_presets = criar_card(padding=dp(12), spacing=dp(8))
        header_presets = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        header_presets.add_widget(criar_label("1. Gerador de Tráfego & Estrutura do Quadro", size="13sp", bold=True, color=colors["text"]))
        header_presets.add_widget(Widget())

        payload_bytes = len(preset["payload"].encode("utf-8"))
        header_transp_bytes = 20 if preset["transporte"] == "TCP" else (8 if preset["transporte"] == "UDP" else 0)
        total_bytes = 14 + 20 + header_transp_bytes + payload_bytes + 4

        header_presets.add_widget(criar_pill(preset["transporte"], colors["tag_bg"], colors["accent"]))
        header_presets.add_widget(criar_pill(f"{total_bytes} BYTES • MTU 1500", colors["success_bg"], colors["success"], "package-variant-closed"))
        card_presets.add_widget(header_presets)

        row_chips = GridLayout(cols=5, spacing=dp(6), size_hint_y=None, height=dp(34))
        for key, p in self.PRESETS_PACOTE.items():
            selecionado = key == self._preset_atual
            row_chips.add_widget(
                criar_botao(
                    p["nome"],
                    partial(self._selecionar_preset_osi, key),
                    variant="primary" if selecionado else "secondary",
                    height=dp(32),
                    font_size="10sp",
                )
            )
        card_presets.add_widget(row_chips)

        # Barra HUD resumo do contexto (sem bloco longo de texto)
        ctx_hud = GridLayout(cols=3, spacing=dp(6), size_hint_y=None, height=dp(30))
        ctx_hud.add_widget(criar_chip_dado("Aplicação", preset["app_proto"], "success"))
        ctx_hud.add_widget(criar_chip_dado("Origem -> Destino", f"{preset['ip_orig']}:{preset['porta_orig']} ➔ {preset['ip_dest']}:{preset['porta_dest']}", "primary"))
        ctx_hud.add_widget(criar_chip_dado("Resumo", preset["descricao"], "accent"))
        card_presets.add_widget(ctx_hud)

        # Blocos proporcionais do Frame Ethernet
        transp_cor = colors["warning"]
        self._osi_frame_blocos: dict[int, BoxLayout] = {}
        layout_blocos = GridLayout(cols=5, spacing=dp(8), size_hint_y=None, height=dp(50))
        b_l2 = _bloco_pdu("Ethernet II (L2)", "14 bytes • MAC", colors["accent"])
        b_l3 = _bloco_pdu("IPv4 Header (L3)", "20 bytes • TTL 64", colors["primary"])
        b_l4 = _bloco_pdu(f"{preset['transporte']} Header (L4)", f"{header_transp_bytes} bytes", transp_cor)
        b_app = _bloco_pdu(f"Payload ({preset['app_proto']})", f"{payload_bytes} bytes dados", colors["success"])
        b_fcs = _bloco_pdu("FCS Trailer (C2/C1)", "4 bytes CRC-32", colors["danger"])
        self._osi_frame_blocos = {2: b_l2, 3: b_l3, 4: b_l4, 7: b_app, 1: b_fcs}
        for b in (b_l2, b_l3, b_l4, b_app, b_fcs):
            layout_blocos.add_widget(b)
        card_presets.add_widget(layout_blocos)

        texto_btn = (
            "Transmitir Pacote Real no Docker (tcpdump) & Iniciar Vídeo Passo a Passo"
            if self._lab_pronto
            else "Transmitir Pacote & Iniciar Vídeo Animado Passo a Passo"
        )
        card_presets.add_widget(
            criar_botao(
                texto_btn,
                self._transmitir_pacote_osi,
                variant="primary",
                height=dp(38),
                font_size="11sp",
                icone="docker" if self._lab_pronto else "play",
            )
        )
        container.add_widget(card_presets)

        # 2. HUD Telemetria + Palco Animado OSI + Player Estilo Vídeo
        card_anim = criar_card(padding=dp(12), spacing=dp(8), elevated=True)
        hdr_anim = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        hdr_anim.add_widget(criar_label("2. Simulação Animada do Encapsulamento OSI (Passo a Passo)", size="13sp", bold=True, color=colors["text"]))
        hdr_anim.add_widget(Widget())
        self._osi_modo_pill = criar_pill(
            "DOCKER REAL PRONTO" if dados_reais else ("PRONTO P/ TRANSMITIR" if self._lab_pronto else "SIMULAÇÃO INTERATIVA"),
            colors["success_bg"] if dados_reais else colors["tag_bg"],
            colors["success"] if dados_reais else colors["accent"],
        )
        hdr_anim.add_widget(self._osi_modo_pill)
        card_anim.add_widget(hdr_anim)

        # 4 KPIs HUD substituindo o textão do osi_log_label
        kpi_row = GridLayout(cols=4, spacing=dp(8), size_hint_y=None, height=dp(64))
        self._osi_kpi_status = criar_kpi_tile(
            "Status da Execução",
            (dados_reais or {}).get("status", "Pronto"),
            "Container Debian PC-B" if self._lab_pronto else "Simulador Local OSI",
            "success" if dados_reais else "accent",
        )
        self._osi_kpi_rtt = criar_kpi_tile(
            "Latência (RTT)",
            (dados_reais or {}).get("rtt", "-- ms"),
            "Tempo ida e volta",
            "primary",
        )
        self._osi_kpi_ttl = criar_kpi_tile(
            "TTL / Transporte",
            f"TTL {(dados_reais or {}).get('ttl', 64)} • {preset['transporte']}",
            f"Porta dest: {preset['porta_dest']}",
            "warning",
        )
        self._osi_kpi_fluxo = criar_kpi_tile(
            "Fluxo IP / MAC",
            f"{preset['ip_orig'][-5:]} ➔ {preset['ip_dest'][-5:]}",
            f"MAC: {preset['mac_orig'][-5:]} ➔ {preset['mac_dest'][-5:]}",
            "info",
        )
        for kpi in (self._osi_kpi_status, self._osi_kpi_rtt, self._osi_kpi_ttl, self._osi_kpi_fluxo):
            kpi_row.add_widget(kpi)
        card_anim.add_widget(kpi_row)

        palco_osi = PalcoAnimadoOSI()
        self._osi_camada_cards: dict[int, tuple] = {}
        self._osi_player = PlayerPassoAPasso(
            palco_osi,
            intervalo_autoplay=2.7,
            on_step_change=self._ao_mudar_passo_osi,
        )
        card_anim.add_widget(self._osi_player)

        # Drawer recolhível para dump tcpdump / dig sem poluir a tela
        self._osi_dump_drawer = DrawerDumpBruto(
            titulo="Captura Real do Kernel / tcpdump -XX (Opcional)",
            icone="code-tags",
        )
        if dados_reais and dados_reais.get("frame_dump"):
            self._osi_dump_drawer.definir_conteudo(dados_reais["frame_dump"], badge_texto="Capturado Docker")
        else:
            self._osi_dump_drawer.definir_conteudo(
                "Clique em 'Transmitir Pacote' acima para capturar os bytes reais do quadro na interface eth0.",
                badge_texto="Aguardando",
            )
        card_anim.add_widget(self._osi_dump_drawer)
        container.add_widget(card_anim)

        # 3. Inspeção Estruturada das 7 Camadas (HUD Limpo + Clique para Pular)
        card_camadas = criar_card(padding=dp(12), spacing=dp(6))
        hdr_cam = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        hdr_cam.add_widget(criar_label("3. Inspeção HUD das 7 Camadas OSI (Clique em uma camada para pular para ela)", size="13sp", bold=True, color=colors["text"]))
        hdr_cam.add_widget(Widget())
        hdr_cam.add_widget(criar_pill("Sincronizado com Vídeo", colors["tag_bg"], colors["muted"]))
        card_camadas.add_widget(hdr_cam)

        proto_num = 6 if preset["transporte"] == "TCP" else (17 if preset["transporte"] == "UDP" else 1)
        utf8_hex = binascii.hexlify(preset["payload"][:12].encode()).decode()
        bits_str = "".join(f"{b:08b} " for b in preset["payload"][:4].encode()).strip()
        camadas_spec = [
            (7, "Aplicação", "Dados", "success", 0, [
                ("Protocolo", preset["app_proto"], "success"),
                ("Payload", preset["payload"].replace("\r\n", " ")[:36], "text"),
            ]),
            (6, "Apresentação", "Codificação", "success", 0, [
                ("UTF-8 Hex", f"{utf8_hex}...", "info"),
                ("Criptografia", "Ativa (TLS 1.3)" if "TLS" in preset["payload"] else "Texto Claro", "success"),
            ]),
            (5, "Sessão", "Diálogo", "info", 0, [
                ("Sessão ID", "#48291", "info"),
                ("Controle", "Full-Duplex • Sincronizado", "text"),
            ]),
            (4, "Transporte", "Segmento", "warning", 1, [
                ("Protocolo", preset["transporte"], "warning"),
                ("Portas", f"{preset['porta_orig']} ➔ {preset['porta_dest']}", "accent"),
                ("Checksum L4", "OK", "success"),
            ]),
            (3, "Rede", "Pacote IP", "primary", 2, [
                ("IPv4", f"{preset['ip_orig']} ➔ {preset['ip_dest']}", "primary"),
                ("TTL / L4", f"64 • Proto {proto_num}", "info"),
            ]),
            (2, "Enlace", "Quadro/Frame", "accent", 3, [
                ("MAC", f"{preset['mac_orig'][-8:]} ➔ {preset['mac_dest'][-8:]}", "accent"),
                ("EtherType", "0x0800 • FCS CRC-32", "danger"),
            ]),
            (1, "Física", "Bits no Meio", "danger", 4, [
                ("Sinalização", f"{bits_str}...", "danger"),
                ("Meio", "Pulsos elétricos • Bridge eth0", "muted"),
            ]),
        ]

        for num, nome, pdu, role, step_idx, chips in camadas_spec:
            row_card = _BotaoCamadaInterativo(
                partial(self._saltar_para_camada_osi, step_idx),
                size_hint_y=None,
                height=dp(38),
                spacing=dp(8),
                padding=(dp(8), dp(4)),
            )
            with row_card.canvas.before:
                r_fill = Color(*colors["panel"])
                r_bg = RoundedRectangle(pos=row_card.pos, size=row_card.size, radius=[dp(8)])
                r_bd_col = Color(*colors["border"])
                r_bd = Line(rounded_rectangle=(row_card.x, row_card.y, row_card.width, row_card.height, dp(8)), width=dp(1))
            registrar_fundo(row_card, r_fill, "panel")
            row_card.bind(
                pos=lambda w, v, s=r_bg, b=r_bd: (setattr(s, "pos", v), setattr(b, "rounded_rectangle", (v[0], v[1], w.width, w.height, dp(8)))),
                size=lambda w, v, s=r_bg, b=r_bd: (setattr(s, "size", v), setattr(b, "rounded_rectangle", (w.x, w.y, v[0], v[1], dp(8)))),
            )

            badge_num = criar_pill(f"C{num}", colors["tag_bg"], colors[role], height=dp(26), fixed_width=dp(42))
            badge_pdu = criar_pill(f"{nome} · {pdu}", colors["tag_bg"], colors["text"], height=dp(26), fixed_width=dp(168))
            badge_num.pos_hint = {"center_y": 0.5}
            badge_pdu.pos_hint = {"center_y": 0.5}
            row_card.add_widget(badge_num)
            row_card.add_widget(badge_pdu)

            chips_grid = GridLayout(cols=len(chips), spacing=dp(6), size_hint=(1, 1))
            for k, v, c_role in chips:
                chips_grid.add_widget(criar_chip_dado(k, v, cor_role=c_role, height=dp(28)))
            row_card.add_widget(chips_grid)

            card_camadas.add_widget(row_card)
            self._osi_camada_cards[num] = (r_bd_col, role)

        container.add_widget(card_camadas)
        scroll.add_widget(container)

        passos = self._passos_osi(preset, dados_reais)
        self._osi_player.definir_passos(passos, indice_inicial=0, auto_play=False)
        return scroll

    def _saltar_para_camada_osi(self, step_idx: int):
        if hasattr(self, "_osi_player") and self._osi_player.get_root_window() is not None:
            self._osi_player.parar()
            self._osi_player.ir_para(step_idx, animar=True)

    def _ao_mudar_passo_osi(self, _idx: int, passo: dict):
        colors = paleta_praticas()
        camada = int(passo.get("anim", {}).get("camada", 7))

        if hasattr(self, "_osi_camada_cards"):
            for num, (bd_col, role) in self._osi_camada_cards.items():
                bd_col.rgba = colors[role] if num == camada else colors["border"]

        if hasattr(self, "_osi_frame_blocos"):
            for num, bloco in self._osi_frame_blocos.items():
                if num == camada or (camada in (5, 6, 7) and num == 7):
                    bloco._bd_col.rgba = bloco._cor_titulo
                else:
                    bloco._bd_col.rgba = colors["border"]

    def _selecionar_preset_osi(self, preset_key: str):
        self._preset_atual = preset_key
        self._atualizar_abas()

    def _transmitir_pacote_osi(self):
        colors = paleta_praticas()
        preset_key = self._preset_atual
        if self._lab_pronto:
            self._osi_kpi_status._lbl_valor.text = "Executando..."
            self._osi_kpi_status._lbl_valor.color = colors["warning"]
            self._osi_modo_pill.children[0].text = "CAPTURANDO NO DOCKER..."

            def worker():
                dados = self.docker_lab.executar_experimento_osi(preset_key)
                Clock.schedule_once(partial(self._on_experimento_osi_concluido, preset_key, dados), 0)

            threading.Thread(target=worker, daemon=True).start()
        else:
            preset = self.PRESETS_PACOTE[preset_key]
            sim = {
                "_preset": preset_key,
                "status": "200 OK (Simulado)" if preset["transporte"] != "ICMP" else "Echo Reply OK",
                "rtt": "0.18 ms",
                "ttl": 64,
                "ip_orig": preset["ip_orig"],
                "ip_dest": preset["ip_dest"],
                "mac_orig": preset["mac_orig"],
                "mac_dest": preset["mac_dest"],
                "porta_dest": preset["porta_dest"],
                "detalhes": f"Fluxo {preset['app_proto']} validado nas 7 camadas OSI locais.",
                "frame_dump": (
                    f"[SIMULAÇÃO LOCAL] {preset['ip_orig']}.{preset['porta_orig']} > "
                    f"{preset['ip_dest']}.{preset['porta_dest']}: {preset['transporte']} | {preset['payload']}"
                ),
            }
            self._dados_experimento_osi = sim
            self._aplicar_telemetria_e_play_osi(preset, sim)

    def _on_experimento_osi_concluido(self, preset_key: str, dados: dict, _dt):
        if not dados or self._aba_ativa != "osi" or self._preset_atual != preset_key:
            return
        if not hasattr(self, "_osi_player") or self._osi_player.get_root_window() is None:
            return
        dados["_preset"] = preset_key
        self._dados_experimento_osi = dados
        self._aplicar_telemetria_e_play_osi(self.PRESETS_PACOTE[preset_key], dados)

    def _aplicar_telemetria_e_play_osi(self, preset: dict, dados: dict):
        colors = paleta_praticas()
        self._osi_kpi_status._lbl_valor.text = dados.get("status", "OK")
        self._osi_kpi_status._lbl_valor.color = colors["success"]
        self._osi_kpi_rtt._lbl_valor.text = str(dados.get("rtt", "0.14 ms"))
        self._osi_kpi_ttl._lbl_valor.text = f"TTL {dados.get('ttl', 64)} • {preset['transporte']}"
        self._osi_modo_pill.children[0].text = "DADO REAL DOCKER" if self._lab_pronto else "SIMULAÇÃO CONCLUÍDA"

        if hasattr(self, "_osi_dump_drawer"):
            self._osi_dump_drawer.definir_conteudo(
                dados.get("frame_dump") or dados.get("raw_output", ""),
                badge_texto="tcpdump Capturado" if self._lab_pronto else "Log Simulado",
            )

        passos = self._passos_osi(preset, dados)
        self._osi_player.definir_passos(passos, indice_inicial=0, auto_play=True)

    # =========================================================================
    # ABA 2: BANCADA DE ROTEAMENTO, MÁSCARAS & BITWISE AND (HUD + ANIMAÇÃO)
    # =========================================================================

    def _montar_tela_roteamento(self):
        colors = paleta_praticas()
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5), scroll_type=["bars", "content"])
        container = GridLayout(cols=1, spacing=dp(10), padding=(dp(2), dp(4)), size_hint_y=None)
        container.bind(minimum_height=container.setter("height"))

        # 1. Cenários Práticos e Inputs
        card_cenarios = criar_card(padding=dp(12), spacing=dp(8))
        card_cenarios.add_widget(criar_label("1. Cenários Práticos de Roteamento & Máscaras", size="13sp", bold=True, color=colors["text"]))

        cenarios = (
            ("Mesma Sub-rede /24 (Comunicação Direta)", "192.168.10.10/24", "192.168.10.20/24"),
            ("Sub-redes Diferentes /25 (Necessita Roteador L3)", "192.168.10.10/25", "192.168.10.130/25"),
            ("Máscara Incompatível (/24 vs /26)", "192.168.10.10/24", "192.168.10.130/26"),
            ("Rede Local vs Internet Pública", "192.168.10.10/24", "8.8.8.8/32"),
        )
        grid_cen = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(74))
        for titulo, ip_a, ip_b in cenarios:
            grid_cen.add_widget(
                criar_botao(
                    titulo,
                    partial(self._aplicar_cenario_roteamento, ip_a, ip_b),
                    variant="secondary",
                    height=dp(33),
                    font_size="10sp",
                )
            )
        card_cenarios.add_widget(grid_cen)

        grid_inputs = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(64))
        self.rot_host_a = _campo("Host A (IP/Prefixo)", "Ex.: 192.168.10.10/24")
        self.rot_host_a.input.text = "192.168.10.10/24"
        self.rot_host_b = _campo("Host B (IP/Prefixo)", "Ex.: 192.168.10.20/24")
        self.rot_host_b.input.text = "192.168.10.20/24"
        grid_inputs.add_widget(self.rot_host_a)
        grid_inputs.add_widget(self.rot_host_b)
        card_cenarios.add_widget(grid_inputs)

        card_cenarios.add_widget(
            criar_botao(
                "Analisar Rota, Calcular Bitwise AND & Animar Decisão",
                partial(self._analisar_roteamento, auto_play=True),
                variant="primary",
                height=dp(36),
                icone="routes",
            )
        )
        container.add_widget(card_cenarios)

        # 2. Banner de Diagnóstico + Palco Animado + Player Passo a Passo
        card_anim = criar_card(padding=dp(12), spacing=dp(8), elevated=True)
        diag_row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
        diag_row.add_widget(criar_label("2. Simulação Animada da Decisão de Rota (Passo a Passo)", size="13sp", bold=True, color=colors["text"]))
        diag_row.add_widget(Widget())
        self._rot_diag_pill = criar_pill("CALCULANDO...", colors["success_bg"], colors["success"], "check-circle-outline", height=dp(24))
        diag_row.add_widget(self._rot_diag_pill)
        card_anim.add_widget(diag_row)

        self._rot_veredito_chip = criar_chip_dado("Veredito", "Analisando hosts...", "success", height=dp(32))
        card_anim.add_widget(self._rot_veredito_chip)

        self._palco_rot = PalcoAnimadoRoteamento()
        self._rot_player = PlayerPassoAPasso(self._palco_rot, intervalo_autoplay=2.8)
        card_anim.add_widget(self._rot_player)
        container.add_widget(card_anim)

        # 3. HUD Visual Bitwise AND (Sem Poluição de Texto!)
        card_and = criar_card(padding=dp(12), spacing=dp(8))
        hdr_and = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(8))
        hdr_and.add_widget(criar_label("3. Comparativo HUD Bitwise AND (IP & Máscara = Rede)", size="13sp", bold=True, color=colors["text"]))
        hdr_and.add_widget(Widget())
        hdr_and.add_widget(criar_pill("Azul: Bits Rede (Net ID)", colors["tag_bg"], colors["primary"], height=dp(22)))
        hdr_and.add_widget(criar_pill("Verde: Bits Host (Host ID)", colors["success_bg"], colors["success"], height=dp(22)))
        card_and.add_widget(hdr_and)

        self._rot_bits_box = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self._rot_bits_box.bind(minimum_height=self._rot_bits_box.setter("height"))
        card_and.add_widget(self._rot_bits_box)
        container.add_widget(card_and)

        # 4. HUD Real do Kernel Linux (FIB / ARP) & Ping ICMP
        card_ping = criar_card(padding=dp(12), spacing=dp(8), elevated=True)
        hdr_ping = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        hdr_ping.add_widget(criar_label("4. Telemetria do Kernel Linux (FIB / ARP) & Ping ICMP", size="13sp", bold=True, color=colors["text"]))
        hdr_ping.add_widget(Widget())
        self._rot_ping_badge = criar_pill("PRONTO P/ PING", colors["tag_bg"], colors["accent"])
        hdr_ping.add_widget(self._rot_ping_badge)
        card_ping.add_widget(hdr_ping)

        fib_row = GridLayout(cols=4, spacing=dp(8), size_hint_y=None, height=dp(64))
        self._rot_kpi_rota = criar_kpi_tile("Rota FIB (ip route)", "--", "Tabela do kernel", "primary")
        self._rot_kpi_iface = criar_kpi_tile("Interface / Via", "--", "Next-Hop", "accent")
        self._rot_kpi_arp = criar_kpi_tile("Vizinho ARP (ip neigh)", "Aguardando", "Resolução MAC L2", "info")
        self._rot_kpi_perda = criar_kpi_tile("Ping / Perda", "--", "4 pacotes ICMP", "success")
        for k in (self._rot_kpi_rota, self._rot_kpi_iface, self._rot_kpi_arp, self._rot_kpi_perda):
            fib_row.add_widget(k)
        card_ping.add_widget(fib_row)

        texto_ping = "Executar Teste de Ping ICMP Real (Container PC-A)" if self._lab_pronto else "Executar Teste de Ping ICMP (4 Pacotes)"
        card_ping.add_widget(criar_botao(texto_ping, self._executar_ping_cenario, variant="primary", height=dp(36), icone="network"))

        # Strip visual de 4 pacotes ICMP em vez de texto cru
        self._rot_ping_strip = GridLayout(cols=4, spacing=dp(8), size_hint_y=None, height=dp(34))
        for seq in range(1, 5):
            self._rot_ping_strip.add_widget(criar_chip_dado(f"ICMP #{seq}", "Aguardando", "muted", height=dp(32)))
        card_ping.add_widget(self._rot_ping_strip)

        self._rot_dump_drawer = DrawerDumpBruto(titulo="Logs Brutos do Kernel (ip route get, ip neigh, ping)", icone="console")
        self._rot_dump_drawer.definir_conteudo("Execute a análise ou Ping para visualizar os comandos brutos do kernel.", "Pronto")
        card_ping.add_widget(self._rot_dump_drawer)

        container.add_widget(card_ping)
        scroll.add_widget(container)

        self._analisar_roteamento(auto_play=False)
        return scroll

    def _aplicar_cenario_roteamento(self, ip_a: str, ip_b: str):
        if hasattr(self, "rot_host_a") and hasattr(self, "rot_host_b"):
            self.rot_host_a.input.text = ip_a
            self.rot_host_b.input.text = ip_b
            self._analisar_roteamento(auto_play=True)

    def _analisar_roteamento(self, auto_play: bool = False):
        colors = paleta_praticas()
        try:
            iface_a = ipaddress.ip_interface(self.rot_host_a.input.text.strip())
            iface_b = ipaddress.ip_interface(self.rot_host_b.input.text.strip())
        except ValueError:
            self._rot_veredito_chip.children[0].text = "Erro: informe endereços IPv4 válidos com prefixo (ex: 192.168.10.10/24)."
            return

        rede_a = iface_a.network
        rede_b = iface_b.network

        ip_b_na_mask_a = ipaddress.ip_network(f"{iface_b.ip}/{rede_a.prefixlen}", strict=False)
        a_enxerga_b_local = ip_b_na_mask_a.network_address == rede_a.network_address
        ip_a_na_mask_b = ipaddress.ip_network(f"{iface_a.ip}/{rede_b.prefixlen}", strict=False)
        b_enxerga_a_local = ip_a_na_mask_b.network_address == rede_b.network_address

        if rede_a == rede_b:
            modo = "local"
            badge_txt = f"MESMA SUB-REDE ({rede_a})"
            cor_diag = "success"
            veredito_txt = "Comunicação direta em Camada 2 via Switch local (ARP descobre MAC sem Roteador)."
        elif a_enxerga_b_local and not b_enxerga_a_local:
            modo = "assimetrica"
            badge_txt = "MÁSCARA ASSIMÉTRICA"
            cor_diag = "warning"
            veredito_txt = f"Host A acha que B é local ({rede_a}), mas B vê A em rede externa ({rede_b})! Causa falha ARP/Gateway."
        else:
            modo = "roteador"
            badge_txt = "ROTEAMENTO L3 OBRIGATÓRIO"
            cor_diag = "primary"
            veredito_txt = f"Sub-redes distintas ({rede_a} ≠ {rede_b}): o pacote precisa ir ao Roteador Gateway."

        self._rot_diag_pill.children[0].text = badge_txt
        self._rot_veredito_chip.children[0].text = veredito_txt
        registrar_cor_texto(self._rot_veredito_chip.children[0], colors[cor_diag], cor_diag)

        self._palco_rot.configurar_hosts(str(iface_a), str(iface_b), modo)

        # Reconstrói visualizador HUD Bitwise AND (Host A e Host B)
        self._rot_bits_box.clear_widgets()
        for titulo_h, iface, rede, cor_h in (
            ("HOST A (ORIGEM)", iface_a, rede_a, "primary"),
            ("HOST B (DESTINO)", iface_b, rede_b, "success"),
        ):
            bloco_h = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(134),
                padding=(dp(10), dp(8)),
                spacing=dp(5),
            )
            with bloco_h.canvas.before:
                fill_b = Color(*colors["panel"])
                bg_b = RoundedRectangle(pos=bloco_h.pos, size=bloco_h.size, radius=[dp(10)])
                Color(*colors["border"])
                bd_b = Line(rounded_rectangle=(bloco_h.x, bloco_h.y, bloco_h.width, bloco_h.height, dp(10)), width=dp(1))
            registrar_fundo(bloco_h, fill_b, "panel")
            bloco_h.bind(
                pos=lambda w, v, s=bg_b, b=bd_b: (setattr(s, "pos", v), setattr(b, "rounded_rectangle", (v[0], v[1], w.width, w.height, dp(10)))),
                size=lambda w, v, s=bg_b, b=bd_b: (setattr(s, "size", v), setattr(b, "rounded_rectangle", (w.x, w.y, v[0], v[1], dp(10)))),
            )
            bloco_h.add_widget(
                criar_label(f"{titulo_h}  •  Rede resultante: {rede}", size="10.5sp", bold=True, color=colors[cor_h], height=dp(20), role=cor_h)
            )
            bloco_h.add_widget(construir_visualizador_bits_ipv4(iface.ip.packed, rede.prefixlen, "IP do Host", str(iface.ip)))
            bloco_h.add_widget(construir_visualizador_bits_ipv4(rede.netmask.packed, rede.prefixlen, f"Máscara /{rede.prefixlen}", str(rede.netmask)))
            bloco_h.add_widget(construir_visualizador_bits_ipv4(rede.network_address.packed, rede.prefixlen, "AND = Rede", str(rede.network_address)))
            self._rot_bits_box.add_widget(bloco_h)

        # Atualiza KPI FIB simulado ou consulta Docker real
        if modo == "local":
            self._rot_kpi_rota._lbl_valor.text = f"Direta ({rede_a})"
            self._rot_kpi_iface._lbl_valor.text = "eth0 (Broadcast L2)"
        else:
            self._rot_kpi_rota._lbl_valor.text = "Via Gateway Padrão"
            self._rot_kpi_iface._lbl_valor.text = "eth0 ➔ Roteador L3"

        # Monta passos animados da decisão de rota
        passos_rot = [
            {
                "curto": "1. AND A",
                "badge": "PASSO 1/5 • HARDWARE DA PLACA DE REDE (HOST A)",
                "titulo": "Host A calcula sua própria sub-rede via Bitwise AND",
                "resumo": (
                    f"A placa de rede de A executa IP_A ({iface_a.ip}) AND Máscara_A (/{rede_a.prefixlen}). "
                    f"Onde há bit 1 na máscara, preserva o bit do IP; onde há 0, zera. Rede A = {rede_a.network_address}."
                ),
                "cor": "primary",
                "dados": [
                    ("IP Host A", str(iface_a.ip), "primary"),
                    ("Máscara A", f"/{rede_a.prefixlen} ({rede_a.netmask})", "info"),
                    ("Rede A", str(rede_a.network_address), "success"),
                ],
                "anim": {"ativos": ("A",), "edges": (), "de": "A", "para": "A", "pkt_label": f"AND A=/{rede_a.prefixlen}"},
            },
            {
                "curto": "2. AND Dest",
                "badge": "PASSO 2/5 • TESTE DE PROXIMIDADE POR HOST A",
                "titulo": "Host A aplica SUA própria máscara sobre o IP destino B",
                "resumo": (
                    f"Host A calcula IP_B ({iface_b.ip}) AND Máscara_A (/{rede_a.prefixlen}) = {ip_b_na_mask_a.network_address}. "
                    + (
                        "O resultado bate com Rede A! Logo, A considera B um vizinho LOCAL."
                        if a_enxerga_b_local
                        else f"Diferente de {rede_a.network_address}! Logo, A sabe que B está em OUTRA rede."
                    )
                ),
                "cor": "accent" if a_enxerga_b_local else "warning",
                "dados": [
                    ("IP B + Mask A", str(ip_b_na_mask_a.network_address), "accent"),
                    ("Rede A", str(rede_a.network_address), "primary"),
                    ("Visão de A", "Local (L2)" if a_enxerga_b_local else "Remota (L3)", "success" if a_enxerga_b_local else "warning"),
                ],
                "anim": {"ativos": ("A", "SW"), "edges": ("A_SW",), "de": "A", "para": "SW", "pkt_label": "Checa Destino"},
            },
            {
                "curto": "3. Visão B",
                "badge": "PASSO 3/5 • SIMETRIA DE MÁSCARA EM HOST B",
                "titulo": "Verificação da máscara configurada no destino Host B",
                "resumo": (
                    f"No sentido inverso, B aplica sua máscara /{rede_b.prefixlen} sobre A ({iface_a.ip}) -> {ip_a_na_mask_b.network_address}. "
                    + (
                        "ERRO DE REDE! A enxerga B como local, mas B enxerga A como remoto — o retorno falha!"
                        if modo == "assimetrica"
                        else "Ambos concordam com a mesma topologia (simetria válida)."
                    )
                ),
                "cor": "danger" if modo == "assimetrica" else "info",
                "dados": [
                    ("Rede B", str(rede_b), "success"),
                    ("Visão de B", "Local" if b_enxerga_a_local else "Via Gateway", "info"),
                    ("Simetria", "ASSIMÉTRICA!" if modo == "assimetrica" else "Simétrica OK", "danger" if modo == "assimetrica" else "success"),
                ],
                "anim": {
                    "ativos": ("B", "GW" if modo != "local" else "SW"),
                    "edges": ("GW_B", "SW_GW") if modo != "local" else ("SW_B",),
                    "de": "B",
                    "para": "GW" if modo != "local" else "SW",
                    "pkt_label": "Assimetria!" if modo == "assimetrica" else f"Mask B=/{rede_b.prefixlen}",
                },
            },
            {
                "curto": "4. Caminho",
                "badge": "PASSO 4/5 • ENCAMINHAMENTO NO SWITCH / ROTEADOR",
                "titulo": (
                    "Switch L2 entrega direto após Broadcast ARP"
                    if modo == "local"
                    else ("Conflito: ARP direto de A vs Gateway em B!" if modo == "assimetrica" else "Pacote encaminhado ao Roteador (Gateway Padrão)")
                ),
                "resumo": (
                    f"Host A envia broadcast ARP ('Quem tem {iface_b.ip}?'), descobre o MAC de B e envia o quadro direto via Switch."
                    if modo == "local"
                    else (
                        "Host A tenta ARP direto na rede local enquanto Host B tenta devolver pelo Gateway Padrão."
                        if modo == "assimetrica"
                        else "Switch entrega o quadro ao MAC do Roteador. Na Camada 3, o Roteador consulta sua FIB e encaminha para Rede B!"
                    )
                ),
                "cor": "success" if modo == "local" else ("danger" if modo == "assimetrica" else "warning"),
                "dados": [
                    ("Caminho Físico", "A ➔ Switch ➔ B" if modo == "local" else "A ➔ Switch ➔ Gateway ➔ B", "accent"),
                    ("Resolução ARP", f"ARP para {iface_b.ip}" if modo == "local" else "ARP para Gateway", "primary"),
                    ("Salto TTL", "Sem salto L3" if modo == "local" else "TTL -1 no Roteador", "warning"),
                ],
                "anim": {
                    "ativos": ("A", "SW", "B") if modo == "local" else ("A", "SW", "GW", "B"),
                    "edges": ("A_SW", "SW_B") if modo == "local" else ("A_SW", "SW_GW", "GW_B"),
                    "de": "SW" if modo == "local" else "GW",
                    "para": "B",
                    "pkt_label": "ARP Direct L2" if modo == "local" else "Salto L3 Gateway",
                },
            },
            {
                "curto": "5. Conclusão",
                "badge": "PASSO 5/5 • DIAGNÓSTICO FINAL DE ROTEAMENTO",
                "titulo": badge_txt,
                "resumo": veredito_txt,
                "cor": cor_diag,
                "dados": [
                    ("Diagnóstico", badge_txt, cor_diag),
                    ("Host A", str(iface_a), "primary"),
                    ("Host B", str(iface_b), "success"),
                ],
                "anim": {
                    "ativos": ("A", "B") if modo != "assimetrica" else ("A", "GW", "B"),
                    "edges": ("A_SW", "SW_B") if modo == "local" else ("A_SW", "SW_GW", "GW_B"),
                    "de": "B",
                    "para": "A",
                    "pkt_label": "Falha Retorno!" if modo == "assimetrica" else "Rota Validada",
                },
            },
        ]

        self._rot_player.definir_passos(passos_rot, indice_inicial=0, auto_play=auto_play)

        if self._lab_pronto:
            def worker():
                ok_r, out_r = self.docker_lab.consultar_rota_kernel(str(iface_b.ip))
                arp_out = self.docker_lab.consultar_vizinhos_arp()
                Clock.schedule_once(partial(self._on_rota_kernel_concluida, ok_r, out_r, arp_out, str(iface_b.ip)), 0)

            threading.Thread(target=worker, daemon=True).start()
        else:
            raw_fib = (
                f"# Modo Simulado (Docker offline)\n"
                f"# Calculo: {iface_a} -> {rede_a} vs {iface_b} -> {rede_b}\n"
                f"# Veredito: {veredito_txt}"
            )
            self._rot_dump_drawer.definir_conteudo(raw_fib, "Simulação Local")

    def _on_rota_kernel_concluida(self, _ok, out_route: str, arp_out: str, ip_destino: str, _dt):
        if self._aba_ativa != "roteamento" or not hasattr(self, "_rot_kpi_rota") or self._rot_kpi_rota.get_root_window() is None:
            return
        curto_route = out_route.splitlines()[0][:32] if out_route else "Sem rota"
        self._rot_kpi_rota._lbl_valor.text = curto_route
        mac_arp = "Cache vazio"
        if arp_out:
            for ln in arp_out.splitlines():
                if "lladdr" in ln:
                    parts = ln.split()
                    if "lladdr" in parts:
                        idx_m = parts.index("lladdr")
                        if idx_m + 1 < len(parts):
                            mac_arp = f"{parts[idx_m + 1][-8:]} ({parts[-1]})"
                            break
        self._rot_kpi_arp._lbl_valor.text = mac_arp
        dump_txt = f"$ ip route get {ip_destino}\n{out_route}\n\n$ ip neigh show\n{arp_out or '(Cache ARP vazio)'}"
        self._rot_dump_drawer.definir_conteudo(dump_txt, "Kernel FIB/ARP OK")

    def _executar_ping_cenario(self):
        colors = paleta_praticas()
        try:
            iface_a = ipaddress.ip_interface(self.rot_host_a.input.text.strip())
            iface_b = ipaddress.ip_interface(self.rot_host_b.input.text.strip())
        except ValueError:
            return

        if self._lab_pronto:
            self._rot_ping_badge.children[0].text = "DISPARANDO ICMP..."
            self._rot_kpi_perda._lbl_valor.text = "Testando..."

            def worker():
                ok, output = self.docker_lab.executar_ping_real(str(iface_b.ip), contagem=4)
                Clock.schedule_once(partial(self._on_ping_real_concluido, ok, output, iface_a, iface_b), 0)

            threading.Thread(target=worker, daemon=True).start()
        else:
            mesma_rede = iface_a.network == iface_b.network
            rtt_base = 0.55 if mesma_rede else 14.2
            ttl = 64 if mesma_rede else 63
            tempos = [f"{rtt_base + random.uniform(0.08, 0.32):.2f} ms" for _ in range(4)]
            raw_sim = [f"PING {iface_b.ip} a partir de {iface_a.ip} (Simulado):"]
            for i, tm in enumerate(tempos, 1):
                raw_sim.append(f"64 bytes de {iface_b.ip}: icmp_seq={i} ttl={ttl} time={tm}")
            raw_sim.append("4 packets transmitted, 4 received, 0% packet loss")
            self._atualizar_hud_ping(True, tempos, "0% perda", "\n".join(raw_sim), real=False)

    def _on_ping_real_concluido(self, ok: bool, output: str, _iface_a, _iface_b, _dt):
        if self._aba_ativa != "roteamento" or not hasattr(self, "_rot_ping_strip") or self._rot_ping_strip.get_root_window() is None:
            return
        tempos = re.findall(r"time=([\d.]+\s*ms)", output)
        perda = "0% perda"
        m_loss = re.search(r"(\d+%)\s*packet loss", output)
        if m_loss:
            perda = f"{m_loss.group(1)} perda"
        elif not ok and not tempos:
            perda = "100% perda (Inalcançável)"
        self._atualizar_hud_ping(ok, tempos, perda, output, real=True)

    def _atualizar_hud_ping(self, ok: bool, tempos: list[str], perda: str, raw_out: str, *, real: bool):
        colors = paleta_praticas()
        self._rot_ping_badge.children[0].text = ("PING DOCKER OK" if ok else "FALHA ICMP") if real else "PING SIMULADO OK"
        self._rot_kpi_perda._lbl_valor.text = perda
        self._rot_kpi_perda._lbl_valor.color = colors["success"] if ok else colors["danger"]

        self._rot_ping_strip.clear_widgets()
        for seq in range(1, 5):
            if seq - 1 < len(tempos):
                self._rot_ping_strip.add_widget(criar_chip_dado(f"ICMP #{seq}", f"{tempos[seq - 1]} OK", "success", height=dp(32)))
            else:
                self._rot_ping_strip.add_widget(criar_chip_dado(f"ICMP #{seq}", "Timeout / Sem rota", "danger", height=dp(32)))

        if hasattr(self, "_rot_dump_drawer"):
            atual = self._rot_dump_drawer._texto_bruto
            prefixo = f"{atual}\n\n" if atual and "PING " not in atual else ""
            self._rot_dump_drawer.definir_conteudo(f"{prefixo}$ ping -c 4\n{raw_out}", "Ping + FIB")

    # =========================================================================
    # ABA 3: RESOLUÇÃO DNS HIERÁRQUICA (HUD ESTRUTURADO + ANIMAÇÃO PASSO A PASSO)
    # =========================================================================

    def _passos_dns(self, dominio: str, tipo: str, dados: dict) -> list[dict]:
        partes = dominio.strip(".").split(".")
        tld = f".{partes[-1]}" if len(partes) > 1 else ".local"
        servidor_dns = dados.get("servidor_dns", "192.168.10.20")
        resposta = dados.get("resposta_principal", "192.168.10.20")
        ttl_s = dados.get("ttl", 300)
        rtt = dados.get("rtt", "2 ms")

        subs_base = {
            "CLI": "Cache: MISS",
            "RES": f"DNS {servidor_dns}",
            "ROOT": "Raiz Global (.)",
            "TLD": f"TLD {tld}",
            "AUTH": f"NS {dominio[:16]}",
        }

        return [
            {
                "curto": "1. Cache SO",
                "badge": "PASSO 1/6 • CLIENTE E CACHE LOCAL (PC-A)",
                "titulo": f"Aplicação solicita '{dominio}' ({tipo}) e verifica Cache Local",
                "resumo": (
                    f"Antes de enviar qualquer pacote na rede, PC-A verifica seu cache DNS em RAM e o arquivo /etc/hosts. "
                    f"Como não há registro válido para '{dominio}', ocorre Cache MISS."
                ),
                "cor": "primary",
                "dados": [
                    ("Domínio", dominio, "primary"),
                    ("Tipo Query", tipo, "accent"),
                    ("Cache Local", "MISS (Ausente)", "warning"),
                ],
                "anim": {"edge": "", "ativos": ("CLI",), "de": "CLI", "para": "CLI", "pkt_label": "Cache MISS", "subs": subs_base},
            },
            {
                "curto": "2. Resolver",
                "badge": "PASSO 2/6 • ENVIO UDP/53 AO RESOLVER RECURSIVO",
                "titulo": f"PC-A envia Query DNS via UDP Porta 53 para {servidor_dns}",
                "resumo": (
                    f"PC-A envia um datagrama UDP porta 53 com flag RD=1 (Recursion Desired) pedindo ao Resolver "
                    f"que descubra o registro {tipo} de '{dominio}'."
                ),
                "cor": "accent",
                "dados": [
                    ("Transporte", "UDP :53", "warning"),
                    ("Resolver", servidor_dns, "accent"),
                    ("Flags DNS", "RD=1 (Recursiva)", "info"),
                ],
                "anim": {
                    "edge": "CLI_RES",
                    "ativos": ("CLI", "RES"),
                    "de": "CLI",
                    "para": "RES",
                    "pkt_label": f"QUERY {tipo}",
                    "subs": {**subs_base, "RES": "Recebeu Query"},
                },
            },
            {
                "curto": "3. Root (.)",
                "badge": "PASSO 3/6 • CONSULTA AO SERVIDOR RAIZ (ROOT)",
                "titulo": f"Resolver consulta Root Server sobre a extensão '{tld}'",
                "resumo": (
                    f"Se o Resolver não tiver '{dominio}' em cache, ele pergunta a um dos 13 clusters Root (.) "
                    f"onde estão os servidores responsáveis pelo domínio de topo '{tld}'."
                ),
                "cor": "warning",
                "dados": [
                    ("Consulta Root", f"Quem atende '{tld}'?", "warning"),
                    ("Resposta Root", f"IP do TLD {tld}", "success"),
                    ("Tipo Resposta", "Referral (NS)", "info"),
                ],
                "anim": {
                    "edge": "RES_ROOT",
                    "ativos": ("RES", "ROOT"),
                    "de": "RES",
                    "para": "ROOT",
                    "pkt_label": f"TLD {tld}?",
                    "subs": {**subs_base, "ROOT": f"Indica TLD {tld}"},
                },
            },
            {
                "curto": f"4. TLD {tld}",
                "badge": f"PASSO 4/6 • CONSULTA AO SERVIDOR TLD ({tld})",
                "titulo": f"Servidor TLD informa quem é o Autoritativo de '{dominio}'",
                "resumo": (
                    f"O Resolver segue para o servidor TLD '{tld}', que consulta sua lista de delegações e retorna "
                    f"o endereço do Nameserver Autoritativo oficial de '{dominio}'."
                ),
                "cor": "info",
                "dados": [
                    ("Servidor TLD", f"Zona {tld}", "info"),
                    ("Retorno NS", f"ns1.{dominio}", "accent"),
                    ("Delegação", "Autoritativo OK", "success"),
                ],
                "anim": {
                    "edge": "RES_TLD",
                    "ativos": ("RES", "TLD"),
                    "de": "RES",
                    "para": "TLD",
                    "pkt_label": "NS Oficial?",
                    "subs": {**subs_base, "TLD": f"Indica ns1"},
                },
            },
            {
                "curto": "5. Autorit.",
                "badge": "PASSO 5/6 • RESPOSTA OFICIAL DO SERVIDOR AUTORITATIVO",
                "titulo": f"Autoritativo responde o registro {tipo}: {resposta}",
                "resumo": (
                    f"O Servidor Autoritativo lê sua tabela oficial de zona DNS e retorna a resposta autoritativa (flag AA=1): "
                    f"'{dominio} IN {tipo} {resposta}' com TTL de {ttl_s}s."
                ),
                "cor": "success",
                "dados": [
                    ("Registro", f"{tipo} = {resposta}", "success"),
                    ("TTL Vida", f"{ttl_s} segundos", "primary"),
                    ("Status Header", "NOERROR (AA=1)", "success"),
                ],
                "anim": {
                    "edge": "RES_AUTH",
                    "ativos": ("RES", "AUTH"),
                    "de": "AUTH",
                    "para": "RES",
                    "pkt_label": "RESP OK!",
                    "subs": {**subs_base, "AUTH": f"{tipo}: {resposta[:18]}"},
                },
            },
            {
                "curto": "6. Cache & IP",
                "badge": "PASSO 6/6 • ENTREGA AO CLIENTE E ARMAZENAMENTO EM CACHE",
                "titulo": f"PC-A recebe {resposta} em {rtt} e grava em Cache",
                "resumo": (
                    f"O Resolver armazena o resultado em cache por {ttl_s}s e o devolve a PC-A. "
                    f"Agora a aplicação de PC-A já possui o endereço final para iniciar TCP/HTTP ou envio!"
                ),
                "cor": "success",
                "dados": [
                    ("Destino Final", resposta, "success"),
                    ("Tempo Total", rtt, "primary"),
                    ("Próxima Ação", "Conectar no IP/Host", "accent"),
                ],
                "anim": {
                    "edge": "CLI_RES",
                    "ativos": ("CLI", "RES"),
                    "de": "RES",
                    "para": "CLI",
                    "pkt_label": f"OK {rtt}",
                    "subs": {**subs_base, "CLI": f"Cache: {resposta[:16]}", "RES": f"Cached {ttl_s}s"},
                },
            },
        ]

    def _simular_dados_dns(self, dominio: str, tipo: str) -> dict:
        _, _, valor = DockerNetworkLab._build_dns_record_data(dominio, tipo, self._ips_reais)
        dom = re.sub(r"[^a-zA-Z0-9.\-]", "", dominio.strip().lower()) or "pm-painel.local"
        return {
            "sucesso": True,
            "modo": "SIMULADO",
            "dominio": dom,
            "tipo": tipo,
            "status": "NOERROR (Simulado)",
            "rtt": f"{random.randint(2, 6)} ms",
            "ttl": 300,
            "msg_size": "58 bytes",
            "servidor_dns": "192.168.10.20",
            "resposta_principal": valor,
            "registros": [
                {"dominio": f"{dom}.", "ttl": "300s", "classe": "IN", "tipo": tipo, "valor": valor}
            ],
            "frame_dump": (
                f"; <<>> Simulador DNS PM-Painel <<>> {dom} {tipo}\n"
                f";; HEADER: opcode: QUERY, status: NOERROR\n"
                f";; ANSWER SECTION:\n{dom}.\t300\tIN\t{tipo}\t{valor}"
            ),
        }

    def _montar_tela_dns(self):
        colors = paleta_praticas()
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5), scroll_type=["bars", "content"])
        container = GridLayout(cols=1, spacing=dp(10), padding=(dp(2), dp(4)), size_hint_y=None)
        container.bind(minimum_height=container.setter("height"))

        # 1. Entrada e Presets de Domínio & Tipo de Registro
        card_cfg = criar_card(padding=dp(12), spacing=dp(8))
        hdr = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        hdr.add_widget(criar_label("1. Consultor Prático de Domínios & Registros DNS", size="13sp", bold=True, color=colors["text"]))
        hdr.add_widget(Widget())
        hdr.add_widget(criar_pill("UDP / PORTA 53", colors["tag_bg"], colors["accent"], "dns"))
        card_cfg.add_widget(hdr)

        presets_row = GridLayout(cols=5, spacing=dp(6), size_hint_y=None, height=dp(34))
        for dom, rec in self.PRESETS_DNS:
            sel = dom == self._dns_dominio_atual and rec == self._dns_tipo_atual
            presets_row.add_widget(
                criar_botao(
                    f"{dom} ({rec})",
                    partial(self._aplicar_preset_dns, dom, rec),
                    variant="primary" if sel else "secondary",
                    height=dp(32),
                    font_size="9.5sp",
                )
            )
        card_cfg.add_widget(presets_row)

        input_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        self.dns_input = CampoTexto(
            hint_text="Digite um domínio (ex: pm-painel.local ou www.google.com)...",
            appearance="dark" if tema_escuro() else "light",
            size_hint_y=None,
            height=dp(40),
            font_size="11.5sp",
        )
        self.dns_input.text = self._dns_dominio_atual
        self.dns_input._tema_aparencia = True
        self.dns_input.size_hint_x = 0.48
        input_row.add_widget(self.dns_input)

        # Chips seletores de Tipo de Registro
        tipos_box = GridLayout(cols=5, spacing=dp(4), size_hint=(0.30, None), height=dp(40))
        self._dns_tipo_btns: dict[str, BotaoAcao] = {}
        for t in ("A", "AAAA", "CNAME", "MX", "TXT"):
            b = criar_botao(
                t,
                partial(self._selecionar_tipo_dns, t),
                variant="primary" if t == self._dns_tipo_atual else "secondary",
                height=dp(38),
                font_size="10sp",
            )
            self._dns_tipo_btns[t] = b
            tipos_box.add_widget(b)
        input_row.add_widget(tipos_box)

        btn_consultar = criar_botao(
            "Consultar & Animar",
            partial(self._executar_consulta_dns, auto_play=True),
            variant="primary",
            height=dp(40),
            icone="docker" if self._lab_pronto else "dns",
        )
        btn_consultar.size_hint_x = 0.22
        input_row.add_widget(btn_consultar)
        card_cfg.add_widget(input_row)
        container.add_widget(card_cfg)

        # 2. HUD Telemetria DNS + Palco Animado + Player Passo a Passo
        card_anim = criar_card(padding=dp(12), spacing=dp(8), elevated=True)
        hdr_anim = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        hdr_anim.add_widget(criar_label("2. Jornada Animada da Resolução DNS (Passo a Passo)", size="13sp", bold=True, color=colors["text"]))
        hdr_anim.add_widget(Widget())
        self._dns_modo_pill = criar_pill(
            "DOCKER REAL DIG" if self._lab_pronto else "SIMULAÇÃO DNS",
            colors["success_bg"] if self._lab_pronto else colors["tag_bg"],
            colors["success"] if self._lab_pronto else colors["accent"],
        )
        hdr_anim.add_widget(self._dns_modo_pill)
        card_anim.add_widget(hdr_anim)

        kpi_dns = GridLayout(cols=5, spacing=dp(8), size_hint_y=None, height=dp(64))
        self._dns_kpi_dom = criar_kpi_tile("Domínio", self._dns_dominio_atual, "Consulta QNAME", "primary")
        self._dns_kpi_tipo = criar_kpi_tile("Registro", self._dns_tipo_atual, "QTYPE / IN", "info")
        self._dns_kpi_status = criar_kpi_tile("Status", "NOERROR", "Header DNS", "success")
        self._dns_kpi_rtt = criar_kpi_tile("Query Time", "-- ms", "TTL 300s", "warning")
        self._dns_kpi_resp = criar_kpi_tile("Resposta Principal", "--", "Valor resolvido", "success")
        for k in (self._dns_kpi_dom, self._dns_kpi_tipo, self._dns_kpi_status, self._dns_kpi_rtt, self._dns_kpi_resp):
            kpi_dns.add_widget(k)
        card_anim.add_widget(kpi_dns)

        self._palco_dns = PalcoAnimadoDNS()
        self._dns_player = PlayerPassoAPasso(self._palco_dns, intervalo_autoplay=2.7)
        card_anim.add_widget(self._dns_player)
        container.add_widget(card_anim)

        # 3. Tabela HUD de Registros DNS + Drawer Bruto dig/tcpdump
        card_resp = criar_card(padding=dp(12), spacing=dp(8))
        card_resp.add_widget(criar_label("3. Seção de Resposta Estruturada (ANSWER SECTION HUD)", size="13sp", bold=True, color=colors["text"]))

        self._dns_tabela_box = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        self._dns_tabela_box.bind(minimum_height=self._dns_tabela_box.setter("height"))
        card_resp.add_widget(self._dns_tabela_box)

        self._dns_dump_drawer = DrawerDumpBruto(titulo="Saída Bruta `dig` & Captura `tcpdump` UDP/53", icone="code-tags")
        card_resp.add_widget(self._dns_dump_drawer)
        container.add_widget(card_resp)

        scroll.add_widget(container)
        autoplay = bool(getattr(self, "_dns_autoplay_pendente", False))
        self._dns_autoplay_pendente = False
        self._aplicar_dados_dns(
            self._dns_dominio_atual,
            self._dns_tipo_atual,
            self._simular_dados_dns(self._dns_dominio_atual, self._dns_tipo_atual),
            auto_play=autoplay,
        )
        if self._lab_pronto:
            self._executar_consulta_dns(auto_play=autoplay)
        return scroll

    def _aplicar_preset_dns(self, dom: str, tipo: str):
        self._dns_dominio_atual = dom
        self._dns_tipo_atual = tipo
        self._dns_autoplay_pendente = True
        self._atualizar_abas()

    def _selecionar_tipo_dns(self, tipo: str):
        self._dns_tipo_atual = tipo
        if hasattr(self, "_dns_tipo_btns"):
            for key, btn in self._dns_tipo_btns.items():
                btn.variant = "primary" if key == tipo else "secondary"
        self._executar_consulta_dns(auto_play=False)

    def _executar_consulta_dns(self, auto_play: bool = False):
        colors = paleta_praticas()
        if hasattr(self, "dns_input"):
            dom = self.dns_input.text.strip() or "pm-painel.local"
        else:
            dom = self._dns_dominio_atual
        self._dns_dominio_atual = dom
        tipo = self._dns_tipo_atual

        if self._lab_pronto:
            self._dns_kpi_status._lbl_valor.text = "Consultando..."
            self._dns_kpi_status._lbl_valor.color = colors["warning"]

            def worker():
                dados = self.docker_lab.executar_experimento_dns(dom, tipo)
                Clock.schedule_once(partial(self._on_dns_concluido, dom, tipo, dados, auto_play), 0)

            threading.Thread(target=worker, daemon=True).start()
        else:
            dados = self._simular_dados_dns(dom, tipo)
            self._aplicar_dados_dns(dom, tipo, dados, auto_play=auto_play)

    def _on_dns_concluido(self, dom: str, tipo: str, dados: dict, auto_play: bool, _dt):
        if self._aba_ativa != "dns" or not hasattr(self, "_dns_player") or self._dns_player.get_root_window() is None:
            return
        self._aplicar_dados_dns(dom, tipo, dados, auto_play=auto_play)

    def _aplicar_dados_dns(self, dom: str, tipo: str, dados: dict, *, auto_play: bool):
        colors = paleta_praticas()
        self._dns_kpi_dom._lbl_valor.text = dados.get("dominio", dom)
        self._dns_kpi_tipo._lbl_valor.text = tipo
        self._dns_kpi_status._lbl_valor.text = dados.get("status", "NOERROR")
        self._dns_kpi_status._lbl_valor.color = colors["success"] if dados.get("sucesso") else colors["danger"]
        self._dns_kpi_rtt._lbl_valor.text = str(dados.get("rtt", "1 ms"))
        self._dns_kpi_rtt._lbl_sub.text = f"TTL {dados.get('ttl', 300)}s • UDP/53"
        self._dns_kpi_resp._lbl_valor.text = str(dados.get("resposta_principal", "--"))
        self._dns_modo_pill.children[0].text = "DIG REAL DOCKER" if dados.get("modo") == "DOCKER_REAL" else "SIMULAÇÃO DNS"

        self._dns_tabela_box.clear_widgets()
        for reg in dados.get("registros", []):
            row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
            row.add_widget(criar_chip_dado("Nome", reg["dominio"], "primary"))
            row.add_widget(criar_chip_dado("TTL / Classe", f"{reg['ttl']} • {reg['classe']}", "info"))
            row.add_widget(criar_chip_dado(f"Tipo {reg['tipo']}", reg["valor"], "success"))
            self._dns_tabela_box.add_widget(row)

        dump = dados.get("frame_dump") or dados.get("raw_output", "")
        self._dns_dump_drawer.definir_conteudo(dump, "dig + tcpdump" if self._lab_pronto else "Simulado")

        passos = self._passos_dns(dados.get("dominio", dom), tipo, dados)
        self._dns_player.definir_passos(passos, indice_inicial=0, auto_play=auto_play)

    # =========================================================================
    # ABA 4: CALCULADORA CIDR & CONVERSOR IP (HUD BINÁRIO + LINUX)
    # =========================================================================

    def _montar_tela_calculadora(self):
        colors = paleta_praticas()
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5), scroll_type=["bars", "content"])
        container = GridLayout(cols=1, spacing=dp(10), padding=(dp(2), dp(4)), size_hint_y=None)
        container.bind(minimum_height=container.setter("height"))

        card_input = criar_card(padding=dp(12), spacing=dp(8))
        header_calc = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        header_calc.add_widget(criar_label("1. Calculadora de Sub-redes CIDR & Conversor IP", size="13sp", bold=True, color=colors["text"]))
        header_calc.add_widget(Widget())
        header_calc.add_widget(criar_pill("IPv4 & IPv6", colors["tag_bg"], colors["accent"], icone="calculator-variant"))
        card_input.add_widget(header_calc)

        row_chips = GridLayout(cols=5, spacing=dp(8), size_hint_y=None, height=dp(34))
        exemplos = ("192.168.10.0/24", "10.0.0.0/8", "172.16.0.0/16", "192.168.10.128/26", "2001:db8::/64")
        for ex in exemplos:
            row_chips.add_widget(criar_botao(ex, partial(self._aplicar_exemplo_calc, ex), variant="secondary", height=dp(32), font_size="10.5sp"))
        card_input.add_widget(row_chips)

        row_calc = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        self.calc_input = CampoTexto(
            hint_text="Digite IP/prefixo CIDR (ex: 192.168.10.34/24 ou 2001:db8::/64)...",
            appearance="dark" if tema_escuro() else "light",
            size_hint_y=None,
            height=dp(42),
            font_size="12sp",
        )
        self.calc_input.text = "192.168.10.34/24"
        self.calc_input._tema_aparencia = True
        self.calc_input.size_hint_x = 0.74
        row_calc.add_widget(self.calc_input)

        btn_calc = criar_botao("Calcular Sub-rede", self._calcular_cidr, variant="primary", height=dp(42), icone="calculator-variant")
        btn_calc.size_hint_x = 0.26
        row_calc.add_widget(btn_calc)
        card_input.add_widget(row_calc)
        container.add_widget(card_input)

        # Painel de Métricas
        card_metricas = criar_card(padding=dp(12), spacing=dp(8), elevated=True)
        header_met = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        header_met.add_widget(criar_label("2. Métricas e Faixas de Endereçamento Calculadas", size="13sp", bold=True, color=colors["text"]))
        header_met.add_widget(Widget())
        self.calc_badge_resumo = criar_pill("IPv4 • /24", colors["success_bg"], colors["success"])
        header_met.add_widget(self.calc_badge_resumo)
        card_metricas.add_widget(header_met)

        self.calc_grid_metricas = GridLayout(cols=3, spacing=dp(8), size_hint_y=None)
        self.calc_grid_metricas.bind(minimum_height=self.calc_grid_metricas.setter("height"))
        card_metricas.add_widget(self.calc_grid_metricas)
        container.add_widget(card_metricas)

        # HUD Binário Colorido + Comandos Linux Estruturados
        card_conv = criar_card(padding=dp(12), spacing=dp(8))
        hdr_bin = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(8))
        hdr_bin.add_widget(criar_label("3. Divisão Visual de Bits (Net ID vs Host ID) & Comandos Linux", size="13sp", bold=True, color=colors["text"]))
        hdr_bin.add_widget(Widget())
        hdr_bin.add_widget(criar_pill("Azul: Rede", colors["tag_bg"], colors["primary"], height=dp(22)))
        hdr_bin.add_widget(criar_pill("Verde: Host", colors["success_bg"], colors["success"], height=dp(22)))
        card_conv.add_widget(hdr_bin)

        self.calc_box_binario = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        self.calc_box_binario.bind(minimum_height=self.calc_box_binario.setter("height"))
        card_conv.add_widget(self.calc_box_binario)

        self.calc_box_comandos = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        self.calc_box_comandos.bind(minimum_height=self.calc_box_comandos.setter("height"))
        card_conv.add_widget(self.calc_box_comandos)

        container.add_widget(card_conv)
        scroll.add_widget(container)
        self._calcular_cidr()
        return scroll

    def _aplicar_exemplo_calc(self, ex: str):
        if hasattr(self, "calc_input"):
            self.calc_input.text = ex
            self._calcular_cidr()

    def _calcular_cidr(self):
        colors = paleta_praticas()
        texto = self.calc_input.text.strip()
        try:
            rede = ipaddress.ip_network(texto, strict=False)
        except ValueError:
            self.calc_grid_metricas.clear_widgets()
            self.calc_grid_metricas.add_widget(
                criar_label("Endereço ou máscara inválida. Utilize notação CIDR (ex.: 192.168.10.0/24).", size="12sp", color=colors["danger"], height=dp(36))
            )
            return

        self.calc_grid_metricas.clear_widgets()
        self.calc_box_binario.clear_widgets()
        self.calc_box_comandos.clear_widgets()

        if rede.version == 4:
            hosts = list(rede.hosts()) if rede.num_addresses <= 256 else None
            primeiro = hosts[0] if hosts else (rede.network_address if rede.prefixlen >= 31 else rede.network_address + 1)
            ultimo = hosts[-1] if hosts else (rede.broadcast_address if rede.prefixlen >= 31 else rede.broadcast_address - 1)
            hosts_uteis = max(0, rede.num_addresses - 2) if rede.prefixlen < 31 else rede.num_addresses
            escopo = "Privado (RFC 1918)" if rede.is_private else ("Loopback" if rede.is_loopback else "Público / Internet")

            self.calc_badge_resumo.children[0].text = f"IPv4 • /{rede.prefixlen} • {rede.num_addresses:,} IPs"

            metricas = (
                ("Endereço de Rede", f"{rede.network_address}/{rede.prefixlen}", "ID do segmento", "primary"),
                ("Máscara de Sub-rede", f"{rede.netmask}", f"Prefixo /{rede.prefixlen}", "text"),
                ("Faixa de Hosts Úteis", f"{primeiro} ➔ {ultimo}", f"{hosts_uteis:,} hosts válidos", "accent"),
                ("Endereço de Broadcast", f"{rede.broadcast_address}", "Difusão na sub-rede", "danger"),
                ("Máscara Curinga (Wildcard)", f"{rede.hostmask}", "Uso em ACL / OSPF", "text"),
                ("Escopo & Bits", f"{escopo}", f"{rede.prefixlen}b Rede • {32 - rede.prefixlen}b Host", "success"),
            )
            for t, v, s, role in metricas:
                self.calc_grid_metricas.add_widget(criar_kpi_tile(t, v, s, cor_role=role, height=dp(68)))

            self.calc_box_binario.add_widget(
                construir_visualizador_bits_ipv4(rede.network_address.packed, rede.prefixlen, "Rede (Bin)", str(rede.network_address))
            )
            self.calc_box_binario.add_widget(
                construir_visualizador_bits_ipv4(rede.netmask.packed, rede.prefixlen, "Máscara (Bin)", str(rede.netmask))
            )
            hex_row = GridLayout(cols=3, spacing=dp(8), size_hint_y=None, height=dp(30))
            hex_str = ".".join(f"{b:02X}" for b in rede.network_address.packed)
            hex_row.add_widget(criar_chip_dado("Hexadecimal", hex_str, "info"))
            hex_row.add_widget(criar_chip_dado("Bits de Rede", f"{rede.prefixlen} bits", "primary"))
            hex_row.add_widget(criar_chip_dado("Bits de Host", f"{32 - rede.prefixlen} bits", "success"))
            self.calc_box_binario.add_widget(hex_row)

            cmds = (
                ("1. Atribuir IP", f"ip addr add {rede.network_address + 1}/{rede.prefixlen} dev eth0"),
                ("2. Subir e Rotear", f"ip link set eth0 up && ip route add {rede.network_address}/{rede.prefixlen} dev eth0"),
                ("3. Inspecionar Kernel", "ip -br addr show dev eth0 && ip route show"),
            )
        else:
            self.calc_badge_resumo.children[0].text = f"IPv6 • /{rede.prefixlen}"
            metricas = (
                ("Endereço IPv6", f"{rede.network_address}/{rede.prefixlen}", "Prefixo de Roteamento", "primary"),
                ("Tamanho do Prefixo", f"/{rede.prefixlen} bits", f"{128 - rede.prefixlen} bits Interface ID", "text"),
                ("Faixa de Alocação", f"{rede.network_address} ➔ {rede.broadcast_address}", "Bloco completo IPv6", "accent"),
                ("Escopo do Bloco", "Privado ULA" if rede.is_private else "Global Unicast", "RFC 4193 / IANA", "success"),
                ("Expandido", rede.network_address.exploded[:28] + "...", "Notação 128 bits", "info"),
                ("Comprimido", rede.network_address.compressed, "Notação compacta", "primary"),
            )
            for t, v, s, role in metricas:
                self.calc_grid_metricas.add_widget(criar_kpi_tile(t, v, s, cor_role=role, height=dp(68)))

            v6_row = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(32))
            v6_row.add_widget(criar_chip_dado("Formato Expandido", rede.network_address.exploded, "info", height=dp(32)))
            v6_row.add_widget(criar_chip_dado("Comprimido", rede.network_address.compressed, "primary", height=dp(32)))
            self.calc_box_binario.add_widget(v6_row)

            cmds = (
                ("1. Atribuir IPv6", f"ip -6 addr add {rede.network_address}1/{rede.prefixlen} dev eth0"),
                ("2. Inspecionar IPv6", "ip -6 -br addr show dev eth0"),
            )

        for tag, cmd_str in cmds:
            row_cmd = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(8))
            pill_tag = criar_pill(tag, colors["tag_bg"], colors["accent"], height=dp(26), fixed_width=dp(150))
            pill_tag.pos_hint = {"center_y": 0.5}
            row_cmd.add_widget(pill_tag)
            row_cmd.add_widget(criar_chip_dado("Linux", cmd_str, "success", height=dp(30)))
            self.calc_box_comandos.add_widget(row_cmd)


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
            icone="docker",
        ))

        self.add_widget(self._montar_configuracao())
        self.add_widget(self._montar_controles())
        self.add_widget(self._montar_acoes_rapidas())

        self._drawer_rapido = DrawerDumpBruto(titulo="Resultado do Último Comando Rápido (Docker)", icone="console")
        self._drawer_rapido.definir_conteudo("Execute uma ação rápida acima para inspecionar a saída do container.", "Aguardando")
        self.add_widget(self._drawer_rapido)

        grid_painel = GridLayout(cols=2, spacing=dp(10), size_hint=(1, 1))
        grid_painel.add_widget(self._montar_terminal("A"))
        grid_painel.add_widget(self._montar_terminal("B"))
        self.add_widget(grid_painel)

        card_guia = criar_card(padding=dp(8), spacing=dp(4))
        card_guia.add_widget(criar_label("Comandos recomendados no terminal:", size="10sp", bold=True, color=paleta_praticas()["accent"], height=dp(18), role="accent"))
        guia_row = GridLayout(cols=3, spacing=dp(6), size_hint_y=None, height=dp(28))
        guia_row.add_widget(criar_chip_dado("Conectividade", "ping -c 4 192.168.10.20", "success", height=dp(26)))
        guia_row.add_widget(criar_chip_dado("Interfaces", "ip a && ip route", "primary", height=dp(26)))
        guia_row.add_widget(criar_chip_dado("Captura", "tcpdump -c 5 -i eth0", "info", height=dp(26)))
        card_guia.add_widget(guia_row)
        self.add_widget(card_guia)

    def aplicar_tema(self):
        aplicar_tema_arvore(self)

    def _montar_configuracao(self):
        colors = paleta_praticas()
        area = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(106))
        for key in ("A", "B"):
            node = self.nos[key]
            card = criar_card(padding=dp(8), spacing=dp(4), elevated=True)
            card.height = dp(106)
            card.add_widget(criar_label(f"Endereçamento de {node['nome']}", size="11sp", bold=True, color=colors["text"], height=dp(20)))
            address = _campo("IPv4 com prefixo CIDR", "192.168.10.10/24", height=dp(32))
            address.input.text = str(node["interface"])
            self.enderecos[key] = address.input
            card.add_widget(address)
            status = criar_label("Aguardando início do laboratório.", size="9sp", color=colors["muted"], height=dp(16), role="muted")
            self.statuses[key] = status
            card.add_widget(status)
            area.add_widget(card)
        return area

    def _montar_controles(self):
        colors = paleta_praticas()
        area = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        area.add_widget(criar_botao("Iniciar / Aplicar IPs", self._iniciar, height=dp(36), font_size="10sp", icone="play"))

        self._console_button = criar_botao(
            "Abrir Terminais Interativos",
            self._abrir_terminais,
            variant="primary",
            height=dp(36),
            font_size="10sp",
            icone="console",
        )
        self._console_button.disabled = True
        area.add_widget(self._console_button)

        area.add_widget(criar_botao("Encerrar Laboratório", self._encerrar, variant="secondary", height=dp(36), font_size="10sp", icone="restart"))

        self.status_lab = criar_label(
            self._terminal_error or "Inicie a rede para liberar os consoles Linux interativos.",
            size="9.5sp",
            color=colors["muted"],
            height=dp(36),
            valign="middle",
            role="muted",
        )
        area.add_widget(self.status_lab)
        return area

    def _montar_acoes_rapidas(self):
        row_acoes = GridLayout(cols=4, spacing=dp(8), size_hint_y=None, height=dp(34))
        row_acoes.add_widget(
            criar_botao("Ping Real A➔B", lambda: self._executar_acao_rapida("ping -c 3 192.168.10.20", "Ping PC-A ➔ PC-B"), variant="secondary", height=dp(32), font_size="9.5sp", icone="network")
        )
        row_acoes.add_widget(
            criar_botao("Capturar tcpdump", lambda: self._executar_acao_rapida("timeout 3 tcpdump -c 3 -nn -XX -l -Z root -i eth0 2>&1", "Captura tcpdump PC-B", target_pc="B"), variant="secondary", height=dp(32), font_size="9.5sp", icone="code-tags")
        )
        row_acoes.add_widget(
            criar_botao("Tabela ARP (ip neigh)", lambda: self._executar_acao_rapida("ip neigh show", "Tabela ARP (PC-A)"), variant="secondary", height=dp(32), font_size="9.5sp", icone="lan")
        )
        row_acoes.add_widget(
            criar_botao("Rotas (ip route)", lambda: self._executar_acao_rapida("ip route show", "Tabela de Rotas (PC-A)"), variant="secondary", height=dp(32), font_size="9.5sp", icone="routes")
        )
        return row_acoes

    def _executar_acao_rapida(self, comando: str, titulo: str, target_pc="A"):
        colors = paleta_praticas()
        if not self._pronto:
            self.status_lab.text = "Inicie os containers antes de executar comandos rápidos."
            return
        self.status_lab.text = f"Executando '{titulo}' no container {target_pc}..."
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
        self.status_lab.text = f"{titulo}: concluído com sucesso."
        self.status_lab.color = colors["success"]
        if hasattr(self, "_drawer_rapido"):
            self._drawer_rapido.definir_conteudo(out or "(Sem saída)", titulo)
            self._drawer_rapido._aplicar_estado_aberto(True)

    def _montar_terminal(self, key):
        colors = paleta_praticas()
        node = self.nos[key]
        panel = criar_card(padding=dp(10), spacing=dp(6), elevated=False)
        heading = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        heading.add_widget(IconeUI(nome="console", size_hint=(None, None), size=(dp(24), dp(24)), font_size=dp(20), color=colors["accent"]))
        title = criar_label(node["nome"], size="13sp", bold=True, color=colors["text"], height=dp(26))
        heading.add_widget(title)
        self.titulos[key] = title
        panel.add_widget(heading)

        address = criar_label(f"IP: {node['interface'].ip}/{node['interface'].network.prefixlen}", size="10sp", color=colors["primary"], bold=True, height=dp(20), role="primary")
        self.terminal_addresses[key] = address
        panel.add_widget(address)

        status = criar_label("Aguardando início do container.", size="10sp", color=colors["muted"], height=dp(22), role="muted")
        self.terminal_statuses[key] = status
        panel.add_widget(status)

        panel.add_widget(criar_label("Shell Bash Debian completo com TTY, iproute2, ping, dig e tcpdump.", size="10sp", color=colors["muted"], height=dp(36), valign="top", role="muted"))
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
