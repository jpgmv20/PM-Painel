"""Gerenciamento da sessão autenticada exclusivamente em memória."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class AuthSession:
    """Dados da autenticação válidos apenas enquanto o processo estiver vivo."""

    profile: dict[str, Any]
    credentials: Any


class SessionManager:
    """Armazena o usuário e as credenciais sem qualquer acesso ao disco."""

    def __init__(self) -> None:
        self._session: Optional[AuthSession] = None

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

    def set_session(self, profile: Mapping[str, Any], credentials: Any) -> None:
        """Registra uma sessão nova depois que o OAuth foi concluído."""
        if not profile.get("email"):
            raise ValueError("Não é permitido criar uma sessão sem e-mail do usuário.")
        self._session = AuthSession(profile=dict(profile), credentials=credentials)

    def clear(self) -> None:
        """Descarta o perfil e as credenciais da memória."""
        self._session = None
