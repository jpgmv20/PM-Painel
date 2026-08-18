"""Repositório local de matérias. A API pública permite futura troca por servidor."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from model.materias import ArquivoCompartilhado, Comentario, Conteudo, Materia, Publicacao, Topico, Trabalho, agora, novo_id


class MateriasService:
    VERSAO = 2

    def __init__(self, path: str | Path | None = None) -> None:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        self.path = Path(path) if path else base / "PM-Painel" / "materias.json"
        self._materias: list[Materia] = []
        self.carregar()

    def carregar(self) -> list[Materia]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            values = raw.get("materias", []) if isinstance(raw, dict) else []
            self._materias = [Materia.from_dict(item) for item in values if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            self._materias = []
        return self.listar()

    def listar(self) -> list[Materia]:
        return list(self._materias)

    def obter(self, materia_id: str) -> Materia:
        for materia in self._materias:
            if materia.id == materia_id:
                return materia
        raise KeyError("Matéria não encontrada.")

    def salvar_materia(self, materia: Materia) -> Materia:
        if not materia.nome.strip():
            raise ValueError("Informe o nome da matéria.")
        materia.nome = materia.nome.strip()
        materia.atualizado_em = agora()
        for index, current in enumerate(self._materias):
            if current.id == materia.id:
                self._materias[index] = materia
                self._persistir()
                return materia
        self._materias.append(materia)
        self._persistir()
        return materia

    def excluir_materia(self, materia_id: str) -> None:
        self._materias = [item for item in self._materias if item.id != materia_id]
        self._persistir()

    def salvar_topico(self, materia_id: str, topico: Topico) -> Topico:
        materia = self.obter(materia_id)
        if not topico.titulo.strip():
            raise ValueError("Informe o título do tópico.")
        topico.titulo = topico.titulo.strip()
        topico.atualizado_em = agora()
        for index, current in enumerate(materia.topicos):
            if current.id == topico.id:
                materia.topicos[index] = topico
                break
        else:
            materia.topicos.append(topico)
        materia.atualizado_em = agora()
        self._persistir()
        return topico

    def excluir_topico(self, materia_id: str, topico_id: str) -> None:
        materia = self.obter(materia_id)
        materia.topicos = [item for item in materia.topicos if item.id != topico_id]
        materia.atualizado_em = agora()
        self._persistir()

    def salvar_conteudo(self, materia_id: str, topico_id: str, conteudo: Conteudo) -> Conteudo:
        topico = self._topico(materia_id, topico_id)
        if not conteudo.titulo.strip():
            raise ValueError("Informe o título do conteúdo.")
        conteudo.titulo = conteudo.titulo.strip()
        conteudo.atualizado_em = agora()
        for index, current in enumerate(topico.conteudos):
            if current.id == conteudo.id:
                topico.conteudos[index] = conteudo
                break
        else:
            topico.conteudos.append(conteudo)
        self.obter(materia_id).atualizado_em = agora()
        self._persistir()
        return conteudo

    def excluir_conteudo(self, materia_id: str, topico_id: str, conteudo_id: str) -> None:
        topico = self._topico(materia_id, topico_id)
        topico.conteudos = [item for item in topico.conteudos if item.id != conteudo_id]
        self._persistir()

    def salvar_publicacao(self, materia_id: str, publicacao: Publicacao) -> Publicacao:
        materia = self.obter(materia_id)
        if not publicacao.titulo.strip() or not publicacao.mensagem.strip():
            raise ValueError("Informe o título e a mensagem da publicação.")
        publicacao.titulo, publicacao.mensagem = publicacao.titulo.strip(), publicacao.mensagem.strip()
        publicacao.atualizado_em = agora()
        self._substituir_ou_adicionar(materia.publicacoes, publicacao)
        materia.atualizado_em = agora(); self._persistir()
        return publicacao

    def comentar_publicacao(self, materia_id: str, publicacao_id: str, comentario: Comentario) -> Comentario:
        if not comentario.mensagem.strip():
            raise ValueError("Escreva uma resposta antes de publicar.")
        publicacao = next((item for item in self.obter(materia_id).publicacoes if item.id == publicacao_id), None)
        if publicacao is None: raise KeyError("Publicação não encontrada.")
        publicacao.comentarios.append(comentario); publicacao.atualizado_em = agora(); self._persistir()
        return comentario

    def excluir_publicacao(self, materia_id: str, publicacao_id: str) -> None:
        materia = self.obter(materia_id)
        materia.publicacoes = [item for item in materia.publicacoes if item.id != publicacao_id]
        self._persistir()

    def salvar_trabalho(self, materia_id: str, trabalho: Trabalho) -> Trabalho:
        materia = self.obter(materia_id)
        if not trabalho.titulo.strip(): raise ValueError("Informe o título do trabalho.")
        trabalho.titulo = trabalho.titulo.strip(); trabalho.atualizado_em = agora()
        self._substituir_ou_adicionar(materia.trabalhos, trabalho)
        materia.atualizado_em = agora(); self._persistir()
        return trabalho

    def entregar_trabalho(self, materia_id: str, trabalho_id: str, email: str) -> Trabalho:
        trabalho = next((item for item in self.obter(materia_id).trabalhos if item.id == trabalho_id), None)
        if trabalho is None: raise KeyError("Trabalho não encontrado.")
        if email and email not in trabalho.entregue_por: trabalho.entregue_por.append(email)
        trabalho.status = "entregue" if email else trabalho.status; trabalho.atualizado_em = agora(); self._persistir()
        return trabalho

    def excluir_trabalho(self, materia_id: str, trabalho_id: str) -> None:
        materia = self.obter(materia_id)
        materia.trabalhos = [item for item in materia.trabalhos if item.id != trabalho_id]; self._persistir()

    def adicionar_arquivo_local(self, materia_id: str, origem: str | Path, autor: str) -> ArquivoCompartilhado:
        source = Path(origem)
        if not source.is_file(): raise ValueError("Selecione um arquivo local válido.")
        destination = self.path.parent / "materias_arquivos" / materia_id / f"{novo_id()}_{source.name}"
        destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, destination)
        arquivo = ArquivoCompartilhado(nome=source.name, caminho_local=str(destination), tipo=source.suffix.lstrip(".").upper() or "arquivo", tamanho=source.stat().st_size, autor=autor)
        self.obter(materia_id).arquivos.append(arquivo); self._persistir(); return arquivo

    def excluir_arquivo(self, materia_id: str, arquivo_id: str) -> None:
        materia = self.obter(materia_id)
        arquivo = next((item for item in materia.arquivos if item.id == arquivo_id), None)
        if arquivo:
            try: Path(arquivo.caminho_local).unlink(missing_ok=True)
            except OSError: pass
        materia.arquivos = [item for item in materia.arquivos if item.id != arquivo_id]; self._persistir()

    @staticmethod
    def _substituir_ou_adicionar(items: list, novo: object) -> None:
        for index, item in enumerate(items):
            if item.id == novo.id:
                items[index] = novo; return
        items.append(novo)

    def _topico(self, materia_id: str, topico_id: str) -> Topico:
        for topico in self.obter(materia_id).topicos:
            if topico.id == topico_id:
                return topico
        raise KeyError("Tópico não encontrado.")

    def _persistir(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"versao": self.VERSAO, "materias": [m.to_dict() for m in self._materias]}, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)
