"""Contas locais do PM-Painel, com senhas armazenadas como hashes."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


class LocalUserStore:
    """Armazena contas neste computador; nenhum segredo é escrito em texto puro."""

    ITERATIONS = 240_000
    ROLES = {"aluno", "professor", "moderador"}

    def __init__(self, path: str | Path | None = None) -> None:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        self.path = Path(path) if path else base / "PM-Painel" / "users.json"
        self._users: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            records = payload.get("users", []) if isinstance(payload, dict) else []
            self._users = [item for item in records if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError, TypeError):
            self._users = []

    def list_users(self) -> list[dict[str, Any]]:
        return [self._public(item) for item in self._users]

    def profile_for_email(self, email: str) -> dict[str, Any] | None:
        normalized = email.strip().casefold()
        record = next(
            (item for item in self._users if item.get("email", "").casefold() == normalized),
            None,
        )
        if record is None:
            return None
        if not record.get("active", True):
            raise PermissionError("Esta conta foi suspensa por um moderador.")
        return self._public(record)

    def create_student(self, name: str, email: str, password: str) -> dict[str, Any]:
        return self._create(name, email, password, "aluno", [])

    def create_staff(
        self,
        name: str,
        email: str,
        password: str,
        role: str,
        subject_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        if role not in {"professor", "moderador"}:
            raise ValueError("Selecione o perfil de professor ou moderador.")
        return self._create(name, email, password, role, subject_ids or [])

    def _create(
        self, name: str, email: str, password: str, role: str, subject_ids: list[str]
    ) -> dict[str, Any]:
        clean_name = name.strip()
        clean_email = email.strip().casefold()
        if len(clean_name) < 2:
            raise ValueError("Informe um nome com pelo menos duas letras.")
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", clean_email):
            raise ValueError("Informe um e-mail válido.")
        if len(password) < 8:
            raise ValueError("A senha precisa ter pelo menos oito caracteres.")
        if any(item.get("email", "").casefold() == clean_email for item in self._users):
            raise ValueError("Já existe uma conta com esse e-mail.")

        salt = secrets.token_bytes(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, self.ITERATIONS
        )
        record = {
            "id": uuid4().hex,
            "name": clean_name,
            "email": clean_email,
            "role": role,
            "papel": role,
            "materias_responsaveis": sorted(set(subject_ids)),
            "picture": "",
            "active": True,
            "password_salt": salt.hex(),
            "password_hash": password_hash.hex(),
        }
        self._users.append(record)
        self._persist()
        return self._public(record)

    def authenticate(self, email: str, password: str) -> dict[str, Any]:
        normalized = email.strip().casefold()
        record = next(
            (item for item in self._users if item.get("email", "").casefold() == normalized),
            None,
        )
        if record is None or not record.get("active", True):
            raise ValueError("E-mail ou senha incorretos.")
        try:
            salt = bytes.fromhex(record["password_salt"])
            expected = bytes.fromhex(record["password_hash"])
        except (KeyError, ValueError, TypeError):
            raise ValueError("E-mail ou senha incorretos.") from None
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, self.ITERATIONS
        )
        if not hmac.compare_digest(actual, expected):
            raise ValueError("E-mail ou senha incorretos.")
        return self._public(record)

    def update_profile(self, profile: Mapping[str, Any], name: str) -> dict[str, Any]:
        user_id = str(profile.get("id") or profile.get("local_id") or "")
        record = next((item for item in self._users if item.get("id") == user_id), None)
        clean_name = name.strip()
        if len(clean_name) < 2:
            raise ValueError("Informe um nome com pelo menos duas letras.")
        if record is None:
            updated = dict(profile)
            updated["name"] = clean_name
            return updated
        record["name"] = clean_name
        self._persist()
        return self._public(record)

    def set_active(self, user_id: str, active: bool) -> None:
        record = next((item for item in self._users if item.get("id") == user_id), None)
        if record is None:
            raise KeyError("Conta não encontrada.")
        record["active"] = bool(active)
        self._persist()

    def set_subjects(self, user_id: str, subject_ids: list[str]) -> dict[str, Any]:
        record = next((item for item in self._users if item.get("id") == user_id), None)
        if record is None:
            raise KeyError("Conta não encontrada.")
        if record.get("role") != "professor":
            raise ValueError("Somente professores recebem matérias responsáveis.")
        record["materias_responsaveis"] = sorted(set(subject_ids))
        self._persist()
        return self._public(record)

    @staticmethod
    def _public(record: Mapping[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in record.items() if not key.startswith("password_")}

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"versao": 1, "users": self._users}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)
