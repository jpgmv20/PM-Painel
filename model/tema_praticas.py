"""Paleta compartilhada e atualizável para os laboratórios práticos."""
from __future__ import annotations

from kivy.app import App


def paleta_praticas() -> dict[str, tuple[float, float, float, float]]:
    app = App.get_running_app()
    surface = getattr(app, "theme_surface", (.95, .97, 1, 1)) if app else (.95, .97, 1, 1)
    escuro = bool(surface and surface[0] < .5)
    if escuro:
        return {
            "shell": (.075, .10, .15, 1),
            "card": (.11, .15, .22, 1),
            "card_elevated": (.14, .19, .28, 1),
            "panel": (.13, .17, .25, 1),
            "text": (.92, .95, .99, 1),
            "text_secondary": (.72, .80, .92, 1),
            "muted": (.58, .67, .79, 1),
            "accent": (.48, .72, 1, 1),
            "primary": (.30, .60, .98, 1),
            "border": (.20, .28, .40, 1),
            "grid": (.16, .22, .31, 1),
            "danger": (1, .49, .44, 1),
            "danger_bg": (.28, .12, .12, 1),
            "success": (.35, .84, .64, 1),
            "success_bg": (.11, .24, .19, 1),
            "warning": (1, .75, .22, 1),
            "warning_bg": (.28, .20, .07, 1),
            "info": (.38, .76, 1, 1),
            "info_bg": (.10, .22, .36, 1),
            "tag_bg": (.16, .23, .35, 1),
            "tag_border": (.24, .34, .50, 1),
            "terminal": (.025, .055, .105, 1),
        }
    return {
        "shell": (.95, .97, 1, 1),
        "card": (1, 1, 1, 1),
        "card_elevated": (.97, .98, 1, 1),
        "panel": (.92, .95, .99, 1),
        "text": (.08, .16, .28, 1),
        "text_secondary": (.22, .32, .46, 1),
        "muted": (.38, .47, .60, 1),
        "accent": (.08, .31, .66, 1),
        "primary": (.08, .36, .74, 1),
        "border": (.82, .88, .94, 1),
        "grid": (.78, .84, .92, 1),
        "danger": (.78, .22, .18, 1),
        "danger_bg": (.99, .91, .91, 1),
        "success": (.08, .55, .38, 1),
        "success_bg": (.88, .97, .92, 1),
        "warning": (.82, .52, .06, 1),
        "warning_bg": (.99, .95, .86, 1),
        "info": (.08, .46, .82, 1),
        "info_bg": (.88, .94, 1, 1),
        "tag_bg": (.91, .94, .98, 1),
        "tag_border": (.80, .86, .94, 1),
        "terminal": (.025, .055, .105, 1),
    }


def tema_escuro() -> bool:
    app = App.get_running_app()
    surface = getattr(app, "theme_surface", (.95, .97, 1, 1)) if app else (.95, .97, 1, 1)
    return bool(surface and surface[0] < .5)


def cor_texto(color) -> str:
    """Infere um papel acessível para as cores usadas historicamente nas telas."""
    r, g, b = color[:3]
    if r > g * 1.45 and r > b * 1.45:
        return "danger"
    if g > r * 1.3 and g > b * 1.05:
        return "success"
    if b > r * 1.15 and b > g * 1.05:
        return "accent"
    luminance = .2126 * r + .7152 * g + .0722 * b
    if luminance < .24:
        return "text"
    if luminance > .76:
        return "text"
    return "muted"


def registrar_cor_texto(widget, color, role: str | None = None):
    role = role or cor_texto(color)
    widget._tema_cor_texto = role
    widget._tema_cor_original = tuple(color)
    widget.color = paleta_praticas()[role] if tema_escuro() else color
    return widget


def registrar_fundo(widget, instruction, role="card"):
    widget._tema_fundo = instruction
    widget._tema_role_fundo = role
    widget._tema_fundo_original = tuple(instruction.rgba)
    instruction.rgba = paleta_praticas()[role] if tema_escuro() else widget._tema_fundo_original
    return widget


def aplicar_tema_arvore(root):
    """Atualiza textos e fundos personalizados de um laboratório já montado."""
    colors = paleta_praticas()
    for widget in root.walk(restrict=True):
        role = getattr(widget, "_tema_cor_texto", None)
        if role in colors:
            widget.color = colors[role] if tema_escuro() else widget._tema_cor_original
        fill = getattr(widget, "_tema_fundo", None)
        background_role = getattr(widget, "_tema_role_fundo", None)
        if fill is not None and background_role in colors:
            fill.rgba = colors[background_role] if tema_escuro() else widget._tema_fundo_original
        if getattr(widget, "_tema_aparencia", False):
            widget.appearance = "dark" if tema_escuro() else "light"
