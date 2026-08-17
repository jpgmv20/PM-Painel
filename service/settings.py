"""Preferências persistentes e centralizadas do PM-Painel."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, StringProperty


class SettingsStore(EventDispatcher):
    """Mantém as preferências em um único JSON fora do diretório do projeto."""

    start_with_windows = BooleanProperty(False)
    start_after_login = BooleanProperty(False)
    minimize_to_tray = BooleanProperty(False)
    confirm_before_close = BooleanProperty(True)

    show_google = BooleanProperty(True)
    show_youtube = BooleanProperty(True)
    show_outlook = BooleanProperty(True)
    show_git = BooleanProperty(True)
    show_classroom = BooleanProperty(True)
    show_teams = BooleanProperty(True)
    show_word = BooleanProperty(True)
    show_excel = BooleanProperty(True)
    show_onedrive = BooleanProperty(True)
    show_google_drive = BooleanProperty(True)
    show_discord = BooleanProperty(False)
    show_github = BooleanProperty(True)

    fullscreen = BooleanProperty(True)
    start_in_lab_mode = BooleanProperty(False)
    block_app_close = BooleanProperty(False)
    block_restricted_features = BooleanProperty(False)
    show_computer_info = BooleanProperty(False)

    auto_check_updates = BooleanProperty(True)
    auto_download_updates = BooleanProperty(False)
    install_updates_on_restart = BooleanProperty(False)
    update_channel = StringProperty("Estável")

    laboratory_mode = BooleanProperty(False)
    clear_sessions_on_exit = BooleanProperty(True)
    clear_temporary_browser = BooleanProperty(True)
    clear_abandoned_sessions = BooleanProperty(True)
    prevent_login_persistence = BooleanProperty(True)
    maximum_session_time = StringProperty("4 horas")

    _FIELDS = (
        "start_with_windows", "start_after_login", "minimize_to_tray",
        "confirm_before_close", "show_google", "show_youtube", "show_outlook",
        "show_git", "show_classroom", "show_teams", "show_word", "show_excel",
        "show_onedrive", "show_google_drive", "show_discord", "show_github",
        "fullscreen", "start_in_lab_mode", "block_app_close",
        "block_restricted_features", "show_computer_info", "auto_check_updates",
        "auto_download_updates", "install_updates_on_restart", "update_channel",
        "laboratory_mode", "clear_sessions_on_exit", "clear_temporary_browser",
        "clear_abandoned_sessions", "prevent_login_persistence", "maximum_session_time",
    )

    def __init__(self, path: str | Path | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        self.path = Path(path) if path else base_dir / "PM-Painel" / "settings.json"
        self._loading = True
        self._load()
        self._loading = False
        for field in self._FIELDS:
            self.bind(**{field: self._persist})

    def _load(self) -> None:
        try:
            values = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(values, dict):
            return
        for field in self._FIELDS:
            value = values.get(field)
            if isinstance(value, type(getattr(self, field))):
                setattr(self, field, value)

    def _persist(self, *_args: Any) -> None:
        if self._loading:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps({field: getattr(self, field) for field in self._FIELDS}, indent=2),
                encoding="utf-8",
            )
            temporary.replace(self.path)
        except OSError:
            # Preferências não devem impedir a utilização do painel se o perfil estiver bloqueado.
            return

    def set_value(self, field: str, value: Any) -> None:
        if field not in self._FIELDS:
            raise KeyError(f"Configuração desconhecida: {field}")
        setattr(self, field, value)
