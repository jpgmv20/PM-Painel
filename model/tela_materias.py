"""Experiência de equipes educacionais para a área de matérias."""
from __future__ import annotations

import os
import re
from functools import partial
from pathlib import Path

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
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
from kivy.uix.image import Image
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.widget import Widget

from model.componentes import BotaoAcao, CampoTexto, IconeUI, LayoutFundo
from model.materias import Comentario, Conteudo, Materia, Publicacao, Topico, Trabalho


PROJECT_DIR = Path(__file__).resolve().parents[1]


def _icone_materia(materia, tamanho=dp(42)):
    """Prioriza o arquivo da matéria em assets/icon e usa MDI como fallback."""
    imagem = str(getattr(materia, "imagem", "") or "").strip()
    icon_root = (PROJECT_DIR / "assets" / "icon").resolve()
    candidates = []
    if imagem:
        raw = Path(imagem)
        candidates.append((PROJECT_DIR / raw).resolve() if raw.is_absolute() else (
            PROJECT_DIR / raw if raw.parts and raw.parts[0].casefold() == "assets"
            else icon_root / raw
        ).resolve())
    for key in (getattr(materia, "id", ""), getattr(materia, "nome", "")):
        stem = Path(str(key or "")).name
        if stem:
            if Path(stem).suffix:
                candidates.append((icon_root / stem).resolve())
            else:
                candidates.extend((icon_root / f"{stem}{extension}").resolve()
                                  for extension in (".png", ".jpg", ".jpeg", ".webp", ".svg"))
    source = ""
    for candidate in candidates:
        try:
            candidate.relative_to(icon_root)
        except ValueError:
            continue
        if candidate.is_file():
            source = str(candidate)
            break
    if source:
        return Image(source=source, size_hint=(None, None), size=(tamanho, tamanho),
                     allow_stretch=True, keep_ratio=True)

    name = f"{getattr(materia, 'nome', '')} {getattr(materia, 'categoria', '')}".casefold()
    fallback = getattr(materia, "icone", "") or ""
    if not fallback or fallback == "book-open-page-variant":
        if "rede" in name or "internet" in name:
            fallback = "lan"
        elif "arquitetura" in name or "comput" in name:
            fallback = "memory"
        elif "program" in name or "desenvolv" in name:
            fallback = "code-tags"
        elif "matem" in name:
            fallback = "calculator-variant"
        else:
            fallback = "book-open-page-variant"
    return IconeUI(nome=fallback, size_hint=(None, None), size=(tamanho, tamanho),
                   font_size=tamanho * .72, color=(.48, .72, 1, 1))


class TeamCard(ButtonBehavior, BoxLayout):
    """Card clicável que abre a equipe ao tocar nele."""

    pass


class LessonCard(ButtonBehavior, BoxLayout):
    """Item clicável de aula no menu lateral da documentação teórica."""

    pass

def markdown_inline_to_kivy_markup(text: str) -> str:
    """Converte markdown inline (*itálico*, **negrito**, `código`, etc.) para marcação Kivy."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r"[color=61afef][b]\1[/b][/color]", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"[b]\1[/b]", text)
    text = re.sub(r"__([^_]+)__", r"[b]\1[/b]", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"[i]\1[/i]", text)
    text = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"[i]\1[/i]", text)
    text = re.sub(r"~~([^~]+)~~", r"[s]\1[/s]", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"[color=4ea8de][u]\1[/u][/color]", text)
    return text


def parse_markdown_to_widgets(text: str, paleta: dict) -> list[Widget]:
    """Interpreta texto markdown e gera uma lista de widgets estilizados para o Kivy."""
    widgets = []
    lines = text.split("\n")
    i = 0
    n = len(lines)

    in_code_block = False
    code_lines = []
    code_lang = ""

    while i < n:
        raw_line = lines[i]
        line = raw_line.rstrip()

        # Blocos de código (```lang ... ```)
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line.strip().lstrip("`").strip().upper()
                code_lines = []
                i += 1
                continue
            else:
                in_code_block = False
                code_content = "\n".join(code_lines)
                code_card = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4), padding=dp(12))
                code_card.bind(minimum_height=code_card.setter("height"))
                with code_card.canvas.before:
                    Color(0.04, 0.07, 0.12, 0.95)
                    c_bg = RoundedRectangle(pos=code_card.pos, size=code_card.size, radius=[dp(8)])
                    Color(*paleta.get("card_border", (0.2, 0.3, 0.5, 0.5)))
                    c_line = Line(rounded_rectangle=(*code_card.pos, *code_card.size, dp(8)), width=dp(1))
                def update_cc(_i, _v, b=c_bg, l=c_line, card=code_card):
                    b.pos = card.pos
                    b.size = card.size
                    l.rounded_rectangle = (*card.pos, *card.size, dp(8))
                code_card.bind(pos=update_cc, size=update_cc)

                if code_lang:
                    head_row = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(6))
                    head_row.add_widget(IconeUI(nome="code-tags", size_hint=(None, None), size=(dp(14), dp(14)), font_size=dp(13), color=paleta.get("accent", (0.35, 0.65, 1, 1))))
                    head_row.add_widget(Label(text=code_lang, color=paleta.get("accent", (0.35, 0.65, 1, 1)), bold=True, font_size="10sp", halign="left"))
                    code_card.add_widget(head_row)

                code_lbl = Label(text=code_content, color=(0.45, 0.88, 0.72, 1), font_size="12sp",
                                 halign="left", valign="top", size_hint_y=None)
                code_lbl.bind(width=lambda _i, w, l=code_lbl: setattr(l, "text_size", (w, None)))
                code_lbl.bind(texture_size=lambda _i, sz, l=code_lbl: setattr(l, "height", sz[1]))
                code_card.add_widget(code_lbl)
                widgets.append(code_card)
                i += 1
                continue

        if in_code_block:
            code_lines.append(raw_line)
            i += 1
            continue

        # Linha divisória horizontal (--- ou ***)
        if re.match(r"^\s*([*\-_])\s*(\1\s*){2,}$", line):
            div = Widget(size_hint_y=None, height=dp(18))
            with div.canvas.before:
                Color(*paleta.get("card_border", (0.2, 0.3, 0.5, 0.5)))
                d_rect = Rectangle(pos=(div.x, div.y + dp(8)), size=(div.width, dp(1)))
            div.bind(pos=lambda _i, v, r=d_rect: setattr(r, "pos", (v[0], v[1] + dp(8))),
                     size=lambda _i, v, r=d_rect: setattr(r, "size", (v[0], dp(1))))
            widgets.append(div)
            i += 1
            continue

        # Cabeçalhos (#, ##, ###, ####)
        h_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h_match:
            level = len(h_match.group(1))
            heading_text = markdown_inline_to_kivy_markup(h_match.group(2))
            if level == 1:
                f_size = "19sp"
                color = paleta.get("text_primary", (1, 1, 1, 1))
                top_pad = dp(16)
            elif level == 2:
                f_size = "16sp"
                color = paleta.get("accent", (0.35, 0.65, 1, 1))
                top_pad = dp(12)
            elif level == 3:
                f_size = "14sp"
                color = paleta.get("text_primary", (1, 1, 1, 1))
                top_pad = dp(8)
            else:
                f_size = "13sp"
                color = paleta.get("text_secondary", (0.8, 0.85, 0.9, 1))
                top_pad = dp(6)

            h_box = BoxLayout(orientation="vertical", size_hint_y=None, padding=(0, top_pad, 0, dp(4)))
            h_box.bind(minimum_height=h_box.setter("height"))
            h_lbl = Label(text=heading_text, markup=True, font_size=f_size, bold=True,
                          color=color, halign="left", valign="top", size_hint_y=None)
            h_lbl.bind(width=lambda _i, w, l=h_lbl: setattr(l, "text_size", (w, None)))
            h_lbl.bind(texture_size=lambda _i, sz, l=h_lbl: setattr(l, "height", sz[1]))
            h_box.add_widget(h_lbl)
            widgets.append(h_box)
            i += 1
            continue

        # Citação / Callout (> texto)
        if line.startswith(">"):
            quote_lines = [line.lstrip(">").strip()]
            while i + 1 < n and lines[i + 1].startswith(">"):
                i += 1
                quote_lines.append(lines[i].lstrip(">").strip())
            q_text = markdown_inline_to_kivy_markup(" ".join(quote_lines))
            q_card = BoxLayout(orientation="vertical", size_hint_y=None, padding=(dp(14), dp(10)), spacing=dp(4))
            q_card.bind(minimum_height=q_card.setter("height"))
            with q_card.canvas.before:
                Color(*paleta.get("callout_bg", (0.08, 0.16, 0.28, 0.5)))
                qb = RoundedRectangle(pos=q_card.pos, size=q_card.size, radius=[dp(8)])
                Color(*paleta.get("accent", (0.35, 0.65, 1, 1)))
                ql = RoundedRectangle(pos=(q_card.x, q_card.y), size=(dp(4), q_card.height), radius=[dp(2)])
            def update_qc(_i, _v, b=qb, l=ql, card=q_card):
                b.pos = card.pos
                b.size = card.size
                l.pos = (card.x, card.y)
                l.size = (dp(4), card.height)
            q_card.bind(pos=update_qc, size=update_qc)
            q_lbl = Label(text=q_text, markup=True, font_size="13sp", italic=True,
                          color=paleta.get("text_secondary", (0.8, 0.85, 0.9, 1)), halign="left", valign="top", size_hint_y=None)
            q_lbl.bind(width=lambda _i, w, l=q_lbl: setattr(l, "text_size", (w, None)))
            q_lbl.bind(texture_size=lambda _i, sz, l=q_lbl: setattr(l, "height", sz[1]))
            q_card.add_widget(q_lbl)
            widgets.append(q_card)
            i += 1
            continue

        # Lista com marcadores (* item ou - item)
        bullet_match = re.match(r"^\s*[\*\-]\s+(.*)$", line)
        if bullet_match:
            item_text = markdown_inline_to_kivy_markup(bullet_match.group(1))
            row = BoxLayout(orientation="horizontal", size_hint_y=None, spacing=dp(8), padding=(dp(8), dp(2)))
            b_dot = Label(text="•", color=paleta.get("accent", (0.35, 0.65, 1, 1)), bold=True,
                          font_size="16sp", size_hint=(None, None), size=(dp(12), dp(20)), pos_hint={"top": 1})
            row.add_widget(b_dot)
            i_lbl = Label(text=item_text, markup=True, font_size="13sp",
                          color=paleta.get("text_primary", (1, 1, 1, 1)), halign="left", valign="top", size_hint_y=None)
            i_lbl.bind(width=lambda _i, w, l=i_lbl: setattr(l, "text_size", (w, None)))
            i_lbl.bind(texture_size=lambda _i, sz, l=i_lbl, r=row: (setattr(l, "height", sz[1]), setattr(r, "height", max(dp(22), sz[1] + dp(4)))))
            row.add_widget(i_lbl)
            widgets.append(row)
            i += 1
            continue

        # Lista numerada (1. item)
        num_match = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        if num_match:
            num = num_match.group(1)
            item_text = markdown_inline_to_kivy_markup(num_match.group(2))
            row = BoxLayout(orientation="horizontal", size_hint_y=None, spacing=dp(8), padding=(dp(8), dp(2)))
            num_lbl = Label(text=f"{num}.", color=paleta.get("accent", (0.35, 0.65, 1, 1)), bold=True,
                            font_size="13sp", size_hint=(None, None), size=(dp(24), dp(20)), pos_hint={"top": 1})
            row.add_widget(num_lbl)
            i_lbl = Label(text=item_text, markup=True, font_size="13sp",
                          color=paleta.get("text_primary", (1, 1, 1, 1)), halign="left", valign="top", size_hint_y=None)
            i_lbl.bind(width=lambda _i, w, l=i_lbl: setattr(l, "text_size", (w, None)))
            i_lbl.bind(texture_size=lambda _i, sz, l=i_lbl, r=row: (setattr(l, "height", sz[1]), setattr(r, "height", max(dp(22), sz[1] + dp(4)))))
            row.add_widget(i_lbl)
            widgets.append(row)
            i += 1
            continue

        # Linha vazia
        if not line.strip():
            i += 1
            continue

        # Parágrafo normal
        para_lines = [line]
        while i + 1 < n and lines[i + 1].strip() and not lines[i + 1].strip().startswith(("#", "```", "---", "* ", "- ", "> ")) and not re.match(r"^\s*\d+\.\s+", lines[i + 1]):
            i += 1
            para_lines.append(lines[i].strip())
        para_text = markdown_inline_to_kivy_markup(" ".join(para_lines))
        p_lbl = Label(text=para_text, markup=True, font_size="13sp",
                      color=paleta.get("text_primary", (1, 1, 1, 1)), halign="left", valign="top", size_hint_y=None)
        p_lbl.bind(width=lambda _i, w, l=p_lbl: setattr(l, "text_size", (w, None)))
        p_lbl.bind(texture_size=lambda _i, sz, l=p_lbl: setattr(l, "height", sz[1] + dp(6)))
        widgets.append(p_lbl)
        i += 1

    return widgets



class TelaMaterias(LayoutFundo):
    """Lista equipes e renderiza uma experiência interna em seções modernas."""

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

    def _is_dark(self) -> bool:
        app = App.get_running_app()
        if app and hasattr(app, "settings") and getattr(app.settings, "theme", None):
            return app.settings.theme.casefold() in {"escuro", "dark"}
        surface = getattr(app, "theme_surface", None) if app else None
        return bool(surface and surface[0] < 0.5)

    def _paleta(self) -> dict:
        escuro = self._is_dark()
        if escuro:
            return {
                "card_bg": (0.09, 0.13, 0.21, 1),
                "card_border": (0.19, 0.27, 0.39, 0.85),
                "surface_alt": (0.13, 0.18, 0.27, 1),
                "surface_input": (0.07, 0.10, 0.17, 1),
                "text_primary": (0.92, 0.95, 1, 1),
                "text_secondary": (0.68, 0.77, 0.89, 1),
                "text_muted": (0.46, 0.56, 0.70, 1),
                "accent": (0.42, 0.69, 1, 1),
                "accent_soft": (0.18, 0.40, 0.78, 0.22),
                "composer_bg": (0.10, 0.15, 0.23, 1),
                "bubble_own": (0.16, 0.30, 0.50, 1),
                "bubble_other": (0.12, 0.17, 0.26, 1),
                "bubble_border": (0.22, 0.33, 0.48, 0.8),
                "callout_bg": (0.10, 0.22, 0.38, 0.45),
                "callout_border": (0.30, 0.60, 1, 1),
                "badge_bg": (0.14, 0.22, 0.35, 1),
            }
        else:
            return {
                "card_bg": (1, 1, 1, 1),
                "card_border": (0.83, 0.88, 0.95, 1),
                "surface_alt": (0.94, 0.96, 0.99, 1),
                "surface_input": (0.97, 0.98, 1, 1),
                "text_primary": (0.08, 0.16, 0.28, 1),
                "text_secondary": (0.30, 0.40, 0.54, 1),
                "text_muted": (0.46, 0.55, 0.68, 1),
                "accent": (0.08, 0.38, 0.78, 1),
                "accent_soft": (0.88, 0.93, 1, 1),
                "composer_bg": (1, 1, 1, 1),
                "bubble_own": (0.88, 0.94, 1, 1),
                "bubble_other": (0.95, 0.97, 1, 1),
                "bubble_border": (0.82, 0.88, 0.96, 1),
                "callout_bg": (0.93, 0.96, 1, 1),
                "callout_border": (0.16, 0.46, 0.88, 1),
                "badge_bg": (0.90, 0.94, 0.99, 1),
            }

    def _badge_pill(self, texto: str, icone: str = "", cor_texto=None, cor_fundo=None, font_size="10sp", height=dp(24)):
        paleta = self._paleta()
        txt_col = cor_texto or paleta["accent"]
        bg_col = cor_fundo or paleta["accent_soft"]
        box = BoxLayout(size_hint=(None, None), height=height, spacing=dp(5), padding=(dp(8), dp(2)))
        with box.canvas.before:
            Color(*bg_col)
            bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[height / 2])
        box.bind(pos=lambda _item, val: setattr(bg, "pos", val),
                 size=lambda _item, val: setattr(bg, "size", val))
        if icone:
            box.add_widget(IconeUI(nome=icone, size_hint=(None, None), size=(dp(14), dp(14)),
                                  font_size=dp(13), color=txt_col, pos_hint={"center_y": 0.5}))
        label = Label(text=str(texto), color=txt_col, bold=True, font_size=font_size,
                      size_hint_x=None, halign="center", valign="middle")
        label.bind(texture_size=lambda _i, sz: setattr(label, "width", sz[0]))
        box.add_widget(label)
        box.bind(minimum_width=box.setter("width"))
        return box

    @staticmethod
    def _obter_info_arquivo(nome: str):
        ext = Path(nome).suffix.lower()
        if ext == ".pdf":
            return "file-pdf-box", (0.90, 0.22, 0.22, 1), (0.96, 0.88, 0.88, 1)
        elif ext in {".doc", ".docx", ".odt", ".rtf", ".txt"}:
            return ("file-word-box" if "doc" in ext else "file-document-outline"), (0.12, 0.44, 0.88, 1), (0.88, 0.93, 1, 1)
        elif ext in {".xls", ".xlsx", ".csv", ".ods"}:
            return "file-excel-box", (0.10, 0.65, 0.32, 1), (0.86, 0.96, 0.90, 1)
        elif ext in {".ppt", ".pptx", ".odp"}:
            return "file-powerpoint-box", (0.94, 0.45, 0.10, 1), (1, 0.92, 0.85, 1)
        elif ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}:
            return "file-image-outline", (0.05, 0.65, 0.75, 1), (0.86, 0.96, 0.98, 1)
        elif ext in {".zip", ".rar", ".7z", ".tar", ".gz"}:
            return "folder-zip-outline", (0.85, 0.60, 0.10, 1), (1, 0.95, 0.85, 1)
        elif ext in {".py", ".js", ".html", ".css", ".json", ".c", ".cpp", ".java", ".sql"}:
            return "code-tags", (0.55, 0.25, 0.85, 1), (0.93, 0.88, 1, 1)
        elif ext in {".mp4", ".mkv", ".avi", ".mov"}:
            return "file-video-outline", (0.85, 0.15, 0.45, 1), (0.98, 0.86, 0.92, 1)
        elif ext in {".mp3", ".wav", ".ogg", ".flac"}:
            return "file-music-outline", (0.20, 0.65, 0.55, 1), (0.88, 0.96, 0.94, 1)
        return "file-document-outline", (0.35, 0.48, 0.65, 1), (0.90, 0.93, 0.97, 1)

    @staticmethod
    def _obter_badge_tipo_post(tipo: str):
        t = str(tipo or "").casefold()
        if t == "aula":
            return "AULA", "school", (0.12, 0.42, 0.88, 1), (0.12, 0.42, 0.88, 0.14)
        elif t == "aviso":
            return "AVISO", "bullhorn", (0.90, 0.48, 0.05, 1), (0.90, 0.48, 0.05, 0.14)
        elif t in {"pergunta", "duvida", "dúvida"}:
            return "DÚVIDA", "help-circle-outline", (0.55, 0.22, 0.85, 1), (0.55, 0.22, 0.85, 0.14)
        elif t in {"conteudo", "material"}:
            return "MATERIAL", "file-document-outline", (0.08, 0.60, 0.32, 1), (0.08, 0.60, 0.32, 0.14)
        elif t in {"tarefa", "atividade", "trabalho"}:
            return "ATIVIDADE", "clipboard-text-outline", (0.05, 0.55, 0.68, 1), (0.05, 0.55, 0.68, 0.14)
        return (tipo or "POST").upper(), "comment-text-outline", (0.35, 0.45, 0.60, 1), (0.35, 0.45, 0.60, 0.14)

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
        manager.transition = SlideTransition(direction="right", duration=.25)
        manager.current = "principal"

    def _clear(self):
        self.ids.conteudo.clear_widgets()
        return self.ids.conteudo

    def _button(self, text, action, danger=False, compact=False, variant=None):
        variant = "danger" if danger else variant or "primary"
        button = BotaoAcao(text=text, variant=variant,
            size_hint_y=None, height=dp(36 if compact else 46),
            font_size="13sp", bold=True,
            padding=(dp(12), dp(6)))
        text_lower = str(text).casefold()
        if "abrir" in text_lower or "continuar" in text_lower or "entrar" in text_lower or "ver" in text_lower or "ir para" in text_lower:
            button.icone = "arrow-right"
            button.icon_position = "right"
        elif "voltar" in text_lower or "anterior" in text_lower or "‹" in text or "turmas" in text_lower:
            button.icone = "arrow-left"
            button.icon_position = "left"
        button.bind(on_release=lambda _instance: action())
        return button

    def _text(self, value, height=28, bold=False, color=None, size="14sp", preserve_color=False):
        paleta = self._paleta()
        if color is None:
            color = paleta["text_primary"] if bold else paleta["text_secondary"]
        elif not preserve_color and (color == (.91, .95, 1, 1) or (color[0] > 0.8 and not self._is_dark())):
            color = paleta["text_primary"] if bold else paleta["text_secondary"]
        label = Label(text=str(value), size_hint_y=None, height=dp(height), color=color, bold=bold, font_size=size, halign="left", valign="middle")
        label.bind(width=lambda item, width: setattr(item, "text_size", (width, None)))
        return label

    def _paragraph(self, value, color=None, size="13sp", minimum=30):
        paleta = self._paleta()
        text_col = color if color is not None else paleta["text_secondary"]
        label = Label(text=str(value), size_hint_y=None, height=dp(minimum), color=text_col, font_size=size,
                      halign="left", valign="top", padding=(0, dp(4)))
        label.bind(width=lambda item, width: setattr(item, "text_size", (max(1, width), None)))
        label.bind(texture_size=lambda item, measured: setattr(item, "height", max(dp(minimum), measured[1] + dp(8))))
        return label

    def _avatar(self, initials, diameter=dp(42), color=None):
        paleta = self._paleta()
        bg_col = color or paleta["accent"]
        avatar = Label(text=initials or "PM", size_hint=(None, None), size=(diameter, diameter),
                       color=(1, 1, 1, 1), bold=True, font_size=f"{int(diameter * 0.32)}sp")
        with avatar.canvas.before:
            Color(*bg_col)
            background = Ellipse(pos=avatar.pos, size=avatar.size)
            Color(1, 1, 1, 0.25)
            outline = Line(ellipse=(*avatar.pos, *avatar.size), width=dp(1.2))
        def update_av(_i, _v):
            background.pos = avatar.pos
            background.size = avatar.size
            outline.ellipse = (*avatar.pos, *avatar.size)
        avatar.bind(pos=update_av, size=update_av)
        return avatar

    def _empty(self, value):
        paleta = self._paleta()
        return Label(text=value, color=paleta["text_muted"], halign="center", valign="middle", text_size=(dp(720), None))

    def _card_moderno(self, height, padding=(dp(18), dp(16)), spacing=dp(10), bg_color=None, border_color=None, radius=dp(18)):
        paleta = self._paleta()
        fill = bg_color or paleta["card_bg"]
        outline_col = border_color or paleta["card_border"]
        card = BoxLayout(orientation="vertical", size_hint_y=None, padding=padding, spacing=spacing)
        if height is None:
            card.bind(minimum_height=card.setter("height"))
        else:
            card.height = dp(height)
        with card.canvas.before:
            Color(0.02, 0.08, 0.18, 0.10 if not self._is_dark() else 0.25)
            shadow = RoundedRectangle(pos=(card.x + dp(3), card.y - dp(4)), size=card.size, radius=[radius])
            Color(*fill)
            background = RoundedRectangle(pos=card.pos, size=card.size, radius=[radius])
            Color(*outline_col)
            outline = Line(rounded_rectangle=(*card.pos, *card.size, radius), width=dp(1))
        def update(_item, _value):
            shadow.pos = (card.x + dp(3), card.y - dp(4))
            shadow.size = card.size
            background.pos = card.pos
            background.size = card.size
            outline.rounded_rectangle = (*card.pos, *card.size, radius)
        card.bind(pos=update, size=update)
        return card

    def _card(self, height, color=None, border=None):
        paleta = self._paleta()
        fill = color if (color is not None and color != (0.065, 0.21, 0.47, 1)) else paleta["card_bg"]
        bdr = border or paleta["card_border"]
        return self._card_moderno(height, bg_color=fill, border_color=bdr)

    def _comment_bubble(self, comment):
        paleta = self._paleta()
        own_message = (comment.autor or "").strip().casefold() == self._autor().strip().casefold()
        
        row = BoxLayout(size_hint_y=None, spacing=dp(10), padding=(0, dp(4)))
        row.bind(minimum_height=row.setter("height"))

        initials = "".join(part[0] for part in (comment.autor or "PM").split()[:2]).upper() or "PM"
        avatar = self._avatar(initials, dp(32), paleta["accent"] if own_message else (0.42, 0.52, 0.65, 1))
        
        bubble = BoxLayout(orientation="vertical", size_hint=(0.88, None), padding=(dp(14), dp(10)), spacing=dp(5))
        bubble.bind(minimum_height=bubble.setter("height"))
        
        fill = paleta["bubble_own"] if own_message else paleta["bubble_other"]
        border_col = paleta["bubble_border"]
        with bubble.canvas.before:
            Color(*fill)
            bg = RoundedRectangle(pos=bubble.pos, size=bubble.size, radius=[dp(14)])
            Color(*border_col)
            line = Line(rounded_rectangle=(*bubble.pos, *bubble.size, dp(14)), width=dp(0.9))
        bubble.bind(pos=lambda _i, v: (setattr(bg, "pos", v), setattr(line, "rounded_rectangle", (*v, *bubble.size, dp(14)))),
                    size=lambda _i, v: (setattr(bg, "size", v), setattr(line, "rounded_rectangle", (*bubble.pos, *v, dp(14)))))
        
        meta = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(8))
        author = Label(text=comment.autor or "Membro da turma", color=paleta["text_primary"],
                       bold=True, font_size="12sp", halign="left", valign="middle")
        author.bind(size=lambda item, size: setattr(item, "text_size", size))
        timestamp = Label(text=self._horario(comment.criado_em), color=paleta["text_muted"],
                          font_size="10sp", halign="right", valign="middle", size_hint_x=None, width=dp(64))
        timestamp.bind(size=lambda item, size: setattr(item, "text_size", size))
        meta.add_widget(author)
        meta.add_widget(timestamp)
        bubble.add_widget(meta)
        bubble.add_widget(self._paragraph(comment.mensagem, color=paleta["text_secondary"], size="12sp", minimum=22))

        if own_message:
            row.add_widget(Label())  # Spacer para empurrar para direita
            row.add_widget(bubble)
            row.add_widget(avatar)
        else:
            row.add_widget(avatar)
            row.add_widget(bubble)
            row.add_widget(Label())  # Spacer
        return row

    def _conversation_panel(self, comments):
        paleta = self._paleta()
        conversation = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(14), spacing=dp(10))
        conversation.bind(minimum_height=conversation.setter("height"))
        with conversation.canvas.before:
            Color(*paleta["surface_alt"])
            bg = RoundedRectangle(pos=conversation.pos, size=conversation.size, radius=[dp(14)])
            Color(*paleta["card_border"])
            line = Line(rounded_rectangle=(*conversation.pos, *conversation.size, dp(14)), width=dp(0.9))
        conversation.bind(pos=lambda _i, v: (setattr(bg, "pos", v), setattr(line, "rounded_rectangle", (*v, *conversation.size, dp(14)))),
                          size=lambda _i, v: (setattr(bg, "size", v), setattr(line, "rounded_rectangle", (*conversation.pos, *v, dp(14)))))
        
        heading = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(8))
        heading.add_widget(IconeUI(nome="forum-outline", size_hint=(None, None), size=(dp(18), dp(18)),
                                   font_size=dp(16), color=paleta["accent"], pos_hint={"center_y": 0.5}))
        heading.add_widget(Label(text="RESPOSTAS DA TURMA", color=paleta["accent"], bold=True,
                                 font_size="11sp", halign="left", valign="middle"))
        count_pill = self._badge_pill(f"{len(comments)} respostas", "", paleta["accent"], paleta["accent_soft"], font_size="10sp", height=dp(20))
        heading.add_widget(count_pill)
        conversation.add_widget(heading)
        for comment in comments[-6:]:
            conversation.add_widget(self._comment_bubble(comment))
        return conversation

    def _team_card(self, height, action):
        paleta = self._paleta()
        card = TeamCard(orientation="vertical", size_hint=(1, None), height=dp(height), padding=dp(18), spacing=dp(10))
        with card.canvas.before:
            Color(0.02, 0.08, 0.18, 0.12 if not self._is_dark() else 0.28)
            c_shadow = RoundedRectangle(pos=(card.x + dp(3), card.y - dp(4)), size=card.size, radius=[dp(18)])
            Color(*paleta["card_bg"])
            c_bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(18)])
            Color(*paleta["card_border"])
            c_line = Line(rounded_rectangle=(*card.pos, *card.size, dp(18)), width=dp(1))
        def update_tc(_item, _val):
            c_shadow.pos = (card.x + dp(3), card.y - dp(4))
            c_shadow.size = card.size
            c_bg.pos = card.pos
            c_bg.size = card.size
            c_line.rounded_rectangle = (*card.pos, *card.size, dp(18))
        card.bind(pos=update_tc, size=update_tc)
        card.bind(on_release=lambda *_args: action())
        return card

    def _center(self, panel, widget):
        """Centraliza cartões para manter a leitura confortável e moderna."""
        row = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=widget.height)
        widget.size_hint_x = None
        widget.width = min(dp(860), Window.width - dp(80))
        Window.bind(width=lambda _window, width: setattr(widget, "width", min(dp(860), width - dp(80))))
        widget.bind(height=lambda _widget, value: setattr(row, "height", value))
        row.add_widget(widget)
        panel.add_widget(row)

    def _update_card_widths(self, *args):
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
        paleta = self._paleta()
        self.equipe_id = ""
        self.titulo = "Turmas"
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
            empty = self._card_moderno(None, padding=dp(28), spacing=dp(12))
            empty.add_widget(self._text("Vamos começar por aqui", 36, True, size="20sp"))
            empty.add_widget(self._paragraph(message, color=paleta["text_secondary"], size="14sp"))
            if self.pode_gerenciar_materia:
                empty.add_widget(self._button("Criar turma", self.editar_materia))
            area.add_widget(empty)
            return

        for materia in materias:
            card = self._team_card(240, partial(self.abrir_equipe, materia.id, self.secao_inicial))
            
            # Header do Card de Turma
            team_header = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(12))
            ic_wrapper = AnchorLayout(size_hint=(None, None), size=(dp(48), dp(48)))
            with ic_wrapper.canvas.before:
                Color(*paleta["accent_soft"])
                iw_bg = RoundedRectangle(pos=ic_wrapper.pos, size=ic_wrapper.size, radius=[dp(12)])
            ic_wrapper.bind(pos=lambda _i, v, b=iw_bg: setattr(b, "pos", v), size=lambda _i, v, b=iw_bg: setattr(b, "size", v))
            ic_wrapper.add_widget(_icone_materia(materia, dp(40)))
            team_header.add_widget(ic_wrapper)

            labels = BoxLayout(orientation="vertical", spacing=dp(2), pos_hint={"center_y": 0.5})
            labels.add_widget(self._text(materia.nome, 24, True, color=paleta["text_primary"], size="17sp", preserve_color=True))
            labels.add_widget(self._badge_pill(materia.categoria, "tag-outline", paleta["accent"], paleta["accent_soft"], font_size="9sp", height=dp(20)))
            team_header.add_widget(labels)
            team_header.add_widget(Label())
            card.add_widget(team_header)

            # Chips de resumo da turma
            meta_stats = BoxLayout(size_hint_y=None, height=dp(22), spacing=dp(8))
            meta_stats.add_widget(self._badge_pill(f"{len(materia.topicos)} módulos", "book-open-outline", paleta["text_muted"], paleta["surface_alt"], font_size="9sp", height=dp(20)))
            meta_stats.add_widget(self._badge_pill(f"{len(materia.publicacoes)} posts", "forum-outline", paleta["text_muted"], paleta["surface_alt"], font_size="9sp", height=dp(20)))
            meta_stats.add_widget(self._badge_pill(f"{len(materia.arquivos)} arquivos", "folder-outline", paleta["text_muted"], paleta["surface_alt"], font_size="9sp", height=dp(20)))
            meta_stats.add_widget(Label())
            card.add_widget(meta_stats)

            # Descrição
            card.add_widget(self._paragraph(materia.descricao or "Acompanhe as aulas, materiais e participe das conversas da turma.",
                                            color=paleta["text_secondary"], size="12sp", minimum=34))

            # Ações
            actions = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
            btn_abrir = self._button("Abrir turma", partial(self.abrir_equipe, materia.id, self.secao_inicial), compact=True, variant="primary")
            btn_abrir.icone = "arrow-right"
            btn_abrir.icon_position = "right"
            actions.add_widget(btn_abrir)
            can_manage_team = app.permission_service.perfil_pode_gerenciar_materias(
                self._perfil(), materia.criado_por_email
            )
            if can_manage_team:
                btn_cfg = self._button("Configurar", partial(self.editar_materia, materia.id), compact=True, variant="light")
                btn_cfg.icone = "cog-outline"
                btn_del = self._button("Excluir", partial(self.confirmar_exclusao_materia, materia.id), danger=True, compact=True)
                btn_del.icone = "delete-outline"
                actions.add_widget(btn_cfg)
                actions.add_widget(btn_del)
            actions.add_widget(Label())
            card.add_widget(actions)
            area.add_widget(card)

        try:
            area.bind(width=self._update_card_widths)
            self._update_card_widths()
        except Exception:
            pass

    # Navegação interna da equipe
    def abrir_equipe(self, materia_id, secao="feed"):
        if secao not in {key for key, _title in self.SECOES}:
            secao = "feed"
        if not self.modo_equipe:
            manager = App.get_running_app().root
            target = manager.get_screen("equipe").children[0]
            target.papel, target.pode_editar = self.papel, self.pode_editar
            manager.transition = SlideTransition(direction="left", duration=.22)
            target.abrir_equipe(materia_id, secao)
            manager.current = "equipe"
            return
        self.equipe_id, self.secao = materia_id, secao
        materia = self._service.obter(materia_id)
        self.titulo = materia.nome
        app = App.get_running_app()
        profile = self._perfil()
        paleta = self._paleta()
        self.pode_editar = app.permission_service.perfil_pode_editar_conteudo(
            profile, materia_id, materia.criado_por_email
        )
        self.pode_gerenciar_materia = app.permission_service.perfil_pode_gerenciar_materias(
            profile, materia.criado_por_email
        )
        self.status_texto = f"{materia.categoria} • {len(materia.publicacoes)} publicações • {len(materia.arquivos)} arquivos"
        area = self._clear()
        area.cols = 1

        # Banner de Cabeçalho da Equipe
        header = BoxLayout(size_hint_y=None, height=dp(88), spacing=dp(16), padding=(dp(18), dp(12)))
        with header.canvas.before:
            Color(*paleta["card_bg"])
            header_background = RoundedRectangle(pos=header.pos, size=header.size, radius=[dp(18)])
            Color(*paleta["card_border"])
            header_line = Line(rounded_rectangle=(*header.pos, *header.size, dp(18)), width=dp(1))
            Color(*paleta["accent"])
            h_accent_bar = RoundedRectangle(pos=(header.x, header.y + dp(12)), size=(dp(5), header.height - dp(24)), radius=[dp(3)])
        def update_hb(_i, _v):
            header_background.pos = header.pos
            header_background.size = header.size
            header_line.rounded_rectangle = (*header.pos, *header.size, dp(18))
            h_accent_bar.pos = (header.x, header.y + dp(12))
            h_accent_bar.size = (dp(5), header.height - dp(24))
        header.bind(pos=update_hb, size=update_hb)

        btn_turmas = self._button("‹ Turmas", self.mostrar_equipes, compact=True, variant="secondary")
        btn_turmas.icone = "arrow-left"
        header.add_widget(btn_turmas)

        ic_team_wrapper = AnchorLayout(size_hint=(None, None), size=(dp(54), dp(54)))
        with ic_team_wrapper.canvas.before:
            Color(*paleta["accent_soft"])
            itw_bg = RoundedRectangle(pos=ic_team_wrapper.pos, size=ic_team_wrapper.size, radius=[dp(14)])
        ic_team_wrapper.bind(pos=lambda _i, v, b=itw_bg: setattr(b, "pos", v), size=lambda _i, v, b=itw_bg: setattr(b, "size", v))
        ic_team_wrapper.add_widget(_icone_materia(materia, dp(44)))
        header.add_widget(ic_team_wrapper)

        title_group = BoxLayout(orientation="vertical", spacing=dp(2), pos_hint={"center_y": 0.5})
        title_group.add_widget(self._text(materia.nome, 28, True, color=paleta["text_primary"], size="20sp", preserve_color=True))
        
        meta_team_row = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(8))
        meta_team_row.add_widget(self._badge_pill(materia.categoria, "tag-outline", paleta["accent"], paleta["accent_soft"], font_size="9sp", height=dp(20)))
        meta_team_row.add_widget(self._badge_pill(f"{len(materia.publicacoes)} posts", "forum-outline", paleta["text_muted"], paleta["surface_alt"], font_size="9sp", height=dp(20)))
        meta_team_row.add_widget(self._badge_pill(f"{len(materia.arquivos)} arquivos", "folder-outline", paleta["text_muted"], paleta["surface_alt"], font_size="9sp", height=dp(20)))
        meta_team_row.add_widget(self._badge_pill(f"{len(materia.topicos)} módulos", "book-open-outline", paleta["text_muted"], paleta["surface_alt"], font_size="9sp", height=dp(20)))
        meta_team_row.add_widget(Label())
        title_group.add_widget(meta_team_row)
        header.add_widget(title_group)

        if self.pode_gerenciar_materia:
            btn_cfg = self._button("Configurar", partial(self.editar_materia, materia.id), compact=True, variant="light")
            btn_cfg.icone = "cog-outline"
            header.add_widget(btn_cfg)
        area.add_widget(header)

        # Tabs de Navegação
        nav = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8), padding=(dp(4), dp(4)))
        tab_icons = {
            "feed": "forum-outline",
            "teorico": "book-open-page-variant-outline",
            "arquivos": "folder-outline",
            "trabalhos": "clipboard-text-outline",
            "testes": "school-outline",
            "info": "information-outline",
        }
        for key, title in self.SECOES:
            selected = key == self.secao
            tab = BotaoAcao(text=title, variant="primary" if selected else "secondary",
                size_hint_x=1, size_hint_y=None, height=dp(42),
                color=(1, 1, 1, 1), font_size="12sp", bold=selected)
            tab.icone = tab_icons.get(key, "")
            tab.bind(on_release=lambda _item, section=key: self.abrir_equipe(materia_id, section))
            nav.add_widget(tab)
        area.add_widget(nav)

        shell = BoxLayout(size_hint_y=None, height=max(dp(450), Window.height - dp(265)), spacing=dp(12))
        panel_scroll = ScrollView(do_scroll_x=False, bar_width=dp(7))
        panel = GridLayout(cols=1, spacing=dp(14), padding=(dp(10), dp(10), dp(20), dp(18)), size_hint_y=None)
        panel.bind(minimum_height=panel.setter("height"))
        panel_scroll.add_widget(panel)
        shell.add_widget(panel_scroll)
        area.add_widget(shell)
        getattr(self, f"_render_{self.secao}")(materia, panel)

    def _toolbar(self, panel, primary=None):
        toolbar = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        if primary and self.pode_editar:
            toolbar.add_widget(self._button(*primary, compact=True))
        elif primary:
            toolbar.add_widget(self._text("Visualização para alunos", 30, color=(.22, .33, .48, 1)))
        panel.add_widget(toolbar)

    # 1. Feed / Área de conversas e discussões
    def _render_feed(self, materia, panel):
        paleta = self._paleta()
        visible_posts = [post for post in materia.publicacoes if self.pode_editar or post.status.casefold() != "rascunho"]

        # Header da Seção de Conversas
        header_box = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(12), padding=(dp(4), 0))
        title_box = BoxLayout(orientation="vertical", spacing=dp(2))
        title_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        title_row.add_widget(IconeUI(nome="forum-outline", size_hint=(None, None), size=(dp(24), dp(24)),
                                     font_size=dp(22), color=paleta["accent"], pos_hint={"center_y": 0.5}))
        title_row.add_widget(self._text("Mural de Conversas & Aulas", 28, True, color=paleta["text_primary"], size="19sp", preserve_color=True))
        title_box.add_widget(title_row)
        title_box.add_widget(self._text("Espaço colaborativo para aulas, avisos, dúvidas e debates da disciplina.", 20,
                                        color=paleta["text_muted"], size="12sp", preserve_color=True))
        header_box.add_widget(title_box)
        header_box.add_widget(Label())
        header_box.add_widget(self._badge_pill(f"{len(visible_posts)} publicações", "message-text-outline",
                                               paleta["accent"], paleta["accent_soft"], font_size="11sp", height=dp(28)))
        panel.add_widget(header_box)

        # Composer Card (Área de Nova Postagem)
        composer = self._card_moderno(None, padding=(dp(20), dp(16)), spacing=dp(12),
                                     bg_color=paleta["card_bg"], border_color=paleta["card_border"])
        top_user_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12))
        initials = "".join(part[0] for part in self._autor().split()[:2]).upper() or "PM"
        top_user_row.add_widget(self._avatar(initials, dp(42), paleta["accent"]))
        user_info = BoxLayout(orientation="vertical", spacing=dp(2), pos_hint={"center_y": 0.5})
        user_info.add_widget(self._text(self._autor(), 20, True, color=paleta["text_primary"], size="14sp", preserve_color=True))
        role_label = "Professor" if self.pode_editar else "Aluno"
        user_info.add_widget(self._text(role_label, 16, color=paleta["text_muted"], size="11sp", preserve_color=True))
        top_user_row.add_widget(user_info)
        top_user_row.add_widget(Label())
        composer.add_widget(top_user_row)

        prompt_box = BoxLayout(size_hint_y=None, height=dp(42), padding=(dp(14), dp(8)), spacing=dp(8))
        with prompt_box.canvas.before:
            Color(*paleta["surface_alt"])
            p_bg = RoundedRectangle(pos=prompt_box.pos, size=prompt_box.size, radius=[dp(12)])
            Color(*paleta["card_border"])
            p_line = Line(rounded_rectangle=(*prompt_box.pos, *prompt_box.size, dp(12)), width=dp(0.9))
        prompt_box.bind(pos=lambda _i, v: (setattr(p_bg, "pos", v), setattr(p_line, "rounded_rectangle", (*v, *prompt_box.size, dp(12)))),
                        size=lambda _i, v: (setattr(p_bg, "size", v), setattr(p_line, "rounded_rectangle", (*prompt_box.pos, *v, dp(12)))))
        prompt_box.add_widget(IconeUI(nome="pencil-outline", size_hint=(None, None), size=(dp(18), dp(18)),
                                      font_size=dp(16), color=paleta["text_muted"], pos_hint={"center_y": 0.5}))
        prompt_text = (
            "Compartilhe uma aula, orientação pedagógica ou aviso com a turma…" if self.pode_editar
            else "Tem alguma dúvida ou pergunta? Inicie uma conversa com a turma…"
        )
        prompt_box.add_widget(Label(text=prompt_text, color=paleta["text_muted"], font_size="12sp",
                                    halign="left", valign="middle", text_size=(dp(600), None)))
        composer.add_widget(prompt_box)

        # Botões de ação do Composer
        actions_bar = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(10))
        if self.pode_editar:
            btn_aula = self._button("Publicar aula", partial(self.editar_publicacao, materia.id, None, "aula"), compact=True, variant="primary")
            btn_aula.icone = "school-outline"
            btn_aviso = self._button("Novo aviso", partial(self.editar_publicacao, materia.id, None, "aviso"), compact=True, variant="secondary")
            btn_aviso.icone = "bullhorn-outline"
            btn_duvida = self._button("Tópico de debate", partial(self.editar_publicacao, materia.id, None, "pergunta"), compact=True, variant="light")
            btn_duvida.icone = "comment-question-outline"
            actions_bar.add_widget(btn_aula)
            actions_bar.add_widget(btn_aviso)
            actions_bar.add_widget(btn_duvida)
        else:
            btn_pergunta = self._button("Fazer uma pergunta", partial(self.editar_publicacao, materia.id, None, "pergunta"), compact=True, variant="primary")
            btn_pergunta.icone = "comment-question-outline"
            actions_bar.add_widget(btn_pergunta)
        actions_bar.add_widget(Label())
        btn_files_link = self._button("Arquivos da turma", partial(self.abrir_equipe, materia.id, "arquivos"), compact=True, variant="light")
        btn_files_link.icone = "folder-outline"
        actions_bar.add_widget(btn_files_link)
        composer.add_widget(actions_bar)
        self._center(panel, composer)

        # Lista de Publicações
        if not visible_posts:
            empty = self._card_moderno(None, padding=dp(28), spacing=dp(12),
                                       bg_color=paleta["card_bg"], border_color=paleta["card_border"])
            empty_icon_box = AnchorLayout(size_hint_y=None, height=dp(60))
            empty_icon_box.add_widget(IconeUI(nome="forum-outline", size_hint=(None, None), size=(dp(56), dp(56)),
                                               font_size=dp(52), color=paleta["text_muted"]))
            empty.add_widget(empty_icon_box)
            empty.add_widget(self._text("O mural de conversas ainda está vazio", 30, True, color=paleta["text_primary"], size="18sp", preserve_color=True))
            empty.add_widget(self._paragraph("As publicações, aulas e discussões da turma aparecerão aqui. Professores podem postar conteúdos e alunos podem iniciar debates ou perguntas.",
                                             color=paleta["text_secondary"], size="13sp"))
            self._center(panel, empty)
            return

        files_by_id = {item.id: item for item in materia.arquivos}
        for post in sorted(visible_posts, key=lambda item: item.criado_em, reverse=True):
            card = self._card_moderno(None, padding=(dp(22), dp(18)), spacing=dp(12),
                                      bg_color=paleta["card_bg"], border_color=paleta["card_border"])
            
            # Autor + Data + Tipo Badge
            author_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(12))
            post_initials = "".join(part[0] for part in (post.autor or "PM").split()[:2]).upper() or "PM"
            author_row.add_widget(self._avatar(post_initials, dp(42), paleta["accent"]))
            
            author_info = BoxLayout(orientation="vertical", spacing=dp(2), pos_hint={"center_y": 0.5})
            author_info.add_widget(self._text(post.autor or "Membro da turma", 20, True, color=paleta["text_primary"], size="14sp", preserve_color=True))
            meta_date_row = BoxLayout(size_hint_y=None, height=dp(18), spacing=dp(4))
            meta_date_row.add_widget(IconeUI(nome="clock-outline", size_hint=(None, None), size=(dp(13), dp(13)),
                                             font_size=dp(12), color=paleta["text_muted"], pos_hint={"center_y": 0.5}))
            date_label = Label(text=self._data(post.criado_em), color=paleta["text_muted"], font_size="11sp",
                               size_hint_x=None, halign="left", valign="middle")
            date_label.bind(texture_size=lambda _i, sz: setattr(date_label, "width", sz[0]))
            meta_date_row.add_widget(date_label)
            author_info.add_widget(meta_date_row)
            author_row.add_widget(author_info)
            author_row.add_widget(Label())

            # Tipo Badge
            rotulo, icone_tipo, cor_txt, cor_fundo = self._obter_badge_tipo_post(post.tipo)
            author_row.add_widget(self._badge_pill(rotulo, icone_tipo, cor_txt, cor_fundo, font_size="10sp", height=dp(26)))
            if post.status.casefold() == "rascunho":
                author_row.add_widget(self._badge_pill("RASCUNHO", "pencil-outline", (0.85, 0.45, 0.05, 1), (0.95, 0.55, 0.10, 0.15), font_size="10sp", height=dp(26)))

            card.add_widget(author_row)

            # Título e Mensagem do Post
            card.add_widget(self._text(post.titulo, 32, True, color=paleta["text_primary"], size="18sp", preserve_color=True))
            card.add_widget(self._paragraph(post.mensagem, color=paleta["text_secondary"], size="13sp"))

            # Anexos
            linked_files = [files_by_id[item] for item in post.arquivos_ids if item in files_by_id]
            if linked_files or post.anexos:
                anexos_container = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
                anexos_container.bind(minimum_height=anexos_container.setter("height"))
                for shared_file in linked_files:
                    f_box = BoxLayout(size_hint_y=None, height=dp(42), padding=(dp(10), dp(4)), spacing=dp(10))
                    with f_box.canvas.before:
                        Color(*paleta["surface_alt"])
                        f_bg = RoundedRectangle(pos=f_box.pos, size=f_box.size, radius=[dp(10)])
                    f_box.bind(pos=lambda _i, v: setattr(f_bg, "pos", v), size=lambda _i, v: setattr(f_bg, "size", v))
                    ic_nome, ic_cor, _ = self._obter_info_arquivo(shared_file.nome)
                    f_box.add_widget(IconeUI(nome=ic_nome, size_hint=(None, None), size=(dp(22), dp(22)),
                                            font_size=dp(20), color=ic_cor, pos_hint={"center_y": 0.5}))
                    f_label = Label(text=f"{shared_file.nome} ({self._tamanho(shared_file.tamanho)})",
                                    color=paleta["text_primary"], bold=True, font_size="12sp",
                                    halign="left", valign="middle")
                    f_label.bind(width=lambda _i, w: setattr(f_label, "text_size", (w, None)))
                    f_box.add_widget(f_label)
                    btn_abrir_anexo = self._button("Abrir", partial(self.abrir_arquivo, shared_file.caminho_local), compact=True, variant="light")
                    btn_abrir_anexo.icone = "open-in-new"
                    f_box.add_widget(btn_abrir_anexo)
                    anexos_container.add_widget(f_box)
                card.add_widget(anexos_container)

            # Conversa / Comentários
            if post.comentarios:
                card.add_widget(self._conversation_panel(post.comentarios))
            else:
                card.add_widget(self._text("Nenhuma resposta ainda. Seja o primeiro a responder!", 24,
                                           color=paleta["text_muted"], size="11sp", preserve_color=True))

            # Rodapé de Ações do Card
            card_actions = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
            btn_reply = self._button("Responder", partial(self.comentar_publicacao, materia.id, post.id), compact=True, variant="light")
            btn_reply.icone = "reply"
            card_actions.add_widget(btn_reply)
            if self.pode_editar:
                btn_edit = self._button("Editar", partial(self.editar_publicacao, materia.id, post.id), compact=True, variant="light")
                btn_edit.icone = "pencil-outline"
                btn_del = self._button("Excluir", partial(self.confirmar_exclusao_publicacao, materia.id, post.id), danger=True, compact=True)
                btn_del.icone = "delete-outline"
                card_actions.add_widget(btn_edit)
                card_actions.add_widget(btn_del)
            card_actions.add_widget(Label())
            card.add_widget(card_actions)
            self._center(panel, card)

    # 2. Onde guarda os arquivos (Biblioteca de arquivos da turma)
    def _render_arquivos(self, materia, panel):
        paleta = self._paleta()
        total_arquivos = len(materia.arquivos)
        total_bytes = sum(getattr(a, "tamanho", 0) for a in materia.arquivos)

        # Header da Seção de Arquivos
        heading = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(12), padding=(dp(4), 0))
        title_box = BoxLayout(orientation="vertical", spacing=dp(2))
        title_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        title_row.add_widget(IconeUI(nome="folder-multiple-outline", size_hint=(None, None), size=(dp(24), dp(24)),
                                     font_size=dp(22), color=paleta["accent"], pos_hint={"center_y": 0.5}))
        title_row.add_widget(self._text("Biblioteca de Arquivos da Turma", 28, True, color=paleta["text_primary"], size="19sp", preserve_color=True))
        title_box.add_widget(title_row)
        title_box.add_widget(self._text(f"{total_arquivos} arquivos disponíveis  •  {self._tamanho(total_bytes)} armazenados localmente", 20,
                                        color=paleta["text_muted"], size="12sp", preserve_color=True))
        heading.add_widget(title_box)
        heading.add_widget(Label())
        if self.pode_editar:
            btn_upload = self._button("Enviar arquivo", partial(self.selecionar_arquivo, materia.id), compact=True, variant="primary")
            btn_upload.icone = "cloud-upload-outline"
            heading.add_widget(btn_upload)
        panel.add_widget(heading)

        # Estado Vazio
        if not materia.arquivos:
            empty = self._card_moderno(None, padding=dp(32), spacing=dp(12),
                                       bg_color=paleta["card_bg"], border_color=paleta["card_border"])
            empty_icon_box = AnchorLayout(size_hint_y=None, height=dp(64))
            empty_icon_box.add_widget(IconeUI(nome="folder-upload-outline", size_hint=(None, None), size=(dp(56), dp(56)),
                                               font_size=dp(52), color=paleta["text_muted"]))
            empty.add_widget(empty_icon_box)
            empty.add_widget(self._text("Nenhum arquivo compartilhado ainda", 32, True, color=paleta["text_primary"], size="18sp", preserve_color=True))
            empty.add_widget(self._paragraph(
                "Esta é a biblioteca central da turma. O professor pode enviar PDFs, apresentações de slides, apostilas, códigos e documentos para consulta dos alunos.",
                color=paleta["text_secondary"], size="13sp",
            ))
            if self.pode_editar:
                btn_first = self._button("Enviar o primeiro arquivo", partial(self.selecionar_arquivo, materia.id), variant="primary")
                btn_first.icone = "cloud-upload-outline"
                empty.add_widget(btn_first)
            self._center(panel, empty)
            return

        # Lista de Arquivos com Cards Modernos
        for arquivo in sorted(materia.arquivos, key=lambda item: item.criado_em, reverse=True):
            card = self._card_moderno(None, padding=(dp(16), dp(12)), spacing=dp(14),
                                      bg_color=paleta["card_bg"], border_color=paleta["card_border"])
            
            row = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(14))
            
            # Badge de ícone do tipo de arquivo
            ic_nome, ic_cor, ic_bg = self._obter_info_arquivo(arquivo.nome)
            badge_box = AnchorLayout(size_hint=(None, None), size=(dp(48), dp(48)))
            with badge_box.canvas.before:
                Color(*ic_bg)
                b_bg = RoundedRectangle(pos=badge_box.pos, size=badge_box.size, radius=[dp(12)])
            badge_box.bind(pos=lambda _i, v: setattr(b_bg, "pos", v), size=lambda _i, v: setattr(b_bg, "size", v))
            badge_box.add_widget(IconeUI(nome=ic_nome, size_hint=(None, None), size=(dp(28), dp(28)),
                                        font_size=dp(26), color=ic_cor))
            row.add_widget(badge_box)

            # Informações do arquivo
            info_box = BoxLayout(orientation="vertical", spacing=dp(3), pos_hint={"center_y": 0.5})
            info_box.add_widget(self._text(arquivo.nome, 22, True, color=paleta["text_primary"], size="15sp", preserve_color=True))
            
            meta_chips = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(8))
            ext_label = Path(arquivo.nome).suffix[1:].upper() or "ARQUIVO"
            meta_chips.add_widget(self._badge_pill(ext_label, "", ic_cor, ic_bg, font_size="9sp", height=dp(18)))
            meta_chips.add_widget(self._badge_pill(self._tamanho(arquivo.tamanho), "harddisk", paleta["text_muted"], paleta["surface_alt"], font_size="9sp", height=dp(18)))
            meta_chips.add_widget(self._badge_pill(f"Enviado por {arquivo.autor}", "account-outline", paleta["text_muted"], paleta["surface_alt"], font_size="9sp", height=dp(18)))
            meta_chips.add_widget(self._badge_pill(self._data(arquivo.criado_em), "calendar-outline", paleta["text_muted"], paleta["surface_alt"], font_size="9sp", height=dp(18)))
            meta_chips.add_widget(Label())
            info_box.add_widget(meta_chips)
            row.add_widget(info_box)

            # Botões de ação
            actions = BoxLayout(size_hint=(None, None), size=(dp(220) if self.pode_editar else dp(110), dp(40)),
                                spacing=dp(8), pos_hint={"center_y": 0.5})
            btn_open = self._button("Abrir", partial(self.abrir_arquivo, arquivo.caminho_local), compact=True, variant="primary")
            btn_open.icone = "open-in-new"
            actions.add_widget(btn_open)
            if self.pode_editar:
                btn_remove = self._button("Excluir", partial(self.confirmar_exclusao_arquivo, materia.id, arquivo.id), danger=True, compact=True)
                btn_remove.icone = "delete-outline"
                actions.add_widget(btn_remove)
            row.add_widget(actions)
            card.add_widget(row)
            self._center(panel, card)

    def _render_trabalhos(self, materia, panel):
        paleta = self._paleta()
        heading = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(12), padding=(dp(4), 0))
        title_box = BoxLayout(orientation="vertical", spacing=dp(2))
        title_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        title_row.add_widget(IconeUI(nome="clipboard-text-outline", size_hint=(None, None), size=(dp(24), dp(24)),
                                     font_size=dp(22), color=paleta["accent"], pos_hint={"center_y": 0.5}))
        title_row.add_widget(self._text("Atividades e Trabalhos da Turma", 28, True, color=paleta["text_primary"], size="19sp", preserve_color=True))
        title_box.add_widget(title_row)
        title_box.add_widget(self._text("Acompanhe os prazos, instruções e envie suas entregas.", 20,
                                        color=paleta["text_muted"], size="12sp", preserve_color=True))
        heading.add_widget(title_box)
        heading.add_widget(Label())
        if self.pode_editar:
            btn_novo_trabalho = self._button("Nova atividade", partial(self.editar_trabalho, materia.id, None), compact=True, variant="primary")
            btn_novo_trabalho.icone = "plus-circle-outline"
            heading.add_widget(btn_novo_trabalho)
        panel.add_widget(heading)

        if not materia.trabalhos:
            empty = self._card_moderno(None, padding=dp(32), spacing=dp(12),
                                       bg_color=paleta["card_bg"], border_color=paleta["card_border"])
            empty_icon_box = AnchorLayout(size_hint_y=None, height=dp(60))
            empty_icon_box.add_widget(IconeUI(nome="clipboard-check-outline", size_hint=(None, None), size=(dp(56), dp(56)),
                                               font_size=dp(52), color=paleta["text_muted"]))
            empty.add_widget(empty_icon_box)
            empty.add_widget(self._text("Nenhuma atividade delegada nesta turma", 32, True, color=paleta["text_primary"], size="18sp", preserve_color=True))
            empty.add_widget(self._paragraph("As atividades, prazos e tarefas propostas pelo professor aparecerão aqui.", color=paleta["text_secondary"], size="13sp"))
            if self.pode_editar:
                btn_start_t = self._button("Criar a primeira atividade", partial(self.editar_trabalho, materia.id, None), variant="primary")
                btn_start_t.icone = "plus-circle-outline"
                empty.add_widget(btn_start_t)
            self._center(panel, empty)
            return

        for trabalho in materia.trabalhos:
            card = self._card_moderno(None, padding=(dp(20), dp(16)), spacing=dp(10),
                                      bg_color=paleta["card_bg"], border_color=paleta["card_border"])
            entregue = self._email() in trabalho.entregue_por
            
            top_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
            top_row.add_widget(self._badge_pill(trabalho.categoria.upper() or "ATIVIDADE", "clipboard-text-outline",
                                                (0.08, 0.45, 0.78, 1), (0.12, 0.45, 0.85, 0.14), font_size="10sp", height=dp(24)))
            status_cor = (0.12, 0.65, 0.35, 1) if trabalho.status.casefold() in {"ativo", "aberto"} else (0.85, 0.45, 0.05, 1)
            top_row.add_widget(self._badge_pill(trabalho.status.upper(), "", status_cor, (status_cor[0], status_cor[1], status_cor[2], 0.14), font_size="10sp", height=dp(24)))
            top_row.add_widget(Label())
            card.add_widget(top_row)

            card.add_widget(self._text(trabalho.titulo, 28, True, color=paleta["text_primary"], size="18sp", preserve_color=True))
            card.add_widget(self._paragraph(trabalho.descricao or "Sem descrição detalhada.", color=paleta["text_secondary"], size="13sp"))
            
            meta_row = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(10))
            meta_row.add_widget(self._badge_pill(f"Prazo: {trabalho.prazo}", "calendar-clock", paleta["text_muted"], paleta["surface_alt"], font_size="10sp", height=dp(22)))
            meta_row.add_widget(self._badge_pill(f"{len(trabalho.entregue_por)} entrega(s)", "account-check-outline", paleta["text_muted"], paleta["surface_alt"], font_size="10sp", height=dp(22)))
            meta_row.add_widget(Label())
            card.add_widget(meta_row)

            if trabalho.anexos:
                card.add_widget(self._text("Anexos: " + ", ".join(trabalho.anexos), 20, color=paleta["accent"], size="12sp", preserve_color=True))

            actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
            if not self.pode_editar and not entregue:
                btn_entregar = self._button("Marcar como entregue", partial(self.entregar_trabalho, materia.id, trabalho.id), compact=True, variant="primary")
                btn_entregar.icone = "check-circle-outline"
                actions.add_widget(btn_entregar)
            elif entregue:
                conf = self._badge_pill("Entregue por você", "check-circle", (0.10, 0.68, 0.35, 1), (0.12, 0.68, 0.35, 0.15), font_size="11sp", height=dp(34))
                actions.add_widget(conf)
            if self.pode_editar:
                btn_edit = self._button("Editar", partial(self.editar_trabalho, materia.id, trabalho.id), compact=True, variant="light")
                btn_edit.icone = "pencil-outline"
                btn_del = self._button("Excluir", partial(self.confirmar_exclusao_trabalho, materia.id, trabalho.id), danger=True, compact=True)
                btn_del.icone = "delete-outline"
                actions.add_widget(btn_edit)
                actions.add_widget(btn_del)
            actions.add_widget(Label())
            card.add_widget(actions)
            self._center(panel, card)

    # 3. Conteúdo no formato de documentação e Aulas Teóricas
    def _conteudo_visivel(self, topico, content, categoria):
        if content.categoria != categoria:
            return False
        if self.pode_editar:
            return True
        return topico.status.casefold() in {"ativo", "publicado"} and content.status.casefold() in {"ativo", "publicado"}

    def _render_teorico(self, materia, panel): self._render_documentacao(materia, panel, "teorico", "Documentação didática")
    def _render_testes(self, materia, panel): self._render_documentacao(materia, panel, "testes", "Provas e avaliações")
    def _render_documentacao(self, materia, panel, categoria, heading):
        paleta = self._paleta()
        is_teorico = categoria == "teorico"
        titulo_secao = "Aulas e Conteúdos Teóricos" if is_teorico else heading
        subtitulo_secao = "Trilha de aprendizagem organizada por módulos temáticos" if is_teorico else "Materiais de provas e avaliações da turma"

        # Header da Seção
        header_box = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(12), padding=(dp(4), 0))
        title_box = BoxLayout(orientation="vertical", spacing=dp(2))
        title_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        title_row.add_widget(IconeUI(nome="book-open-page-variant-outline" if is_teorico else "school-outline",
                                     size_hint=(None, None), size=(dp(24), dp(24)),
                                     font_size=dp(22), color=paleta["accent"], pos_hint={"center_y": 0.5}))
        title_row.add_widget(self._text(titulo_secao, 28, True, color=paleta["text_primary"], size="19sp", preserve_color=True))
        title_box.add_widget(title_row)
        title_box.add_widget(self._text(subtitulo_secao, 20, color=paleta["text_muted"], size="12sp", preserve_color=True))
        header_box.add_widget(title_box)
        header_box.add_widget(Label())
        if self.pode_editar:
            btn_novo_mod = self._button("Novo módulo", partial(self.editar_topico, materia.id, None), compact=True, variant="primary")
            btn_novo_mod.icone = "folder-plus-outline"
            header_box.add_widget(btn_novo_mod)
        panel.add_widget(header_box)

        chapters = [(topico, content) for topico in materia.topicos for content in topico.conteudos if self._conteudo_visivel(topico, content, categoria)]
        if not chapters:
            empty = self._card_moderno(None, padding=dp(32), spacing=dp(12),
                                       bg_color=paleta["card_bg"], border_color=paleta["card_border"])
            empty_icon_box = AnchorLayout(size_hint_y=None, height=dp(60))
            empty_icon_box.add_widget(IconeUI(nome="book-open-blank-variant" if is_teorico else "file-certificate-outline",
                                               size_hint=(None, None), size=(dp(56), dp(56)),
                                               font_size=dp(52), color=paleta["text_muted"]))
            empty.add_widget(empty_icon_box)
            empty.add_widget(self._text("Ainda não há aulas nesta área" if is_teorico else "Ainda não há materiais de avaliação", 32, True, color=paleta["text_primary"], size="18sp", preserve_color=True))
            empty.add_widget(self._paragraph(
                "O professor pode organizar a matéria em módulos temáticos e cadastrar aulas teóricas com textos explicativos e resumos didáticos." if is_teorico else
                "Os materiais de avaliação e provas publicados pelo professor aparecerão aqui.",
                color=paleta["text_secondary"], size="13sp",
            ))
            if self.pode_editar and not materia.topicos:
                btn_start = self._button("Criar o primeiro módulo", partial(self.editar_topico, materia.id, None), variant="primary")
                btn_start.icone = "folder-plus-outline"
                empty.add_widget(btn_start)
            self._center(panel, empty)

            if self.pode_editar and materia.topicos:
                for topico in materia.topicos:
                    mod_card = self._card_moderno(None, padding=(dp(18), dp(14)), spacing=dp(8),
                                                  bg_color=paleta["card_bg"], border_color=paleta["card_border"])
                    mod_row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(8))
                    mod_row.add_widget(IconeUI(nome="folder-outline", size_hint=(None, None), size=(dp(22), dp(22)),
                                               font_size=dp(20), color=paleta["accent"], pos_hint={"center_y": 0.5}))
                    mod_row.add_widget(self._text(topico.titulo, 28, True, color=paleta["text_primary"], size="16sp", preserve_color=True))
                    mod_card.add_widget(mod_row)
                    if topico.descricao:
                        mod_card.add_widget(self._paragraph(topico.descricao, color=paleta["text_muted"], size="12sp"))
                    btn_add = self._button("Adicionar aula a este módulo", partial(self.editar_conteudo, materia.id, topico.id, None), compact=True, variant="light")
                    btn_add.icone = "plus-circle-outline"
                    mod_card.add_widget(btn_add)
                    self._center(panel, mod_card)
            return

        chosen_topico, chosen = next((item for item in chapters if item[1].id == self.documento_conteudo_id), chapters[0])
        self.documento_topico_id = chosen_topico.id
        self.documento_conteudo_id = chosen.id

        # Layout de Leitura Dividido (Sidebar com Módulos + Leitor da Aula)
        doc_height = max(dp(500), Window.height - dp(320))
        doc_container = BoxLayout(size_hint_y=None, height=doc_height, spacing=dp(16))

        # --- Sidebar Esquerda: Lista de Módulos e Aulas ---
        sidebar = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(340), spacing=dp(10), padding=dp(14))
        with sidebar.canvas.before:
            Color(*paleta["card_bg"])
            s_bg = RoundedRectangle(pos=sidebar.pos, size=sidebar.size, radius=[dp(16)])
            Color(*paleta["card_border"])
            s_line = Line(rounded_rectangle=(*sidebar.pos, *sidebar.size, dp(16)), width=dp(1))
        sidebar.bind(pos=lambda _i, v: (setattr(s_bg, "pos", v), setattr(s_line, "rounded_rectangle", (*v, *sidebar.size, dp(16)))),
                     size=lambda _i, v: (setattr(s_bg, "size", v), setattr(s_line, "rounded_rectangle", (*sidebar.pos, *v, dp(16)))))
        
        side_heading = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
        side_heading.add_widget(IconeUI(nome="format-list-bulleted-type", size_hint=(None, None), size=(dp(18), dp(18)),
                                        font_size=dp(16), color=paleta["accent"], pos_hint={"center_y": 0.5}))
        side_heading.add_widget(Label(text="MÓDULOS DE ENSINO", color=paleta["accent"], bold=True,
                                      font_size="11sp", halign="left", valign="middle"))
        side_heading.add_widget(self._badge_pill(f"{len(chapters)} aulas", "", paleta["accent"], paleta["accent_soft"], font_size="9sp", height=dp(20)))
        sidebar.add_widget(side_heading)

        side_scroll = ScrollView(do_scroll_x=False, bar_width=dp(5), scroll_type=['bars', 'content'])
        side_list = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, size_hint_x=1, padding=(0, dp(4), dp(6), dp(8)))
        side_list.bind(minimum_height=side_list.setter("height"))

        topics = [topico for topico in materia.topicos if self.pode_editar or topico.status.casefold() in {"ativo", "publicado"}]
        for topico in topics:
            topic_box = BoxLayout(orientation="vertical", size_hint_y=None, size_hint_x=1, spacing=dp(5))
            topic_box.bind(minimum_height=topic_box.setter("height"))
            topic_box.bind(width=lambda inst, _w: inst.do_layout())
            
            t_header = BoxLayout(orientation="horizontal", size_hint_y=None, size_hint_x=1, spacing=dp(8), padding=(0, dp(6)))
            t_header.add_widget(IconeUI(nome="folder-open-outline", size_hint=(None, None), size=(dp(16), dp(16)),
                                        font_size=dp(15), color=paleta["accent"], pos_hint={"center_y": 0.5}))
            t_title = Label(text=topico.titulo, color=paleta["text_primary"], bold=True, font_size="12sp",
                            halign="left", valign="top", size_hint_x=1, size_hint_y=None)
            def on_title_size(inst, val, h=t_header):
                if val[0] > 0 and inst.text_size[0] != val[0]:
                    inst.text_size = (val[0], None)
                    inst.texture_update()
            t_title.bind(size=on_title_size)
            t_title.bind(texture_size=lambda inst, sz, h=t_header: (
                setattr(inst, "height", max(dp(16), sz[1])),
                setattr(h, "height", max(dp(26), sz[1] + dp(8)))
            ))
            t_header.add_widget(t_title)
            t_header.bind(width=lambda inst, _w: inst.do_layout())
            t_header.bind(height=lambda _i, _h, p=topic_box: p.do_layout())
            topic_box.add_widget(t_header)

            topic_contents = [content for content in topico.conteudos if self._conteudo_visivel(topico, content, categoria)]
            for content in topic_contents:
                active = content.id == chosen.id
                lesson_btn = LessonCard(orientation="horizontal", size_hint_y=None, size_hint_x=1,
                                        padding=(dp(10), dp(8)), spacing=dp(8))
                btn_fill = paleta["accent"] if active else paleta["surface_alt"]
                with lesson_btn.canvas.before:
                    Color(*btn_fill)
                    l_bg = RoundedRectangle(pos=lesson_btn.pos, size=lesson_btn.size, radius=[dp(10)])
                    Color(1, 1, 1, 0.4 if active else 0)
                    l_line = Line(rounded_rectangle=(*lesson_btn.pos, *lesson_btn.size, dp(10)), width=dp(1))
                def update_lc(_i, _v, b=l_bg, ln=l_line, card=lesson_btn):
                    b.pos = card.pos
                    b.size = card.size
                    ln.rounded_rectangle = (*card.pos, *card.size, dp(10))
                lesson_btn.bind(pos=update_lc, size=update_lc)
                lesson_btn.bind(width=lambda inst, _w: inst.do_layout())
                lesson_btn.bind(height=lambda _i, _h, p=topic_box: p.do_layout())
                
                ic_aula = "play-circle" if active else "file-document-outline"
                ic_cor_aula = (1, 1, 1, 1) if active else paleta["text_muted"]
                lesson_btn.add_widget(IconeUI(nome=ic_aula, size_hint=(None, None), size=(dp(18), dp(18)),
                                              font_size=dp(16), color=ic_cor_aula, pos_hint={"center_y": 0.5}))
                lbl_aula = Label(text=content.titulo, color=(1, 1, 1, 1) if active else paleta["text_secondary"],
                                 bold=active, font_size="12sp", halign="left", valign="middle",
                                 size_hint_x=1, size_hint_y=None)
                def on_lbl_size(inst, val, card=lesson_btn):
                    if val[0] > 0 and inst.text_size[0] != val[0]:
                        inst.text_size = (val[0], None)
                        inst.texture_update()
                lbl_aula.bind(size=on_lbl_size)
                lbl_aula.bind(texture_size=lambda inst, sz, card=lesson_btn: (
                    setattr(inst, "height", max(dp(18), sz[1])),
                    setattr(card, "height", max(dp(44), sz[1] + dp(16)))
                ))
                lesson_btn.add_widget(lbl_aula)
                lesson_btn.bind(on_release=partial(lambda cid, *_: self.ver_documento(materia.id, cid), content.id))
                topic_box.add_widget(lesson_btn)

            if self.pode_editar:
                btn_add_aula = self._button("+ Adicionar aula", partial(self.editar_conteudo, materia.id, topico.id, None), compact=True, variant="light")
                btn_add_aula.height = dp(32)
                btn_add_aula.font_size = "11sp"
                topic_box.add_widget(btn_add_aula)
            side_list.add_widget(topic_box)
        side_scroll.add_widget(side_list)
        sidebar.add_widget(side_scroll)

        # --- Painel Direito: Leitor da Aula Teórica ---
        reader_card = BoxLayout(orientation="vertical", spacing=dp(14), padding=(dp(24), dp(20)), size_hint_y=None)
        reader_card.bind(minimum_height=reader_card.setter("height"))
        with reader_card.canvas.before:
            Color(*paleta["card_bg"])
            r_bg = RoundedRectangle(pos=reader_card.pos, size=reader_card.size, radius=[dp(16)])
            Color(*paleta["card_border"])
            r_line = Line(rounded_rectangle=(*reader_card.pos, *reader_card.size, dp(16)), width=dp(1))
        reader_card.bind(pos=lambda _i, v: (setattr(r_bg, "pos", v), setattr(r_line, "rounded_rectangle", (*v, *reader_card.size, dp(16)))),
                         size=lambda _i, v: (setattr(r_bg, "size", v), setattr(r_line, "rounded_rectangle", (*reader_card.pos, *v, dp(16)))))

        # Breadcrumb & Status Bar
        crumb_row = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        crumb_row.add_widget(IconeUI(nome="school-outline", size_hint=(None, None), size=(dp(16), dp(16)),
                                     font_size=dp(15), color=paleta["accent"], pos_hint={"center_y": 0.5}))
        crumb_text = f"{chosen_topico.titulo.upper()}  ›  {chosen.titulo}"
        crumb_lbl = Label(text=crumb_text, color=paleta["accent"], bold=True, font_size="11sp", halign="left", valign="middle",
                          shorten=True, shorten_from="right")
        crumb_lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        crumb_row.add_widget(crumb_lbl)
        crumb_row.add_widget(Label())

        status_cor = (0.12, 0.65, 0.35, 1) if chosen.status.casefold() in {"ativo", "publicado"} else (0.85, 0.45, 0.05, 1)
        crumb_row.add_widget(self._badge_pill(chosen.status.upper(), "check-circle" if chosen.status.casefold() in {"ativo", "publicado"} else "pencil",
                                              status_cor, (status_cor[0], status_cor[1], status_cor[2], 0.15), font_size="9sp", height=dp(22)))
        crumb_row.add_widget(self._badge_pill(self._data(chosen.atualizado_em), "clock-outline", paleta["text_muted"], paleta["surface_alt"], font_size="9sp", height=dp(22)))
        reader_card.add_widget(crumb_row)

        # Título da Aula
        reader_card.add_widget(self._text(chosen.titulo, 38, True, color=paleta["text_primary"], size="22sp", preserve_color=True))

        # Caixa de Resumo / Objetivo Didático (Callout Box)
        if chosen.descricao:
            callout = BoxLayout(orientation="vertical", size_hint_y=None, padding=(dp(16), dp(12)), spacing=dp(4))
            callout.bind(minimum_height=callout.setter("height"))
            with callout.canvas.before:
                Color(*paleta["callout_bg"])
                c_bg = RoundedRectangle(pos=callout.pos, size=callout.size, radius=[dp(12)])
                Color(*paleta["callout_border"])
                c_bar = RoundedRectangle(pos=(callout.x, callout.y), size=(dp(4), callout.height), radius=[dp(2)])
            callout.bind(pos=lambda _i, v: (setattr(c_bg, "pos", v), setattr(c_bar, "pos", (v[0], v[1]))),
                         size=lambda _i, v: (setattr(c_bg, "size", v), setattr(c_bar, "size", (dp(4), v[1]))))
            callout_head = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(6))
            callout_head.add_widget(IconeUI(nome="lightbulb-on-outline", size_hint=(None, None), size=(dp(16), dp(16)),
                                            font_size=dp(15), color=paleta["accent"], pos_hint={"center_y": 0.5}))
            callout_head.add_widget(Label(text="OBJETIVO / RESUMO DA AULA", color=paleta["accent"], bold=True, font_size="10sp", halign="left", valign="middle"))
            callout.add_widget(callout_head)
            callout.add_widget(self._paragraph(chosen.descricao, color=paleta["text_secondary"], size="13sp"))
            reader_card.add_widget(callout)

        # Corpo do Texto da Aula (Renderizador Markdown com suporte a #, ##, **, *, listas, códigos)
        texto_corpo = chosen.corpo or "Esta aula ainda não possui explicação cadastrada. O professor pode editar o material para redigir o conteúdo."
        for w in parse_markdown_to_widgets(texto_corpo, paleta):
            reader_card.add_widget(w)

        # Barra Inferior: Stepper (Aula Anterior, Contador, Próxima Aula, Editar)
        current_index = next((index for index, item in enumerate(chapters) if item[1].id == chosen.id), 0)
        total_chapters = len(chapters)
        
        stepper_bar = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10), padding=(0, dp(6)))
        btn_prev = self._button("‹ Aula anterior", partial(self.mover_documento, materia.id, categoria, -1), compact=True, variant="secondary")
        btn_prev.disabled = current_index == 0
        stepper_bar.add_widget(btn_prev)

        counter_pill = self._badge_pill(f"Aula {current_index + 1} de {total_chapters}", "book-open-outline",
                                        paleta["accent"], paleta["accent_soft"], font_size="11sp", height=dp(34))
        stepper_bar.add_widget(counter_pill)

        btn_next = self._button("Próxima aula ›", partial(self.mover_documento, materia.id, categoria, 1), compact=True, variant="primary")
        btn_next.disabled = current_index == total_chapters - 1
        stepper_bar.add_widget(btn_next)

        stepper_bar.add_widget(Label())  # Spacer

        if self.pode_editar:
            btn_edit_aula = self._button("Editar esta aula", partial(self.editar_conteudo, materia.id, chosen_topico.id, chosen.id), compact=True, variant="light")
            btn_edit_aula.icone = "pencil-outline"
            stepper_bar.add_widget(btn_edit_aula)
        
        reader_card.add_widget(stepper_bar)

        reader_scroll = ScrollView(do_scroll_x=False, bar_width=dp(6))
        reader_wrapper = GridLayout(cols=1, size_hint_y=None, spacing=dp(8))
        reader_wrapper.bind(minimum_height=reader_wrapper.setter("height"))
        reader_wrapper.add_widget(reader_card)
        reader_scroll.add_widget(reader_wrapper)

        doc_container.add_widget(sidebar)
        doc_container.add_widget(reader_scroll)
        panel.add_widget(doc_container)

    def mover_documento(self, materia_id, categoria, deslocamento):
        materia = self._service.obter(materia_id)
        chapters = [(topic, content) for topic in materia.topicos for content in topic.conteudos if self._conteudo_visivel(topic, content, categoria)]
        index = next((i for i, item in enumerate(chapters) if item[1].id == self.documento_conteudo_id), 0)
        target = max(0, min(len(chapters) - 1, index + deslocamento))
        self.documento_conteudo_id = chapters[target][1].id
        self.abrir_equipe(materia_id, self.secao)

    def ver_documento(self, materia_id, conteudo_id):
        self.documento_conteudo_id = conteudo_id
        self.abrir_equipe(materia_id, self.secao)

    def _render_info(self, materia, panel):
        paleta = self._paleta()
        heading = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(12), padding=(dp(4), 0))
        title_box = BoxLayout(orientation="vertical", spacing=dp(2))
        title_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        title_row.add_widget(IconeUI(nome="information-outline", size_hint=(None, None), size=(dp(24), dp(24)),
                                     font_size=dp(22), color=paleta["accent"], pos_hint={"center_y": 0.5}))
        title_row.add_widget(self._text("Informações da Turma", 28, True, color=paleta["text_primary"], size="19sp", preserve_color=True))
        title_box.add_widget(title_row)
        title_box.add_widget(self._text("Visão geral, estatísticas e configurações desta disciplina.", 20,
                                        color=paleta["text_muted"], size="12sp", preserve_color=True))
        heading.add_widget(title_box)
        heading.add_widget(Label())
        if self.pode_gerenciar_materia:
            btn_edit_info = self._button("Editar informações", partial(self.editar_materia, materia.id), compact=True, variant="primary")
            btn_edit_info.icone = "pencil-outline"
            heading.add_widget(btn_edit_info)
        panel.add_widget(heading)

        card = self._card_moderno(None, padding=dp(22), spacing=dp(14),
                                  bg_color=paleta["card_bg"], border_color=paleta["card_border"])
        card.add_widget(self._text("Sobre esta turma", 32, True, color=paleta["text_primary"], size="20sp", preserve_color=True))
        card.add_widget(self._paragraph(materia.descricao or "Sem descrição cadastrada.", color=paleta["text_secondary"], size="14sp"))

        # Grade de estatísticas da turma
        stats_grid = GridLayout(cols=4 if Window.width >= dp(800) else 2, spacing=dp(10), size_hint_y=None, height=dp(70))
        for stat_title, stat_val, stat_icon in (
            ("Módulos", str(len(materia.topicos)), "book-open-page-variant-outline"),
            ("Publicações", str(len(materia.publicacoes)), "forum-outline"),
            ("Arquivos", str(len(materia.arquivos)), "folder-outline"),
            ("Atividades", str(len(materia.trabalhos)), "clipboard-text-outline"),
        ):
            s_box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(2))
            with s_box.canvas.before:
                Color(*paleta["surface_alt"])
                sb_bg = RoundedRectangle(pos=s_box.pos, size=s_box.size, radius=[dp(10)])
            s_box.bind(pos=lambda _i, v, b=sb_bg: setattr(b, "pos", v), size=lambda _i, v, b=sb_bg: setattr(b, "size", v))
            h_stat = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(6))
            h_stat.add_widget(IconeUI(nome=stat_icon, size_hint=(None, None), size=(dp(16), dp(16)),
                                      font_size=dp(14), color=paleta["accent"], pos_hint={"center_y": 0.5}))
            h_stat.add_widget(Label(text=stat_title, color=paleta["text_muted"], font_size="10sp", halign="left", valign="middle"))
            s_box.add_widget(h_stat)
            s_box.add_widget(Label(text=stat_val, color=paleta["text_primary"], bold=True, font_size="18sp", halign="left", valign="middle"))
            stats_grid.add_widget(s_box)
        card.add_widget(stats_grid)

        # Meta chips
        meta_chips = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        meta_chips.add_widget(self._badge_pill(f"Categoria: {materia.categoria}", "tag-outline", paleta["accent"], paleta["accent_soft"], font_size="10sp", height=dp(24)))
        meta_chips.add_widget(self._badge_pill(f"Status: {materia.status}", "check-circle-outline", (0.12, 0.65, 0.35, 1), (0.12, 0.65, 0.35, 0.15), font_size="10sp", height=dp(24)))
        meta_chips.add_widget(self._badge_pill(f"Criada em: {self._data(materia.criado_em)}", "calendar-outline", paleta["text_muted"], paleta["surface_alt"], font_size="10sp", height=dp(24)))
        meta_chips.add_widget(Label())
        card.add_widget(meta_chips)

        card.add_widget(self._paragraph(
            "As turmas e os arquivos são armazenados localmente neste computador. A sincronização automática entre computadores ainda não está configurada.",
            color=paleta["text_muted"], size="12sp", minimum=36,
        ))
        self._center(panel, card)

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
        novo = not materia_id
        if not novo and not self.exigir_edicao(materia_id):
            return

        def save():
            materia.nome = fields[0].text
            materia.categoria = fields[1].text
            materia.descricao = fields[2].text
            materia.status = status_spinner.text
            if novo:
                materia.criado_por_email = self._email()
            action = partial(self._service.salvar_materia, materia)
            self._salvar(action, popup, self.mostrar_equipes)

        fields = self._fields([("Nome da turma", materia.nome), ("Categoria", materia.categoria), ("Descrição", materia.descricao)])
        status_spinner = Spinner(text=materia.status or "Ativa", values=("Ativa", "Arquivada", "Rascunho"), size_hint_y=None, height=dp(42))
        fields.append(status_spinner)
        popup = self._popup("Criar turma" if novo else "Editar turma", fields, save)

    def editar_publicacao(self, materia_id, post_id, tipo_inicial=None):
        if not self._exigir_internet("publicar no mural"):
            return
        materia = self._service.obter(materia_id)
        post = next((item for item in materia.publicacoes if item.id == post_id), Publicacao(autor=self._autor()))
        if post_id and not self.exigir_edicao(materia_id):
            return
        novo = not post_id
        is_student = not self.pode_editar
        if is_student and novo and not tipo_inicial:
            tipo_inicial = "pergunta"

        tipo_inicial_valor = (tipo_inicial or post.tipo or ("pergunta" if is_student else "aula")).casefold()
        tipo_para_rotulo = {
            "aula": "Aula",
            "aviso": "Aviso",
            "pergunta": "Dúvida",
            "recado": "Recado",
            "conteudo": "Material",
            "tarefa": "Atividade",
        }
        rotulo_inicial = tipo_para_rotulo.get(tipo_inicial_valor, tipo_inicial_valor.capitalize())

        tipos_disponiveis = ("Dúvida", "Recado") if is_student else ("Aula", "Aviso", "Dúvida", "Recado", "Material", "Atividade")
        if rotulo_inicial not in tipos_disponiveis:
            rotulo_inicial = tipos_disponiveis[0]

        titulo_inicial = (
            "" if novo and tipo_inicial_valor in {"pergunta", "aviso", "recado"}
            else (post.titulo or ("Dúvida sobre a matéria" if is_student else ""))
        )

        def save():
            post.titulo = fields[0].text
            post.mensagem = fields[1].text
            post.anexos = [item.strip() for item in fields[2].text.split(",") if item.strip()]
            post.arquivos_ids = [file_id for file_id, checkbox in file_checkboxes.items() if checkbox.active]
            rotulo_para_tipo = {
                "aula": "aula",
                "aviso": "aviso",
                "dúvida": "pergunta",
                "recado": "recado",
                "material": "conteudo",
                "atividade": "tarefa",
            }
            post.tipo = rotulo_para_tipo.get(tipo_spinner.text.casefold(), tipo_spinner.text.casefold())
            post.status = "rascunho" if not is_student and rascunho_checkbox.active else "publicado"
            action = partial(self._service.salvar_publicacao, materia_id, post)
            self._salvar(action, popup, partial(self.abrir_equipe, materia_id, "feed"))

        fields = self._fields([("Título", titulo_inicial), ("Mensagem", post.mensagem), ("Links ou anexos externos", ", ".join(post.anexos))])
        tipo_spinner = Spinner(text=rotulo_inicial, values=tipos_disponiveis, size_hint_y=None, height=dp(42))
        tipo_spinner.form_label = "Tipo de publicação"
        tipo_spinner.form_helper_text = "Dúvidas ficam visíveis para toda a turma responder." if is_student else "Escolha se este post é uma aula, aviso ou material."
        fields.append(tipo_spinner)

        file_checkboxes = {}
        if materia.arquivos:
            attachment_group = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
            attachment_group.bind(minimum_height=attachment_group.setter("height"))
            caption = Label(text="Anexar arquivos da biblioteca da turma:", size_hint_y=None, height=dp(22),
                            color=(.12, .23, .38, 1), bold=True, font_size="12sp", halign="left", valign="middle")
            caption.bind(width=lambda item, width: setattr(item, "text_size", (max(1, width), None)))
            attachment_group.add_widget(caption)
            for shared_file in materia.arquivos:
                row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
                check = CheckBox(active=shared_file.id in post.arquivos_ids, size_hint=(None, None), size=(dp(24), dp(24)))
                file_checkboxes[shared_file.id] = check
                label = Label(text=f"{shared_file.nome} ({self._tamanho(shared_file.tamanho)})",
                              color=(.22, .32, .45, 1), font_size="12sp", halign="left", valign="middle")
                label.bind(width=lambda item, width: setattr(item, "text_size", (max(1, width), None)))
                row.add_widget(check)
                row.add_widget(label)
                attachment_group.add_widget(row)
            fields.append(attachment_group)

        if not is_student:
            draft_box = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
            rascunho_checkbox = CheckBox(active=post.status.casefold() == "rascunho", size_hint=(None, None), size=(dp(24), dp(24)))
            draft_label = Label(text="Salvar apenas como rascunho (não visível para alunos)", color=(.22, .32, .45, 1),
                                font_size="12sp", halign="left", valign="middle")
            draft_label.bind(width=lambda item, width: setattr(item, "text_size", (max(1, width), None)))
            draft_box.add_widget(rascunho_checkbox)
            draft_box.add_widget(draft_label)
            fields.append(draft_box)
        else:
            class DummyDraft: active = False
            rascunho_checkbox = DummyDraft()

        titulo_popup = "Fazer uma pergunta" if is_student and novo else ("Nova publicação" if novo else "Editar publicação")
        popup = self._popup(titulo_popup, fields, save)

    def comentar_publicacao(self, materia_id, post_id):
        if not self._exigir_internet("responder à conversa"):
            return
        fields = self._fields([("Mensagem", "")])
        field = fields[0]
        def save():
            self._salvar(
                lambda: self._service.comentar_publicacao(materia_id, post_id, Comentario(autor=self._autor(), mensagem=field.text)),
                popup, partial(self.abrir_equipe, materia_id, "feed")
            )
        popup = self._popup("Responder à conversa", fields, save)

    def editar_trabalho(self, materia_id, trabalho_id):
        if not self.exigir_edicao(materia_id): return
        materia = self._service.obter(materia_id); trabalho = next((item for item in materia.trabalhos if item.id == trabalho_id), Trabalho())
        novo = not trabalho_id
        def save():
            trabalho.titulo = fields[0].text; trabalho.categoria = fields[1].text; trabalho.prazo = fields[2].text; trabalho.descricao = fields[3].text
            trabalho.anexos = [item.strip() for item in fields[4].text.split(",") if item.strip()]
            action = partial(self._service.salvar_trabalho, materia_id, trabalho)
            self._salvar(action, popup, partial(self.abrir_equipe, materia_id, "trabalhos"))
        fields = self._fields([("Título", trabalho.titulo), ("Categoria", trabalho.categoria), ("Prazo", trabalho.prazo), ("Descrição", trabalho.descricao), ("Anexos", ", ".join(trabalho.anexos))])
        popup = self._popup("Novo trabalho" if novo else "Editar trabalho", fields, save)

    def editar_topico(self, materia_id, topico_id):
        if not self.exigir_edicao(materia_id): return
        materia = self._service.obter(materia_id); topico = next((item for item in materia.topicos if item.id == topico_id), Topico())
        novo = not topico_id
        def save():
            topico.titulo = fields[0].text; topico.descricao = fields[1].text
            action = partial(self._service.salvar_topico, materia_id, topico)
            def completed():
                self.documento_topico_id = topico.id
                self.abrir_equipe(materia_id, "teorico")
            self._salvar(action, popup, completed)
        fields = self._fields([("Título do módulo", topico.titulo), ("Descrição", topico.descricao)])
        popup = self._popup("Novo módulo" if novo else "Editar módulo", fields, save)

    def editar_conteudo(self, materia_id, topico_id, conteudo_id):
        if not self.exigir_edicao(materia_id): return
        materia = self._service.obter(materia_id); topico = next(item for item in materia.topicos if item.id == topico_id)
        conteudo = next((item for item in topico.conteudos if item.id == conteudo_id), Conteudo())
        novo = not conteudo_id
        def save():
            conteudo.titulo = fields[0].text; conteudo.descricao = fields[1].text; conteudo.corpo = fields[2].text; conteudo.categoria = categoria_spinner.text.casefold()
            action = partial(self._service.salvar_conteudo, materia_id, topico_id, conteudo)
            self._salvar(action, popup, partial(self.abrir_equipe, materia_id, "teorico"))
        fields = self._fields([("Título", conteudo.titulo), ("Descrição", conteudo.descricao), ("Texto da aula", conteudo.corpo)])
        categoria_spinner = Spinner(text=conteudo.categoria or "teorico", values=("teorico", "testes"), size_hint_y=None, height=dp(42))
        fields.append(categoria_spinner)
        popup = self._popup("Nova aula" if novo else "Editar aula", fields, save)

    def selecionar_arquivo(self, materia_id):
        if not self.exigir_edicao(materia_id): return
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        chooser = FileChooserListView(path=str(Path.home()), filters=["*.*"], size_hint_y=.86)
        actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        actions.add_widget(self._button("Cancelar", lambda: popup.dismiss(), compact=True))
        actions.add_widget(self._button("Enviar arquivo selecionado", lambda: self._enviar(materia_id, chooser, popup), compact=True))
        box.add_widget(chooser); box.add_widget(actions)
        popup = Popup(title="Selecionar arquivo para upload", content=box, size_hint=(.86, .84))
        popup.open()

    def _enviar(self, materia_id, chooser, popup):
        if not chooser.selection: self._mensagem("Atenção", "Selecione um arquivo da lista."); return
        self._salvar(lambda: self._service.adicionar_arquivo_local(materia_id, chooser.selection[0], self._autor()), popup, partial(self.abrir_equipe, materia_id, "arquivos"))

    def abrir_arquivo(self, caminho):
        resolved = Path(caminho).resolve() if caminho else None
        if not resolved or not resolved.exists():
            self._mensagem("Arquivo não encontrado", "O arquivo selecionado não existe mais no armazenamento local.")
            return
        os.startfile(str(resolved))

    def entregar_trabalho(self, materia_id, trabalho_id):
        if not self._exigir_internet("entregar trabalho"): return
        self._service.entregar_trabalho(materia_id, trabalho_id, self._email()); self.abrir_equipe(materia_id, "trabalhos")

    def _confirm(self, text, action):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        box.add_widget(self._text(text, 40, True))
        actions = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        actions.add_widget(self._button("Cancelar", lambda: popup.dismiss(), compact=True))
        actions.add_widget(self._button("Confirmar", lambda: (action(), popup.dismiss()), danger=True, compact=True))
        box.add_widget(actions)
        popup = Popup(title="Confirmação", content=box, size_hint=(.46, .26))
        popup.open()

    def confirmar_exclusao_materia(self, ident):
        if not self.exigir_edicao(ident):
            return
        self._confirm(
            "Tem certeza de que deseja excluir esta turma e todos os seus dados?",
            lambda: self._excluir_materia(ident),
        )

    def _excluir_materia(self, ident):
        try:
            self._service.excluir_materia(ident)
            self.mostrar_equipes()
        except ValueError as error:
            self._mensagem("Não foi possível excluir", str(error))

    def confirmar_exclusao_publicacao(self, mid, ident):
        if not self.exigir_edicao(mid): return
        self._confirm("Excluir esta publicação?", lambda: (self._service.excluir_publicacao(mid, ident), self.abrir_equipe(mid, "feed")))

    def confirmar_exclusao_arquivo(self, mid, ident):
        if not self.exigir_edicao(mid): return
        self._confirm("Remover este arquivo?", lambda: (self._service.excluir_arquivo(mid, ident), self.abrir_equipe(mid, "arquivos")))

    def confirmar_exclusao_trabalho(self, mid, ident):
        if not self.exigir_edicao(mid): return
        self._confirm("Excluir este trabalho?", lambda: (self._service.excluir_trabalho(mid, ident), self.abrir_equipe(mid, "trabalhos")))

    def _fields(self, values):
        result = []
        for title, value in values:
            multi = title in {"Descrição", "Mensagem", "Texto da aula", "Texto do capítulo"}
            height = 52 if not multi else 252 if "aula" in title.lower() or "capítulo" in title.lower() else 144 if title == "Mensagem" else 120
            hints = {
                "Descrição": "Dê um pouco de contexto…",
                "Mensagem": "Escreva sua mensagem para a turma…",
                "Texto da aula": "Desenvolva o conteúdo e a explicação da aula…",
                "Texto do capítulo": "Desenvolva o conteúdo da aula…",
            }
            helpers = {
                "Descrição": "Uma descrição breve ajuda todos a entender o propósito.",
                "Mensagem": "Você pode usar mais de um parágrafo.",
                "Texto da aula": "Organize a explicação em parágrafos claros e objetivos.",
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
            "criar turma": "Criar turma",
            "criar equipe": "Criar turma",
            "novo trabalho": "Criar atividade",
            "novo módulo": "Criar módulo",
            "novo capítulo": "Criar módulo",
            "nova aula": "Salvar aula",
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
        popup.open()
        return popup

    def _salvar(self, action, popup, success):
        try:
            action()
            popup.dismiss()
            success()
        except (ValueError, KeyError, OSError, ConnectionError) as error:
            self._mensagem("Verifique os dados", str(error))

    def _mensagem(self, title, text):
        Popup(title=title, content=Label(text=text, color=(.1, .1, .1, 1), halign="left", valign="top", text_size=(dp(520), None)), size_hint=(.6, .42)).open()

    @staticmethod
    def _data(value): return value[:10] if value else "sem data"
    @staticmethod
    def _horario(value):
        if not value or len(value) < 16:
            return "agora"
        return value[11:16]
    @staticmethod
    def _tamanho(value):
        if not value:
            return "0 KB"
        return f"{value / 1024:.1f} KB" if value < 1024 * 1024 else f"{value / (1024 * 1024):.1f} MB"


class TelaEquipe(TelaMaterias):
    """Variação para quando a equipe já é a tela raiz."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.modo_equipe = True

    def on_kv_post(self, _base_widget):
        # A tela de equipe só desenha quando abrir_equipe é acionado diretamente.
        pass

    def mostrar_equipes(self):
        # Em vez de desmontar a tela inteira, apenas volta para a tela de matérias.
        manager = App.get_running_app().root
        manager.transition = SlideTransition(direction="right", duration=.25)
        manager.current = "materias"

    def voltar(self):
        self.mostrar_equipes()
