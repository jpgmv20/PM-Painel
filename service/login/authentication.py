"""Caso de uso que coordena o login sem acoplar a interface Kivy."""
from __future__ import annotations

import model.componentes as componentes

from typing import Any

from service.login.google_auth import GoogleAuth
from service.login.session import SessionManager
from service.login.users import LocalUserStore
from service.web.browser import BrowserManager
from service.network import InternetService

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
        user_store: LocalUserStore | None = None,
        internet_service: InternetService | None = None,
    ) -> None:
        self._google_auth = google_auth
        self._session_manager = session_manager
        self._browser_manager = browser_manager
        self._user_store = user_store or LocalUserStore()
        self._internet_service = internet_service or InternetService()

    def login_with_google(self) -> dict[str, Any]:
        """Autentica, busca o perfil e cria a sessão do processo atual."""
        print("[AUTH] Iniciando login com Google...")
        credentials = self._google_auth.start_login(self._browser_manager)
        print("[AUTH] Credenciais obtidas; consultando perfil...")
        profile = self._google_auth.get_user_profile(credentials)
        account = self._user_store.profile_for_email(str(profile.get("email") or ""))
        if account:
            account.update({key: value for key, value in profile.items() if not account.get(key)})
            profile = account
        try:
            email = profile.get('email') if isinstance(profile, dict) else None
        except Exception:
            email = None
        print(f"[AUTH] Perfil obtido: {email}")
        self._session_manager.set_session(profile=profile, credentials=credentials)
        print("[AUTH] Sessão gravada em memória.")
        return profile

    def login_with_password(
        self, email: str, password: str, *, offline_mode: bool = False
    ) -> dict[str, Any]:
        """Valida uma conta local; uma primeira autenticação precisa de conexão."""
        self._internet_service.require_online(offline_mode=offline_mode, action="O login com senha")
        profile = self._user_store.authenticate(email, password)
        self._session_manager.set_session(profile, credentials=None)
        return profile

    def register_student(
        self,
        name: str,
        email: str,
        password: str,
        confirm_password: str | None = None,
        *,
        offline_mode: bool = False,
    ) -> dict[str, Any]:
        """Cria uma conta gratuita de aluno e inicia a sessão após o cadastro."""
        self._internet_service.require_online(offline_mode=offline_mode, action="O cadastro de aluno")
        if confirm_password is not None and password != confirm_password:
            raise ValueError("As senhas não coincidem.")
        profile = self._user_store.create_student(name, email, password)
        self._session_manager.set_session(profile, credentials=None)
        return profile

    def list_users(self) -> list[dict[str, Any]]:
        return self._user_store.list_users()

    def create_staff_user(
        self,
        name: str,
        email: str,
        password: str,
        role: str,
        subject_ids: list[str],
        actor_profile: dict[str, Any] | None = None,
        *,
        offline_mode: bool = False,
    ) -> dict[str, Any]:
        """Cria um professor ou moderador; a interface valida quem pode chamar."""
        from service.permissoes import PermissionService

        if not PermissionService().perfil_pode_gerenciar_usuarios(actor_profile):
            raise PermissionError("Somente um moderador pode criar contas de professor ou moderador.")
        self._internet_service.require_online(offline_mode=offline_mode, action="O gerenciamento de usuários")
        return self._user_store.create_staff(name, email, password, role, subject_ids)

    def set_user_active(
        self, user_id: str, active: bool, actor_profile: dict[str, Any] | None = None,
        *, offline_mode: bool = False,
    ) -> None:
        from service.permissoes import PermissionService

        if not PermissionService().perfil_pode_gerenciar_usuarios(actor_profile):
            raise PermissionError("Somente um moderador pode gerenciar contas.")
        self._internet_service.require_online(offline_mode=offline_mode, action="O gerenciamento de usuários")
        self._user_store.set_active(user_id, active)

    def set_user_subjects(
        self,
        user_id: str,
        subject_ids: list[str],
        actor_profile: dict[str, Any] | None = None,
        *,
        offline_mode: bool = False,
    ) -> dict[str, Any]:
        from service.permissoes import PermissionService

        if not PermissionService().perfil_pode_gerenciar_usuarios(actor_profile):
            raise PermissionError("Somente um moderador pode alterar as matérias de um professor.")
        self._internet_service.require_online(offline_mode=offline_mode, action="O gerenciamento de usuários")
        return self._user_store.set_subjects(user_id, subject_ids)

    def update_profile(self, profile: dict[str, Any], name: str) -> dict[str, Any]:
        active = self._session_manager.user
        if not active or active.get("email", "").casefold() != profile.get("email", "").casefold():
            raise PermissionError("Só é possível editar o perfil autenticado.")
        updated = self._user_store.update_profile(profile, name)
        self._session_manager.update_profile(updated)
        return updated

    def logout(self) -> None:
        """Revoga a credencial quando possível e remove a sessão local."""
        self._session_manager.clear()
        self._google_auth.logout()
        self._browser_manager.reset_profile()
