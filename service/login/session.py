"""Gerenciamento da sessão em memória e do token local de uso offline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import secrets
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class AuthSession:
    """Dados da autenticação válidos apenas enquanto o processo estiver vivo."""

    profile: dict[str, Any]
    credentials: Any


class SessionManager:
    """Guarda credenciais apenas em memória e um passe offline com validade de sete dias."""

    OFFLINE_VALIDITY = timedelta(days=7)

    def __init__(self, path: str | Path | None = None) -> None:
        self._session: Optional[AuthSession] = None
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        self.path = Path(path) if path else base / "PM-Painel" / "offline_session.json"
        self._restored_offline = False
        self._offline_expires_at: str | None = None

    @property
    def is_authenticated(self) -> bool:
        """Indica se há um usuário autenticado na memória do processo."""
        return self._session is not None

    @property
    def session(self) -> Optional[AuthSession]:
        """Retorna a sessão atual, caso exista."""
        return self._session

    @property
    def user(self) -> Optional[dict[str, Any]]:
        """Retorna uma cópia do perfil para impedir mutações acidentais."""
        if self._session is None:
            return None
        return self._session.profile.copy()

    @property
    def credentials(self) -> Any | None:
        """Retorna as credenciais OAuth mantidas somente em memória."""
        return None if self._session is None else self._session.credentials

    @property
    def restored_offline(self) -> bool:
        return self._restored_offline

    @property
    def offline_expires_at(self) -> str | None:
        return self._offline_expires_at

    def set_session(self, profile: Mapping[str, Any], credentials: Any) -> None:
        """Registra um login concluído e cria o token local de sete dias."""
        if not profile.get("email"):
            raise ValueError("Não é permitido criar uma sessão sem e-mail do usuário.")
        clean_profile = dict(profile)
        self._session = AuthSession(profile=clean_profile, credentials=credentials)
        self._restored_offline = False
        self._offline_expires_at = (
            datetime.now(timezone.utc) + self.OFFLINE_VALIDITY
        ).isoformat()
        self._save_offline_lease(clean_profile, self._offline_expires_at)

    def restore_offline_session(self) -> bool:
        """Recupera o último perfil se o token local ainda estiver válido."""
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            profile = payload.get("profile")
            expires_at = datetime.fromisoformat(payload.get("expires_at", ""))
            token = payload.get("token")
            if not isinstance(profile, dict) or not profile.get("email") or not token:
                return False
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                self.clear()
                return False
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return False
        self._session = AuthSession(profile=profile, credentials=None)
        self._restored_offline = True
        self._offline_expires_at = expires_at.isoformat()
        return True

    def update_profile(self, profile: Mapping[str, Any]) -> None:
        """Atualiza o perfil em memória e no passe offline sem renovar sua validade."""
        if self._session is None:
            raise RuntimeError("Não há usuário autenticado.")
        clean_profile = dict(profile)
        self._session = AuthSession(clean_profile, self._session.credentials)
        if self._offline_expires_at:
            self._save_offline_lease(clean_profile, self._offline_expires_at)

    def has_valid_offline_session_for(self, email: str) -> bool:
        """Confirma que existe um passe ainda válido para o e-mail informado."""
        if self._session is not None and self._session.profile.get("email", "").casefold() == email.casefold():
            return self._offline_expires_at is not None
        return False

    def clear(self, *, preserve_offline_token: bool = False) -> None:
        """Descarta a sessão; o token local só permanece ao fechar o aplicativo."""
        self._session = None
        self._restored_offline = False
        if not preserve_offline_token:
            self._offline_expires_at = None
            try:
                self.path.unlink(missing_ok=True)
            except OSError:
                pass

    def _save_offline_lease(self, profile: Mapping[str, Any], expires_at: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {"token": secrets.token_urlsafe(32), "profile": dict(profile), "expires_at": expires_at},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.path)
