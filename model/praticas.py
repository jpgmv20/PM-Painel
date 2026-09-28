"""Catálogo fixo de práticas e laboratório de lógica digital inspirado no Proteus."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial

from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.clock import Clock

from model.componentes import BotaoAcao, Cabecalho, LayoutFundo, Rodape


ATIVIDADE_PORTAS_DISPLAY = "portas-logicas-display-7-segmentos"

# Matérias práticas fazem parte do programa do PM-Painel. Professores não
# criam, editam nem removem itens deste catálogo.
PRACTICAS_FIXAS = (
    {
        "id": "arquitetura-de-computadores",
        "titulo": "Arquitetura de Computadores",
        "descricao": "Sistemas digitais, lógica booleana, circuitos e organização de computadores.",
        "atividades": (
            {
                "id": ATIVIDADE_PORTAS_DISPLAY,
                "titulo": "Portas lógicas e display de 7 segmentos",
                "descricao": (
                    "Monte e simule um circuito digital. Alterne as entradas BCD, conecte portas "
                    "lógicas e observe os segmentos do display em tempo real."
                ),
                "nivel": "Iniciante",
                "tempo": "15 a 25 min",
            },
        ),
    },
)

PORTAS = {
    "AND": ("AND", 2),
    "OR": ("OR", 2),
    "NOT": ("NOT", 1),
    "XOR": ("XOR", 2),
    "NAND": ("NAND", 2),
    "NOR": ("NOR", 2),
}

SEGMENTOS_POR_DIGITO = {
    0: frozenset("abcdef"), 1: frozenset("bc"), 2: frozenset("abdeg"),
    3: frozenset("abcdg"), 4: frozenset("bcfg"), 5: frozenset("acdfg"),
    6: frozenset("acdefg"), 7: frozenset("abc"), 8: frozenset("abcdefg"),
    9: frozenset("abcdfg"),
}


def calcular_porta(nome: str, entrada_a: bool, entrada_b: bool = False) -> bool:
    """Calcula a saída de uma porta lógica digital."""
    a, b = bool(entrada_a), bool(entrada_b)
    if nome == "AND":
        return a and b
    if nome == "OR":
        return a or b
    if nome == "NOT":
        return not a
    if nome == "XOR":
        return a != b
    if nome == "NAND":
        return not (a and b)
    if nome == "NOR":
        return not (a or b)
    raise ValueError(f"Porta lógica desconhecida: {nome}")


def segmentos_para_bcd(bits: dict[str, bool]) -> frozenset[str]:
    """Converte BCD (A é o bit menos significativo) em saídas a-g."""
    value = sum((1 << index) for index, name in enumerate("ABCD") if bits.get(name, False))
    return SEGMENTOS_POR_DIGITO.get(value, frozenset())


@dataclass(frozen=True)
class ResultadoCircuito:
    """Snapshot imutável do estado lógico calculado para um quadro do circuito."""

    saidas: dict[tuple[str, str], bool] = field(default_factory=dict)
    bcd: dict[str, bool] = field(default_factory=lambda: {bit: False for bit in "ABCD"})
    digito: int | None = None
    segmentos_por_display: dict[str, frozenset[str]] = field(default_factory=dict)


class SimuladorLogico:
    """Avalia uma rede combinacional sem acoplar a lógica à camada visual Kivy."""

    def __init__(self, componentes: list[dict], fios: list[dict]):
        self.componentes = {component["id"]: component for component in componentes}
        self.fios = fios
        self.entradas: dict[tuple[str, str], tuple[str, str]] = {}
        for wire in fios:
            self.entradas[wire["destino"]] = wire["origem"]
        self._cache: dict[tuple[str, str], bool] = {}
        self._resultado = ResultadoCircuito()

    def avaliar(self) -> ResultadoCircuito:
        decoder = next((item for item in self.componentes.values() if item["kind"] == "decoder"), None)
        bcd = {bit: self._ler_entrada(decoder["id"], bit, frozenset()) if decoder else False
               for bit in "ABCD"}
        digit = sum((1 << index) for index, bit in enumerate("ABCD") if bcd[bit]) if decoder else None

        for component in self.componentes.values():
            if component["kind"] == "input":
                self._saida(component["id"], "Q", frozenset())
            elif component["kind"] == "gate":
                self._saida(component["id"], "Q", frozenset())
            elif component["kind"] == "decoder":
                for segment in "abcdefg":
                    self._saida(component["id"], segment, frozenset())

        lit_segments: dict[str, frozenset[str]] = {}
        for display in (item for item in self.componentes.values() if item["kind"] == "display"):
            active = set()
            for segment in "abcdefg":
                source = self.entradas.get((display["id"], segment))
                # Displays comuns neste laboratório acendem com nível baixo.
                if source and not self._saida(source[0], source[1], frozenset()):
                    active.add(segment)
            lit_segments[display["id"]] = frozenset(active)

        self._resultado = ResultadoCircuito(self._cache.copy(), bcd, digit, lit_segments)
        return self._resultado

    def _ler_entrada(self, component_id: str, pin: str, visiting: frozenset[str]) -> bool:
        source = self.entradas.get((component_id, pin))
        return self._saida(source[0], source[1], visiting) if source else False

    def _saida(self, component_id: str, pin: str, visiting: frozenset[str]) -> bool:
        key = (component_id, pin)
        if key in self._cache:
            return self._cache[key]
        if component_id in visiting:
            return False  # Um ciclo combinacional sem memória não produz nível estável.
        component = self.componentes.get(component_id)
        if component is None:
            return False
        kind = component["kind"]
        if kind == "input":
            value = bool(component.get("value")) if pin == "Q" else False
        elif kind == "gate":
            next_path = visiting | {component_id}
            a = self._ler_entrada(component_id, "A", next_path)
            b = self._ler_entrada(component_id, "B", next_path)
            value = calcular_porta(component["gate"], a, b) if pin == "Q" else False
        elif kind == "decoder":
            next_path = visiting | {component_id}
            bits = {bit: self._ler_entrada(component_id, bit, next_path) for bit in "ABCD"}
            # O 74LS47 usa saídas ativas em nível baixo.
            value = pin not in segmentos_para_bcd(bits)
        else:
            value = False
        self._cache[key] = value
        return value


class EditorCircuito(Widget):
    """Editor esquemático com grade, componentes arrastáveis, fios e simulação."""

    status_texto = StringProperty("Simulação ao vivo ativa. Clique nas chaves para alterar as entradas.")
    estado_circuito = StringProperty("AO VIVO | BCD 0000 | Display: 0")
    PASSO_GRADE = dp(24)
    TEMPO_SEGURAR_PARA_ARRASTAR = .22
    TAMANHOS = {
        "input": (dp(108), dp(58)),
        "gate": (dp(112), dp(82)),
        "decoder": (dp(142), dp(174)),
        "display": (dp(112), dp(174)),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.componentes: list[dict] = []
        self.fios: list[dict] = []
        self.selecionado: str | None = None
        self._labels: dict[str, Label] = {}
        self._pin_labels: dict[tuple[str, str], Label] = {}
        self._pin_pendente: tuple[str, str] | None = None
        self._arrastando: dict | None = None
        self._segmentos_display: frozenset[str] = frozenset()
        self._digito: int | None = 0
        self._contador = 0
        self._resultado = ResultadoCircuito()
        self._avaliacao_pendente = None
        self.fio_selecionado: int | None = None
        self._criar_exemplo()
        self.bind(pos=self._redesenhar, size=self._redesenhar)
        Clock.schedule_once(self._redesenhar, 0)

    def _novo_componente(self, kind: str, nome: str, nx: float, ny: float, **data) -> dict:
        self._contador += 1
        item = {"id": f"c{self._contador}", "kind": kind, "nome": nome,
                "nx": nx, "ny": ny, **data}
        self.componentes.append(item)
        return item

    def _criar_exemplo(self, *_args):
        for label in self._labels.values():
            self.remove_widget(label)
        for label in self._pin_labels.values():
            self.remove_widget(label)
        self.componentes.clear()
        self.fios.clear()
        self._labels.clear()
        self._pin_labels.clear()
        self._contador = 0
        inputs = []
        for index, bit in enumerate("ABCD"):
            y = .77 - index * .18
            inputs.append(self._novo_componente("input", f"CHAVE {bit}", .08, y, bit=bit, value=False))
        gate = self._novo_componente("gate", "AND", .30, .50, gate="AND")
        decoder = self._novo_componente("decoder", "74LS47 BCD", .49, .48)
        display = self._novo_componente("display", "DISPLAY", .84, .48)
        self.fios.append({"origem": (inputs[0]["id"], "Q"), "destino": (gate["id"], "A")})
        self.fios.append({"origem": (inputs[1]["id"], "Q"), "destino": (gate["id"], "B")})
        self.fios.append({"origem": (gate["id"], "Q"), "destino": (decoder["id"], "A")})
        self.fios.append({"origem": (inputs[1]["id"], "Q"), "destino": (decoder["id"], "B")})
        for index, bit in ((2, "C"), (3, "D")):
            self.fios.append({"origem": (inputs[index]["id"], "Q"), "destino": (decoder["id"], bit)})
        for segment in "abcdefg":
            self.fios.append({"origem": (decoder["id"], segment), "destino": (display["id"], segment)})
        self.selecionado = None
        self._pin_pendente = None
        self.fio_selecionado = None
        self._segmentos_display = frozenset()
        self._digito = 0
        self.status_texto = "Exemplo pronto. As saídas serão atualizadas automaticamente a cada mudança."
        self.estado_circuito = "AO VIVO | BCD 0000 | Display: 0"
        self._solicitar_avaliacao()

    def adicionar_componente(self, tipo: str):
        if tipo == "input":
            count = sum(item["kind"] == "input" for item in self.componentes)
            component = self._novo_componente("input", f"CHAVE {count + 1}", .29 + (count % 3) * .08,
                                              .76 - (count % 4) * .17, value=False, bit="X")
        elif tipo in PORTAS:
            component = self._novo_componente("gate", PORTAS[tipo][0], .36, .51, gate=tipo)
        elif tipo == "decoder":
            component = self._novo_componente("decoder", "74LS47 BCD", .52, .50)
        elif tipo == "display":
            component = self._novo_componente("display", "DISPLAY", .72, .50)
        else:
            return
        self.selecionado = component["id"]
        self.status_texto = f"{component['nome']} adicionado. Arraste para posicionar e conecte os pinos."
        self._solicitar_avaliacao()

    def reiniciar_exemplo(self, *_args):
        self._criar_exemplo()

    def zerar_entradas(self, *_args):
        for component in self.componentes:
            if component["kind"] == "input":
                component["value"] = False
        self._solicitar_avaliacao("Entradas zeradas; os níveis e segmentos foram atualizados ao vivo.")

    def remover_selecionado(self, *_args):
        if not self.selecionado:
            self.status_texto = "Selecione um componente antes de removê-lo."
            return
        selected = self.selecionado
        self.componentes = [item for item in self.componentes if item["id"] != selected]
        self.fios = [wire for wire in self.fios if wire["origem"][0] != selected and wire["destino"][0] != selected]
        label = self._labels.pop(selected, None)
        if label is not None:
            self.remove_widget(label)
        self.selecionado = None
        self.fio_selecionado = None
        self._solicitar_avaliacao("Componente e conexões removidos.")

    def remover_fio_selecionado(self, *_args):
        if self.fio_selecionado is None or not (0 <= self.fio_selecionado < len(self.fios)):
            self.status_texto = "Selecione um fio no esquema antes de removê-lo."
            return
        self.fios.pop(self.fio_selecionado)
        self.fio_selecionado = None
        self._solicitar_avaliacao("Fio removido. As saídas foram recalculadas.")

    def limpar_selecao(self, *_args):
        self.selecionado = None
        self.fio_selecionado = None
        self._pin_pendente = None
        self.status_texto = "Seleção limpa. O circuito continua atualizando ao vivo."
        self._redesenhar()

    def _solicitar_avaliacao(self, mensagem: str | None = None):
        """Agrupa alterações do mesmo quadro e reavalia o circuito sem clique em Simular."""
        if mensagem:
            self.status_texto = mensagem
        if self._avaliacao_pendente is None:
            self._avaliacao_pendente = Clock.schedule_once(self._processar_avaliacao, 0)

    def _processar_avaliacao(self, _dt):
        self._avaliacao_pendente = None
        self._avaliar()

    def _iniciar_arrasto(self, touch):
        """Ativa o arraste apenas depois de manter o componente pressionado."""
        state = self._arrastando
        if state is None or state.get("touch") is not touch:
            return
        state["hold_event"] = None
        state["ativo"] = True
        self.status_texto = f"Movendo {state['component']['nome']}. Solte para encaixar na grade."
        start_x, start_y = state["start_pos"]
        if (touch.x - start_x) ** 2 + (touch.y - start_y) ** 2 > dp(4) ** 2:
            self._mover_componente(state["component"], touch)

    def _mover_componente(self, component: dict, touch):
        width, height = self.TAMANHOS[component["kind"]]
        available_x = max(1, self.width - width - dp(20))
        available_y = max(1, self.height - height - dp(20))
        px = max(self.x + dp(10), min(self.right - width - dp(10), touch.x - self._arrastando["dx"]))
        py = max(self.y + dp(10), min(self.top - height - dp(10), touch.y - self._arrastando["dy"]))
        component["nx"] = (px - self.x - dp(10)) / available_x
        component["ny"] = (py - self.y - dp(10)) / available_y
        self._redesenhar()

    @staticmethod
    def _distancia_ponto_segmento(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** .5
        ratio = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        nearest_x, nearest_y = x1 + ratio * dx, y1 + ratio * dy
        return ((px - nearest_x) ** 2 + (py - nearest_y) ** 2) ** .5

    def _fio_no_ponto(self, pos) -> int | None:
        for index in range(len(self.fios) - 1, -1, -1):
            wire = self.fios[index]
            source, target = self._componente(wire["origem"][0]), self._componente(wire["destino"][0])
            if not source or not target:
                continue
            start = self._pinos(source).get(wire["origem"][1])
            end = self._pinos(target).get(wire["destino"][1])
            if not start or not end:
                continue
            mid_x = (start[0] + end[0]) / 2
            segments = ((start[0], start[1], mid_x, start[1]),
                        (mid_x, start[1], mid_x, end[1]),
                        (mid_x, end[1], end[0], end[1]))
            if any(self._distancia_ponto_segmento(pos.x, pos.y, *segment) <= dp(8) for segment in segments):
                return index
        return None

    def _componente_no_ponto(self, pos) -> dict | None:
        for component in reversed(self.componentes):
            x, y, width, height = self._retangulo(component)
            if x <= pos.x <= x + width and y <= pos.y <= y + height:
                return component
        return None

    def _componente(self, component_id: str) -> dict | None:
        return next((item for item in self.componentes if item["id"] == component_id), None)

    def _retangulo(self, component: dict) -> tuple[float, float, float, float]:
        width, height = self.TAMANHOS[component["kind"]]
        available_x = max(0, self.width - width - dp(20))
        available_y = max(0, self.height - height - dp(20))
        x = self.x + dp(10) + available_x * component["nx"]
        y = self.y + dp(10) + available_y * component["ny"]
        return x, y, width, height

    def _pinos(self, component: dict) -> dict[str, tuple[float, float, str]]:
        x, y, width, height = self._retangulo(component)
        kind = component["kind"]
        if kind == "input":
            return {"Q": (x + width, y + height / 2, "out")}
        if kind == "gate":
            gate = component["gate"]
            inputs = ("A",) if gate == "NOT" else ("A", "B")
            result = {pin: (x, y + height * (.67 if pin == "A" else .33), "in") for pin in inputs}
            result["Q"] = (x + width, y + height / 2, "out")
            return result
        if kind == "decoder":
            result = {pin: (x, y + height * (.79 - index * .19), "in")
                      for index, pin in enumerate("ABCD")}
            result.update({pin: (x + width, y + height * (.87 - index * .12), "out")
                           for index, pin in enumerate("abcdefg")})
            return result
        return {pin: (x, y + height * (.87 - index * .12), "in")
                for index, pin in enumerate("abcdefg")}

    def _redesenhar(self, *_args):
        if self.width <= 0 or self.height <= 0:
            return
        for component in self.componentes:
            if component["id"] not in self._labels:
                label = Label(color=(.08, .16, .28, 1), bold=True, halign="center", valign="middle", font_size="10sp")
                self._labels[component["id"]] = label
                self.add_widget(label)
            label = self._labels[component["id"]]
            x, y, width, height = self._retangulo(component)
            if component["kind"] == "display":
                digit_text = str(self._digito) if self._digito is not None and self._digito < 10 else "--"
                label.text = f"DISPLAY 7 SEGMENTOS\nDÍGITO {digit_text}"
                label.color = (.88, .94, 1, 1)
                label.font_size = "9sp"
                label.size = (width, dp(36))
                label.pos = (x, y + height - dp(39))
            elif component["kind"] == "input":
                level = "ALTO · 1" if component["value"] else "BAIXO · 0"
                label.text = f"{component['nome']}\n{component['bit']}  |  {level}"
                label.color = (.06, .21, .37, 1)
                label.font_size = "9sp"
                label.size = (width, height)
                label.pos = (x, y)
            elif component["kind"] == "gate":
                output = int(self._resultado.saidas.get((component["id"], "Q"), False))
                inputs = "A -> Q" if component["gate"] == "NOT" else "A, B -> Q"
                label.text = f"{component['gate']}\n{inputs}\nQ = {output}"
                label.color = (.06, .21, .37, 1)
                label.font_size = "10sp"
                label.size = (width, height)
                label.pos = (x, y)
            elif component["kind"] == "decoder":
                bits = {name: int(self._resultado.bcd.get(name, False)) for name in "ABCD"}
                label.text = f"74LS47 · BCD\nA={bits['A']}  B={bits['B']}\nC={bits['C']}  D={bits['D']}"
                label.color = (.06, .21, .37, 1)
                label.font_size = "9sp"
                label.size = (width, height)
                label.pos = (x, y)
            else:
                label.text = component["nome"]
                label.size = (width, height)
                label.pos = (x, y)
        self._sincronizar_rotulos_pinos()
        self._desenhar_canvas()

    def _sincronizar_rotulos_pinos(self):
        valid_keys = {(component["id"], pin) for component in self.componentes
                      for pin in self._pinos(component)}
        for key in tuple(self._pin_labels):
            if key not in valid_keys:
                self.remove_widget(self._pin_labels.pop(key))
        for component in self.componentes:
            for pin, (px, py, direction) in self._pinos(component).items():
                key = (component["id"], pin)
                label = self._pin_labels.get(key)
                if label is None:
                    label = Label(color=(.21, .33, .50, 1), bold=True, font_size="8sp",
                                  halign="center", valign="middle")
                    self._pin_labels[key] = label
                    self.add_widget(label)
                label.text = pin
                label.size = (dp(18), dp(13))
                label.pos = (px - dp(19), py - dp(7)) if direction == "out" else (px + dp(2), py - dp(7))

    def _desenhar_canvas(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(.94, .97, 1, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            Color(.78, .84, .92, 1)
            step = self.PASSO_GRADE
            start_x = self.x + (step - (self.x % step)) % step
            start_y = self.y + (step - (self.y % step)) % step
            for xx in range(int(start_x), int(self.right), int(step)):
                Line(points=(xx, self.y, xx, self.top), width=.55)
            for yy in range(int(start_y), int(self.top), int(step)):
                Line(points=(self.x, yy, self.right, yy), width=.55)

            # Fios ortogonais com mudança de cor quando a saída está em nível alto.
            for wire_index, wire in enumerate(self.fios):
                source = self._componente(wire["origem"][0])
                target = self._componente(wire["destino"][0])
                if source is None or target is None:
                    continue
                source_pin = self._pinos(source).get(wire["origem"][1])
                target_pin = self._pinos(target).get(wire["destino"][1])
                if source_pin is None or target_pin is None:
                    continue
                high = self._resultado.saidas.get((source["id"], wire["origem"][1]), False)
                energized = not high if source["kind"] == "decoder" else high
                if wire_index == self.fio_selecionado:
                    Color(1, .66, .18, 1)
                else:
                    Color(.08, .68, .86, 1) if energized else Color(.28, .40, .56, .88)
                middle_x = (source_pin[0] + target_pin[0]) / 2
                Line(points=(source_pin[0], source_pin[1], middle_x, source_pin[1],
                             middle_x, target_pin[1], target_pin[0], target_pin[1]),
                     width=dp(2.8) if wire_index == self.fio_selecionado else dp(2) if energized else dp(1.3))
                Color(.08, .68, .86, 1) if energized else Color(.39, .49, .63, 1)
                Ellipse(pos=(middle_x - dp(3), source_pin[1] - dp(3)), size=(dp(6), dp(6)))
                Ellipse(pos=(middle_x - dp(3), target_pin[1] - dp(3)), size=(dp(6), dp(6)))

            # Símbolos dos componentes.
            for component in self.componentes:
                x, y, width, height = self._retangulo(component)
                selected = component["id"] == self.selecionado
                kind = component["kind"]
                if kind == "input":
                    Color(.77, .91, .99, 1) if component["value"] else Color(.90, .94, .98, 1)
                elif kind == "display":
                    Color(.08, .14, .24, 1)
                elif kind == "decoder":
                    Color(.87, .93, .99, 1)
                elif selected:
                    Color(.78, .89, 1, 1)
                else:
                    Color(.98, .99, 1, 1)
                RoundedRectangle(pos=(x, y), size=(width, height), radius=[dp(9)])
                Color(.05, .27, .55, 1) if selected else Color(.29, .40, .56, 1)
                Line(rounded_rectangle=(x, y, width, height, dp(9)), width=dp(2) if selected else dp(1.2))

                if kind == "display":
                    self._desenhar_display(x + width * .22, y + dp(13), width * .67,
                                           height - dp(48), component["id"])

                for pin_name, (px, py, direction) in self._pinos(component).items():
                    if direction == "out":
                        level = self._resultado.saidas.get((component["id"], pin_name), False)
                        Color(.12, .82, .56, 1) if level else Color(.36, .46, .60, 1)
                    elif self._pin_pendente == (component["id"], pin_name):
                        Color(1, .64, .12, 1)
                    else:
                        Color(.12, .30, .50, 1)
                    Ellipse(pos=(px - dp(3.3), py - dp(3.3)), size=(dp(6.6), dp(6.6)))

                if kind == "input":
                    led_color = (.12, .83, .58, 1) if component["value"] else (.42, .49, .60, 1)
                    Color(*led_color)
                    Ellipse(pos=(x + dp(8), y + height / 2 - dp(4)), size=(dp(8), dp(8)))

    def _desenhar_display(self, x: float, y: float, width: float, height: float, display_id: str):
        margin = min(dp(7), width * .08, height * .05)
        thickness = min(width * .17, height * .12)
        bar_width = max(thickness, width - 2 * margin - thickness)
        vertical_height = max(thickness, height / 2 - margin * 1.5 - thickness)
        left_x, right_x = x + margin, x + width - margin - thickness
        bar_x = x + margin + thickness * .5
        positions = {
            "a": (bar_x, y + height - margin - thickness, bar_width, thickness),
            "g": (bar_x, y + height / 2 - thickness / 2, bar_width, thickness),
            "d": (bar_x, y + margin, bar_width, thickness),
            "f": (left_x, y + height / 2 + thickness * .35, thickness, vertical_height),
            "b": (right_x, y + height / 2 + thickness * .35, thickness, vertical_height),
            "e": (left_x, y + margin + thickness, thickness, vertical_height),
            "c": (right_x, y + margin + thickness, thickness, vertical_height),
        }
        active_segments = self._resultado.segmentos_por_display.get(display_id, frozenset())
        for segment, geometry in positions.items():
            Color(.13, .75, .97, 1) if segment in active_segments else Color(.20, .27, .37, 1)
            RoundedRectangle(pos=geometry[:2], size=geometry[2:], radius=[thickness / 2])

    def _avaliar(self):
        self._resultado = SimuladorLogico(self.componentes, self.fios).avaliar()
        bits = self._resultado.bcd
        decoder = next((item for item in self.componentes if item["kind"] == "decoder"), None)
        self._digito = self._resultado.digito
        display = next((item for item in self.componentes if item["kind"] == "display"), None)
        self._segmentos_display = self._resultado.segmentos_por_display.get(
            display["id"], frozenset()
        ) if display else frozenset()
        binary_value = "".join(str(int(bits[name])) for name in "DCBA")
        shown_digit = (str(self._digito) if self._digito is not None and self._digito < 10 else "inválido") if decoder else "sem decodificador"
        active = "".join(sorted(self._segmentos_display)) or "nenhum"
        self.estado_circuito = f"AO VIVO  |  BCD {binary_value}  |  Display: {shown_digit}  |  Segmentos: {active}"
        self._redesenhar()

    def _encontrar_pino(self, pos) -> tuple[str, str, str] | None:
        for component in reversed(self.componentes):
            for pin, (x, y, direction) in self._pinos(component).items():
                if (x - pos.x) ** 2 + (y - pos.y) ** 2 <= dp(15) ** 2:
                    return component["id"], pin, direction
        return None

    def _conectar(self, first: tuple[str, str], second: tuple[str, str]):
        first_component, second_component = self._componente(first[0]), self._componente(second[0])
        if not first_component or not second_component or first == second:
            self.status_texto = "Conexão inválida. Escolha um pino de saída e um pino de entrada."
            return
        first_direction = self._pinos(first_component).get(first[1], (0, 0, ""))[2]
        second_direction = self._pinos(second_component).get(second[1], (0, 0, ""))[2]
        source, target = (first, second) if first_direction == "out" and second_direction == "in" else (second, first)
        source_component, target_component = self._componente(source[0]), self._componente(target[0])
        if not source_component or not target_component or source == target or source_component["id"] == target_component["id"]:
            self.status_texto = "Conexão inválida. Ligue a saída de um componente à entrada de outro."
            return
        if self._pinos(source_component).get(source[1], (0, 0, ""))[2] != "out" or self._pinos(target_component).get(target[1], (0, 0, ""))[2] != "in":
            self.status_texto = "Use um pino de saída como origem e um pino de entrada como destino."
            return
        self.fios = [wire for wire in self.fios if wire["destino"] != target]
        self.fios.append({"origem": source, "destino": target})
        self._pin_pendente = None
        self.fio_selecionado = len(self.fios) - 1
        self._solicitar_avaliacao(f"Fio conectado: {source_component['nome']} para {target_component['nome']}.")

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        pin = self._encontrar_pino(touch)
        if pin:
            component_id, pin_name, direction = pin
            if self._pin_pendente is None:
                self._pin_pendente = (component_id, pin_name)
                self.status_texto = f"Pino {pin_name} selecionado. Clique no pino de destino."
            else:
                self._conectar(self._pin_pendente, (component_id, pin_name))
            self._redesenhar()
            return True
        wire_index = self._fio_no_ponto(touch)
        component_hit = self._componente_no_ponto(touch)
        if wire_index is not None and not component_hit:
            self.fio_selecionado = wire_index
            self.selecionado = None
            self._pin_pendente = None
            wire = self.fios[wire_index]
            source = self._componente(wire["origem"][0])
            target = self._componente(wire["destino"][0])
            source_name = source["nome"] if source else "saída"
            target_name = target["nome"] if target else "entrada"
            self.status_texto = f"Fio selecionado: {source_name} para {target_name}. Use Remover fio para desconectar."
            self._redesenhar()
            return True
        for component in reversed(self.componentes):
            x, y, width, height = self._retangulo(component)
            if x <= touch.x <= x + width and y <= touch.y <= y + height:
                self.selecionado = component["id"]
                self._arrastando = {
                    "component": component,
                    "dx": touch.x - x,
                    "dy": touch.y - y,
                    "start_pos": (touch.x, touch.y),
                    "touch": touch,
                    "ativo": False,
                    "hold_event": None,
                }
                self._arrastando["hold_event"] = Clock.schedule_once(
                    lambda _dt, active_touch=touch: self._iniciar_arrasto(active_touch),
                    self.TEMPO_SEGURAR_PARA_ARRASTAR,
                )
                self.fio_selecionado = None
                if component["kind"] == "input":
                    self.status_texto = f"Chave {component['bit']} selecionada. Solte para alternar; segure para mover."
                else:
                    self.status_texto = f"{component['nome']} selecionado. Segure para mover; a grade facilita o alinhamento."
                touch.grab(self)
                self._redesenhar()
                return True
        if self._pin_pendente:
            self._pin_pendente = None
            self.status_texto = "Seleção de pino cancelada."
        self.selecionado = None
        self._redesenhar()
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self and self._arrastando:
            if not self._arrastando["ativo"]:
                return True
            self._mover_componente(self._arrastando["component"], touch)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self and self._arrastando:
            state = self._arrastando
            component = state["component"]
            if state["hold_event"] is not None:
                state["hold_event"].cancel()
            touch.ungrab(self)
            self._arrastando = None
            if state["ativo"]:
                width, height = self.TAMANHOS[component["kind"]]
                available_x = max(1, self.width - width - dp(20))
                available_y = max(1, self.height - height - dp(20))
                x, y, _, _ = self._retangulo(component)
                grid_x = round((x - self.x - dp(10)) / self.PASSO_GRADE) * self.PASSO_GRADE + self.x + dp(10)
                grid_y = round((y - self.y - dp(10)) / self.PASSO_GRADE) * self.PASSO_GRADE + self.y + dp(10)
                grid_x = max(self.x + dp(10), min(self.right - width - dp(10), grid_x))
                grid_y = max(self.y + dp(10), min(self.top - height - dp(10), grid_y))
                component["nx"] = (grid_x - self.x - dp(10)) / available_x
                component["ny"] = (grid_y - self.y - dp(10)) / available_y
                self._solicitar_avaliacao(f"{component['nome']} alinhado à grade. Conexões e sinais foram atualizados.")
            elif component["kind"] == "input" and self._componente_no_ponto(touch) is component:
                component["value"] = not component["value"]
                level = "ALTO (1)" if component["value"] else "BAIXO (0)"
                self._solicitar_avaliacao(
                    f"Chave {component['bit']} alterada para {level}; circuito recalculado ao vivo."
                )
            else:
                self._redesenhar()
            return True
        return super().on_touch_up(touch)


class IndicadorSinal(Widget):
    """Ponto de estado vetorial, sem depender de glifos ou emoji."""

    def __init__(self, rgba=(.10, .67, .42, 1), **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*rgba)
            self._dot = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._layout_dot, size=self._layout_dot)

    def _layout_dot(self, *_args):
        diameter = min(self.width, self.height, dp(8))
        self._dot.pos = (self.center_x - diameter / 2, self.center_y - diameter / 2)
        self._dot.size = (diameter, diameter)


class TelaPraticas(LayoutFundo):
    """Catálogo de matérias práticas do sistema e editor de circuitos."""

    titulo = StringProperty("Conteúdo Prático")
    status_texto = StringProperty("Matérias práticas disponíveis no sistema")
    secao = StringProperty("catalogo")

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=0, **kwargs)
        self.materia_atual: dict | None = None
        self.atividade_atual: dict | None = None
        self.editor: EditorCircuito | None = None
        self.add_widget(Cabecalho(titulo="Conteúdo Prático"))
        self._shell = BoxLayout(orientation="vertical", padding=(dp(24), dp(14)), size_hint=(1, 1))
        with self._shell.canvas.before:
            Color(.95, .97, 1, .98)
            self._shell_background = RoundedRectangle(pos=self._shell.pos, size=self._shell.size, radius=[dp(20)])
        self._shell.bind(pos=lambda item, value: setattr(self._shell_background, "pos", value),
                         size=lambda item, value: setattr(self._shell_background, "size", value))
        self.add_widget(self._shell)
        self.add_widget(Rodape(size_hint_y=None, height=dp(34)))
        self._back_bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        self._back_bar.add_widget(self._button("Voltar ao painel", self.voltar, variant="secondary", height=dp(36)))
        self._back_bar.add_widget(Widget())
        self._shell.add_widget(self._back_bar)
        self._mostrar_catalogo()

    def _button(self, text: str, action, *, variant="primary", height=dp(40), font_size="12sp"):
        button = BotaoAcao(text=text, variant=variant, size_hint_y=None, height=height,
                           color=(1, 1, 1, 1), bold=True, font_size=font_size,
                           padding=(dp(10), dp(6)))
        button.bind(on_release=lambda *_args: action())
        return button

    def _card(self, *, padding=dp(16), spacing=dp(8), color=(.065, .21, .47, 1)):
        card = BoxLayout(orientation="vertical", padding=padding, spacing=spacing, size_hint_y=None)
        with card.canvas.before:
            Color(*color)
            background = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(14)])
        card.bind(pos=lambda item, value: setattr(background, "pos", value),
                  size=lambda item, value: setattr(background, "size", value))
        card.bind(minimum_height=card.setter("height"))
        return card

    @staticmethod
    def _label(text, *, size="13sp", color=(.91, .95, 1, 1), bold=False, height=dp(28), valign="middle"):
        label = Label(text=text, size_hint_y=None, height=height, color=color, bold=bold,
                      font_size=size, halign="left", valign=valign)
        label.bind(width=lambda item, value: setattr(item, "text_size", (max(1, value), None)))
        return label

    def _reset_shell(self):
        self._shell.clear_widgets()
        self._shell.add_widget(self._back_bar)

    def _mostrar_catalogo(self):
        self.secao = "catalogo"
        self.titulo = "Conteúdo Prático"
        self.status_texto = "Matérias e exercícios fixos do PM-Painel"
        self._reset_shell()
        self._shell.add_widget(self._label("Laboratórios práticos", size="24sp", color=(.08, .20, .37, 1), bold=True, height=dp(38)))
        self._shell.add_widget(self._label(
            "Este catálogo é mantido junto ao sistema. As turmas e equipes criadas por professores ficam na área teórica.",
            size="13sp", color=(.31, .40, .54, 1), height=dp(32)))
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(6))
        grid = GridLayout(cols=2, spacing=dp(14), padding=(dp(2), dp(12)), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for materia in PRACTICAS_FIXAS:
            card = self._card()
            card.add_widget(self._label("MATÉRIA FIXA DO SISTEMA", size="10sp", color=(.57, .76, 1, 1), bold=True))
            card.add_widget(self._label(materia["titulo"], size="20sp", bold=True, height=dp(34)))
            card.add_widget(self._label(materia["descricao"], color=(.82, .88, .97, 1), height=dp(42), valign="top"))
            card.add_widget(self._label(f"{len(materia['atividades'])} atividade prática disponível", size="11sp", color=(.68, .81, 1, 1)))
            card.add_widget(self._button("Abrir matéria", partial(self._abrir_materia, materia["id"])))
            grid.add_widget(card)
        scroll.add_widget(grid)
        self._shell.add_widget(scroll)

    def _abrir_materia(self, materia_id: str):
        self.materia_atual = next((item for item in PRACTICAS_FIXAS if item["id"] == materia_id), None)
        if not self.materia_atual:
            self._mostrar_catalogo()
            return
        self.secao = "materia"
        self.titulo = self.materia_atual["titulo"]
        self.status_texto = "Matéria prática fixa do sistema"
        self._reset_shell()
        toolbar = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        toolbar.add_widget(self._button("Voltar às matérias práticas", self._mostrar_catalogo, variant="secondary"))
        toolbar.add_widget(self._label(self.materia_atual["titulo"], size="22sp", color=(.08, .20, .37, 1), bold=True, height=dp(42)))
        self._shell.add_widget(toolbar)
        self._shell.add_widget(self._label(self.materia_atual["descricao"], size="14sp", color=(.31, .40, .54, 1), height=dp(45)))
        for activity in self.materia_atual["atividades"]:
            card = self._card()
            card.add_widget(self._label("LABORATÓRIO INTERATIVO", size="10sp", color=(.57, .76, 1, 1), bold=True))
            card.add_widget(self._label(activity["titulo"], size="19sp", bold=True, height=dp(34)))
            card.add_widget(self._label(activity["descricao"], color=(.82, .88, .97, 1), height=dp(42)))
            card.add_widget(self._label(f"{activity['nivel']}  |  {activity['tempo']}  |  Simulação digital", size="11sp", color=(.68, .81, 1, 1)))
            card.add_widget(self._button("Abrir laboratório", partial(self._abrir_atividade, activity["id"])))
            self._shell.add_widget(card)

    def _abrir_atividade(self, activity_id: str):
        if not self.materia_atual:
            return
        self.atividade_atual = next((item for item in self.materia_atual["atividades"] if item["id"] == activity_id), None)
        if not self.atividade_atual:
            return
        self.secao = "atividade"
        self.titulo = "Laboratório - Lógica digital"
        self._mostrar_editor()

    def _mostrar_editor(self):
        self._reset_shell()
        toolbar = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(7))
        toolbar.add_widget(self._button("Voltar", partial(self._abrir_materia, self.materia_atual["id"]), variant="secondary", height=dp(38)))
        toolbar.add_widget(self._label("Editor de circuito", size="17sp", color=(.08, .20, .37, 1), bold=True, height=dp(38)))
        toolbar.add_widget(self._indicador_ao_vivo())
        toolbar.add_widget(Widget())
        toolbar.add_widget(self._button("Zerar entradas", self._zerar_entradas, variant="secondary", height=dp(38)))
        toolbar.add_widget(self._button("Remover fio", self._remover_fio_selecionado, variant="secondary", height=dp(38)))
        toolbar.add_widget(self._button("Remover componente", self._remover_selecionado, variant="danger", height=dp(38)))
        toolbar.add_widget(self._button("Restaurar exemplo", self._reiniciar_exemplo, variant="secondary", height=dp(38)))
        self._shell.add_widget(toolbar)

        workspace = BoxLayout(spacing=dp(10))
        palette_scroll = ScrollView(size_hint_x=None, width=dp(184), do_scroll_x=False, bar_width=dp(4))
        palette = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6), padding=(dp(8), dp(8)))
        palette.bind(minimum_height=palette.setter("height"))
        self._painel(palette, "Componentes", "Adicione blocos ao esquema.")
        for key, title in (("input", "Chave digital"), ("AND", "Porta AND"), ("OR", "Porta OR"),
                           ("NOT", "Porta NOT"), ("XOR", "Porta XOR"), ("NAND", "Porta NAND"),
                           ("NOR", "Porta NOR"), ("decoder", "Decodificador 74LS47"),
                           ("display", "Display 7 segmentos")):
            palette.add_widget(self._button("+  " + title, partial(self._adicionar_componente, key),
                                             variant="secondary", height=dp(38), font_size="11sp"))
        self._painel(palette, "Como usar", "Segure um bloco para mover. Clique em dois pinos para criar um fio. Solte uma chave para alternar 0/1.")
        palette_scroll.add_widget(palette)
        workspace.add_widget(palette_scroll)

        center = BoxLayout(orientation="vertical", spacing=dp(6))
        self.editor = EditorCircuito()
        self.editor.bind(status_texto=self._atualizar_status)
        self.editor.bind(estado_circuito=self._atualizar_estado)
        center.add_widget(self.editor)
        live_readout = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(50), spacing=dp(2))
        self._state_label = self._label(self.editor.estado_circuito, size="11sp", color=(.04, .40, .34, 1), bold=True, height=dp(24))
        self._status_label = self._label(self.editor.status_texto, size="10sp", color=(.33, .42, .55, 1), height=dp(22))
        live_readout.add_widget(self._state_label)
        live_readout.add_widget(self._status_label)
        center.add_widget(live_readout)
        workspace.add_widget(center)

        info_scroll = ScrollView(size_hint_x=None, width=dp(215), do_scroll_x=False, bar_width=dp(4))
        info = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(7), padding=(dp(8), dp(8)))
        info.bind(minimum_height=info.setter("height"))
        self._painel(info, "Circuito ao vivo", "O simulador começa ligado. Toda mudança recalcula as saídas automaticamente.")
        self._texto_info(info, "1. A e B passam pela porta AND; a saída segue para o bit A do 74LS47.")
        self._texto_info(info, "2. Ligue as saídas a-g do decodificador ao display.")
        self._texto_info(info, "3. A é o bit menos significativo; D é o mais significativo.")
        self._texto_info(info, "4. Saídas do 74LS47 são ativas em nível baixo: 0 acende o segmento.")
        self._texto_info(info, "5. Solte uma chave para formar 0-9 em BCD; segure para mover sem alterar o sinal.")
        self._texto_info(info, "6. Clique em um fio para selecioná-lo e desconectá-lo.")
        self._texto_info(info, "7. Componentes encaixam na grade ao soltar; Restaurar exemplo desfaz as alterações.")
        self._painel(info, "Legenda visual", "Verde = saída ALTA\nAzul = sinal ativo\nÂmbar = item selecionado\nPinos ficam alinhados à grade ao soltar.")
        self._painel(info, "Níveis lógicos", "0 = BAIXO\n1 = ALTO\nBCD 1010-1111 não representa um dígito decimal.")
        info_scroll.add_widget(info)
        workspace.add_widget(info_scroll)
        self._shell.add_widget(workspace)

    def _painel(self, parent, title: str, description: str):
        card = self._card(padding=dp(10), spacing=dp(5), color=(.08, .25, .52, 1))
        card.add_widget(self._label(title, size="13sp", bold=True, height=dp(25)))
        card.add_widget(self._label(description, size="10sp", color=(.82, .89, .98, 1), height=dp(54), valign="top"))
        parent.add_widget(card)

    def _indicador_ao_vivo(self):
        badge = BoxLayout(orientation="horizontal", size_hint=(None, None), size=(dp(154), dp(32)),
                          spacing=dp(7), padding=(dp(9), dp(3)))
        with badge.canvas.before:
            Color(.84, .97, .91, 1)
            background = RoundedRectangle(pos=badge.pos, size=badge.size, radius=[dp(15)])
        badge.bind(pos=lambda item, value: setattr(background, "pos", value),
                   size=lambda item, value: setattr(background, "size", value))
        badge.add_widget(IndicadorSinal(size_hint=(None, None), size=(dp(9), dp(22))))
        label = Label(text="SIMULAÇÃO AO VIVO", color=(.05, .40, .29, 1), bold=True, font_size="9sp")
        badge.add_widget(label)
        return badge

    def _texto_info(self, parent, text: str):
        parent.add_widget(self._label(text, size="10sp", color=(.24, .35, .51, 1), height=dp(66), valign="top"))

    def _atualizar_status(self, _editor, value):
        if hasattr(self, "_status_label"):
            self._status_label.text = value

    def _atualizar_estado(self, _editor, value):
        if hasattr(self, "_state_label"):
            self._state_label.text = value

    def _adicionar_componente(self, kind: str):
        if self.editor:
            self.editor.adicionar_componente(kind)

    def _remover_fio_selecionado(self):
        if self.editor:
            self.editor.remover_fio_selecionado()

    def _zerar_entradas(self):
        if self.editor:
            self.editor.zerar_entradas()

    def _reiniciar_exemplo(self):
        if self.editor:
            self.editor.reiniciar_exemplo()

    def _remover_selecionado(self):
        if self.editor:
            self.editor.remover_selecionado()

    def voltar(self):
        manager = self._app_manager()
        if manager:
            manager.transition.direction = "right"
            manager.current = "principal"

    @staticmethod
    def _app_manager():
        from kivy.app import App
        app = App.get_running_app()
        return getattr(app, "root", None) if app else None
