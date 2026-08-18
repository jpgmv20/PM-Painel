"""Autenticação Google, mantida somente enquanto o PM-Painel está aberto."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional, Sequence, TYPE_CHECKING

import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from service.web.oauth_callback import OAuthCallbackServer

if TYPE_CHECKING:
    from service.web.browser import BrowserManager


SCOPES: tuple[str, ...] = (
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
)


class GoogleAuth:
    """Executa OAuth no navegador interno e mantém tokens apenas na memória."""

    def __init__(self, client_secrets_file: str | Path = Path(__file__).resolve().parents[2] / "docs" / "client_google_desktop.json", scopes: Optional[Sequence[str]] = None) -> None:
        self._client_secrets_file = Path(client_secrets_file)
        self._scopes = tuple(scopes or SCOPES)
        self._credentials: Optional[Credentials] = None
        self._user_profile: Optional[dict[str, Any]] = None
        self._profile_photo_path: Optional[Path] = None

    def start_login(self, browser: "BrowserManager") -> Credentials:
        """Abre a autorização no WebView do programa e troca o código por token."""
        if not self._client_secrets_file.exists():
            raise FileNotFoundError(f"Cliente OAuth não encontrado: {self._client_secrets_file}")
        flow = InstalledAppFlow.from_client_secrets_file(str(self._client_secrets_file), scopes=list(self._scopes))
        with OAuthCallbackServer() as callback_server:
            flow.redirect_uri = callback_server.redirect_uri
            authorization_url, _state = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="select_account")
            browser.open_url(authorization_url, title="Entrar no PM-Painel")
            authorization_response = callback_server.wait_for_response()

            # O Google redireciona aplicativos instalados para localhost por HTTP.
            # A exceção fica ativa apenas durante essa troca feita no próprio computador.
            previous_transport_setting = os.environ.get("OAUTHLIB_INSECURE_TRANSPORT")
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
            try:
                flow.fetch_token(authorization_response=authorization_response)
            finally:
                if previous_transport_setting is None:
                    os.environ.pop("OAUTHLIB_INSECURE_TRANSPORT", None)
                else:
                    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = previous_transport_setting
        self._credentials = flow.credentials
        return self._credentials

    def get_user_profile(self, credentials: Optional[Credentials] = None) -> dict[str, Any]:
        """Consulta os dados públicos necessários para identificar o usuário."""
        active_credentials = credentials or self._credentials
        if active_credentials is None or not active_credentials.token:
            raise RuntimeError("Não existe uma sessão Google válida.")
        response = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {active_credentials.token}"}, timeout=15)
        response.raise_for_status()
        profile = response.json()
        if not profile.get("email"):
            raise ValueError("O Google não retornou um e-mail válido.")
        self._user_profile = profile
        return profile

    def logout(self) -> None:
        """Revoga o token quando possível e descarta referências sensíveis."""
        credentials = self._credentials
        if credentials is not None:
            try:
                token = credentials.refresh_token or credentials.token
                if token:
                    requests.post("https://oauth2.googleapis.com/revoke", params={"token": token}, timeout=10)
            except Exception:
                pass
        self._remove_cached_profile_photo()
        self._credentials = None
        self._user_profile = None

    def remember_profile_photo(self, path: str | Path) -> None:
        """Guarda o arquivo baixado do Google para removê-lo no logout."""
        self._profile_photo_path = Path(path)

    def _remove_cached_profile_photo(self) -> None:
        path = self._profile_photo_path
        if path is None:
            path = Path(tempfile.gettempdir()) / "pm_painel" / "perfil_google.jpg"
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass
        finally:
            self._profile_photo_path = None
