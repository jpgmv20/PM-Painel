"""Ponto local de decisão de papéis, pronto para ser substituído pelo servidor."""
from __future__ import annotations

from enum import Enum
from typing import Any, Mapping


class Papel(str, Enum):
    ALUNO = "aluno"
    PROFESSOR = "professor"
    MODERADOR = "moderador"


class PermissionService:
    """Resolve permissões locais; no futuro o backend deve fornecer o papel."""

    EMAIL_MODERADOR_TESTE = "duolinfo.cefet@gmail.com"

    def papel_do_email(self, email: str | None) -> Papel:
        if (email or "").strip().lower() == self.EMAIL_MODERADOR_TESTE:
            return Papel.MODERADOR
        return Papel.ALUNO

    def papel_do_perfil(self, profile: Mapping[str, Any] | None) -> Papel:
        """Aceita desde já o campo que o futuro servidor devolverá no perfil."""
        profile = profile or {}
        remoto = str(profile.get("papel") or profile.get("role") or "").lower().strip()
        if remoto in {papel.value for papel in Papel}:
            return Papel(remoto)
        return self.papel_do_email(str(profile.get("email") or ""))

    def pode_editar_materias(self, email: str | None) -> bool:
        return self.papel_do_email(email) in {Papel.PROFESSOR, Papel.MODERADOR}

    def perfil_pode_editar_materias(self, profile: Mapping[str, Any] | None) -> bool:
        return self.papel_do_perfil(profile) in {Papel.PROFESSOR, Papel.MODERADOR}
