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

    EMAIL_MODERADOR_TESTE = "jpgamesv40@gmail.com"
    EMAILS_MODERADORES = {"jpgamesv40@gmail.com", "duolinfo.cefet@gmail.com"}

    def papel_do_email(self, email: str | None) -> Papel:
        if (email or "").strip().lower() in self.EMAILS_MODERADORES or (email or "").strip().lower() == self.EMAIL_MODERADOR_TESTE:
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

    def perfil_pode_editar_conteudo(
        self, profile: Mapping[str, Any] | None, materia_id: str,
        criado_por_email: str | None = None,
    ) -> bool:
        """Professores editam suas equipes e matérias associadas; moderadores editam todas."""
        profile = profile or {}
        role = self.papel_do_perfil(profile)
        if role == Papel.MODERADOR:
            return True
        if role != Papel.PROFESSOR:
            return False
        email = str(profile.get("email") or "").strip().casefold()
        if criado_por_email and email == criado_por_email.strip().casefold():
            return True
        assigned = profile.get("materias_responsaveis") or profile.get("subject_ids") or []
        return materia_id in {str(item) for item in assigned}

    def perfil_pode_gerenciar_materias(
        self, profile: Mapping[str, Any] | None, criado_por_email: str | None = None
    ) -> bool:
        """Professores administram equipes próprias; moderadores podem administrar todas."""
        profile = profile or {}
        role = self.papel_do_perfil(profile)
        if role == Papel.MODERADOR:
            return True
        if role != Papel.PROFESSOR:
            return False
        if criado_por_email is None:
            return True  # Autoriza criar uma nova equipe.
        email = str(profile.get("email") or "").strip().casefold()
        owner_email = criado_por_email.strip().casefold()
        return bool(email and owner_email) and email == owner_email

    def perfil_pode_gerenciar_usuarios(self, profile: Mapping[str, Any] | None) -> bool:
        return self.papel_do_perfil(profile) == Papel.MODERADOR

    def perfil_pode_aprovar_extensoes(self, profile: Mapping[str, Any] | None) -> bool:
        return self.papel_do_perfil(profile) in {Papel.PROFESSOR, Papel.MODERADOR}
