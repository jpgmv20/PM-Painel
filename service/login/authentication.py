"""Caso de uso que coordena o login sem acoplar a interface Kivy."""
from __future__ import annotations

import model.componentes as componentes

from typing import Any

from service.login.google_auth import GoogleAuth
from service.login.session import SessionManager
from service.web.browser import BrowserManager

from pathlib import Path
import tempfile
import requests
from kivy.clock import Clock


class AuthenticationService:
    """Coordena OAuth e a sessão em memória para a camada de apresentação."""

    def __init__(
        self,
        google_auth: GoogleAuth,
        session_manager: SessionManager,
        browser_manager: BrowserManager,
    ) -> None:
        self._google_auth = google_auth
        self._session_manager = session_manager
        self._browser_manager = browser_manager

    def login_with_google(self) -> dict[str, Any]:
        """Autentica, busca o perfil e cria a sessão do processo atual."""
        print("[AUTH] Iniciando login com Google...")
        credentials = self._google_auth.start_login(self._browser_manager)
        print("[AUTH] Credenciais obtidas; consultando perfil...")
        profile = self._google_auth.get_user_profile(credentials)
        try:
            email = profile.get('email') if isinstance(profile, dict) else None
        except Exception:
            email = None
        print(f"[AUTH] Perfil obtido: {email}")
        self._session_manager.set_session(profile=profile, credentials=credentials)
        print("[AUTH] Sessão gravada em memória.")
        return profile

    def logout(self) -> None:
        """Revoga a credencial quando possível e remove a sessão local."""
        self._session_manager.clear()
        self._google_auth.logout()
