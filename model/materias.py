"""Entidades do domínio de matérias, independentes da interface."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def novo_id() -> str:
    return uuid4().hex


@dataclass
class Conteudo:
    id: str = field(default_factory=novo_id)
    titulo: str = ""
    descricao: str = ""
    categoria: str = "teorico"  # teorico | pratico
    corpo: str = ""
    status: str = "publicado"
    criado_em: str = field(default_factory=agora)
    atualizado_em: str = field(default_factory=agora)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Conteudo":
        allowed = {key: value[key] for key in cls.__dataclass_fields__ if key in value}
        return cls(**allowed)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Comentario:
    id: str = field(default_factory=novo_id)
    autor: str = ""
    mensagem: str = ""
    criado_em: str = field(default_factory=agora)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Comentario":
        return cls(**{key: value[key] for key in cls.__dataclass_fields__ if key in value})


@dataclass
class Publicacao:
    id: str = field(default_factory=novo_id)
    titulo: str = ""
    mensagem: str = ""
    autor: str = ""
    tipo: str = "aviso"  # aviso | conteudo | tarefa | recado
    status: str = "publicado"
    anexos: list[str] = field(default_factory=list)
    comentarios: list[Comentario] = field(default_factory=list)
    criado_em: str = field(default_factory=agora)
    atualizado_em: str = field(default_factory=agora)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Publicacao":
        data = {key: value[key] for key in cls.__dataclass_fields__ if key in value and key != "comentarios"}
        data["comentarios"] = [Comentario.from_dict(item) for item in value.get("comentarios", []) if isinstance(item, dict)]
        return cls(**data)


@dataclass
class ArquivoCompartilhado:
    id: str = field(default_factory=novo_id)
    nome: str = ""
    caminho_local: str = ""
    tipo: str = "arquivo"
    tamanho: int = 0
    autor: str = ""
    status: str = "disponivel"
    criado_em: str = field(default_factory=agora)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ArquivoCompartilhado":
        return cls(**{key: value[key] for key in cls.__dataclass_fields__ if key in value})


@dataclass
class Trabalho:
    id: str = field(default_factory=novo_id)
    titulo: str = ""
    descricao: str = ""
    prazo: str = "Sem prazo"
    categoria: str = "Trabalho"
    status: str = "aberto"
    anexos: list[str] = field(default_factory=list)
    criado_por: str = ""
    entregue_por: list[str] = field(default_factory=list)
    criado_em: str = field(default_factory=agora)
    atualizado_em: str = field(default_factory=agora)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Trabalho":
        return cls(**{key: value[key] for key in cls.__dataclass_fields__ if key in value})


@dataclass
class Topico:
    id: str = field(default_factory=novo_id)
    titulo: str = ""
    descricao: str = ""
    status: str = "ativo"
    conteudos: list[Conteudo] = field(default_factory=list)
    criado_em: str = field(default_factory=agora)
    atualizado_em: str = field(default_factory=agora)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Topico":
        allowed = {key: value[key] for key in cls.__dataclass_fields__ if key in value and key != "conteudos"}
        allowed["conteudos"] = [Conteudo.from_dict(item) for item in value.get("conteudos", []) if isinstance(item, dict)]
        return cls(**allowed)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["conteudos"] = [item.to_dict() for item in self.conteudos]
        return data


@dataclass
class Materia:
    id: str = field(default_factory=novo_id)
    nome: str = ""
    descricao: str = ""
    categoria: str = "Geral"
    status: str = "ativa"
    topicos: list[Topico] = field(default_factory=list)
    publicacoes: list[Publicacao] = field(default_factory=list)
    arquivos: list[ArquivoCompartilhado] = field(default_factory=list)
    trabalhos: list[Trabalho] = field(default_factory=list)
    criado_em: str = field(default_factory=agora)
    atualizado_em: str = field(default_factory=agora)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Materia":
        nested = {"topicos", "publicacoes", "arquivos", "trabalhos"}
        allowed = {key: value[key] for key in cls.__dataclass_fields__ if key in value and key not in nested}
        allowed["topicos"] = [Topico.from_dict(item) for item in value.get("topicos", []) if isinstance(item, dict)]
        allowed["publicacoes"] = [Publicacao.from_dict(item) for item in value.get("publicacoes", []) if isinstance(item, dict)]
        allowed["arquivos"] = [ArquivoCompartilhado.from_dict(item) for item in value.get("arquivos", []) if isinstance(item, dict)]
        allowed["trabalhos"] = [Trabalho.from_dict(item) for item in value.get("trabalhos", []) if isinstance(item, dict)]
        return cls(**allowed)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["topicos"] = [item.to_dict() for item in self.topicos]
        data["publicacoes"] = [asdict(item) for item in self.publicacoes]
        data["arquivos"] = [asdict(item) for item in self.arquivos]
        data["trabalhos"] = [asdict(item) for item in self.trabalhos]
        return data
