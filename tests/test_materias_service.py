"""Testes da persistência e da regra local de permissões."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from model.componentes import BotaoAcao
from model.materias import Comentario, Conteudo, Materia, Publicacao, Topico, Trabalho
from service.materias import MateriasService
from service.permissoes import Papel, PermissionService


class MateriasServiceTests(unittest.TestCase):
    def test_crud_persiste_topico_e_conteudo(self):
        with TemporaryDirectory() as folder:
            service = MateriasService(Path(folder) / "materias.json")
            materia = service.salvar_materia(Materia(nome="Programação", criado_por_email="professor@example.com"))
            topico = service.salvar_topico(materia.id, Topico(titulo="Python"))
            service.salvar_conteudo(materia.id, topico.id, Conteudo(titulo="Variáveis", corpo="Material offline"))
            reaberto = MateriasService(service.path).obter(materia.id)
            self.assertEqual(reaberto.topicos[0].conteudos[0].corpo, "Material offline")
            self.assertEqual(reaberto.criado_por_email, "professor@example.com")

    def test_email_de_teste_e_moderador(self):
        permissions = PermissionService()
        self.assertEqual(permissions.papel_do_email("duolinfo.cefet@gmail.com"), Papel.MODERADOR)
        self.assertTrue(permissions.pode_editar_materias("duolinfo.cefet@gmail.com"))
        self.assertFalse(permissions.pode_editar_materias("aluno@example.com"))
        self.assertEqual(permissions.papel_do_perfil({"email": "aluno@example.com", "role": "professor"}), Papel.PROFESSOR)

    def test_professor_cria_e_gerencia_apenas_as_proprias_equipes(self):
        permissions = PermissionService()
        professor = {"email": "professor@example.com", "role": "professor"}
        self.assertTrue(permissions.perfil_pode_gerenciar_materias(professor))
        self.assertTrue(permissions.perfil_pode_gerenciar_materias(professor, "PROFESSOR@example.com"))
        self.assertFalse(permissions.perfil_pode_gerenciar_materias(professor, "outra@example.com"))
        self.assertTrue(permissions.perfil_pode_editar_conteudo(professor, "turma-1", "professor@example.com"))
        self.assertFalse(permissions.perfil_pode_editar_conteudo(professor, "turma-2", "outra@example.com"))

    def test_post_trabalho_e_comentario_sobrevivem_reabertura(self):
        with TemporaryDirectory() as folder:
            service = MateriasService(Path(folder) / "materias.json")
            materia = service.salvar_materia(Materia(nome="Redes"))
            post = service.salvar_publicacao(materia.id, Publicacao(titulo="Bem-vindos", mensagem="Primeiro aviso", autor="Professor"))
            service.comentar_publicacao(materia.id, post.id, Comentario(autor="Aluno", mensagem="Entendido"))
            trabalho = service.salvar_trabalho(materia.id, Trabalho(titulo="Projeto", prazo="30/08/2026"))
            service.entregar_trabalho(materia.id, trabalho.id, "aluno@example.com")
            reaberto = MateriasService(service.path).obter(materia.id)
            self.assertEqual(reaberto.publicacoes[0].comentarios[0].mensagem, "Entendido")
            self.assertIn("aluno@example.com", reaberto.trabalhos[0].entregue_por)

    def test_botao_acao_suporta_icone_na_direita(self):
        botao = BotaoAcao(text="Prosseguir", icone="arrow-right", icon_position="right")
        self.assertEqual(botao.icon_position, "right")
        self.assertEqual(botao.icone, "arrow-right")


if __name__ == "__main__":
    unittest.main()
