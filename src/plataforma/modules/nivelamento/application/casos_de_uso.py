"""Casos de uso do nivelamento: questões (H28). O teste do aluno fica em fazer_nivelamento.py."""

from collections.abc import Sequence
from dataclasses import dataclass

from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.domain.autorizacao import exigir_perfil
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.nivelamento.application.fazer_nivelamento import (
    ConcluirNivelamento,
    DarMaisTempo,
    FecharNivelamento,
    IniciarNivelamento,
    LiberarRefazer,
    RegistrarTempo,
    ResponderQuestao,
    VerMeusNiveis,
)
from plataforma.modules.nivelamento.application.portas import RepositorioDeQuestoes
from plataforma.modules.nivelamento.domain.questao import Questao, nova_questao


class CadastrarQuestao:
    """O ADM cadastra uma questão no nivelamento de uma matéria."""

    def __init__(
        self,
        questoes: RepositorioDeQuestoes,
        materias: ConsultaDeMaterias,
        transacao: Transacao,
    ) -> None:
        self._questoes = questoes
        self._materias = materias
        self._transacao = transacao

    def executar(
        self,
        usuario: Usuario,
        materia_id: int,
        enunciado: str,
        alternativas: Sequence[str],
        indice_da_correta: int | None,
    ) -> Questao:
        exigir_perfil(usuario, Perfil.ADM, "cadastrar questão")
        questao = nova_questao(enunciado, alternativas, indice_da_correta)
        self._materias.obter(materia_id)
        with self._transacao():
            return self._questoes.adicionar(materia_id, questao)


class ListarQuestoes:
    """O ADM vê as questões de uma matéria. Só ele: a lista mostra a alternativa correta."""

    def __init__(self, questoes: RepositorioDeQuestoes) -> None:
        self._questoes = questoes

    def executar(self, usuario: Usuario, materia_id: int) -> list[Questao]:
        exigir_perfil(usuario, Perfil.ADM, "ver as questões do nivelamento")
        return self._questoes.listar(materia_id)


@dataclass(frozen=True)
class CasosDeUsoDoNivelamento:
    """Os casos de uso do módulo, montados pelo main.py e entregues às telas."""

    cadastrar_questao: CadastrarQuestao
    listar_questoes: ListarQuestoes
    iniciar: IniciarNivelamento
    responder: ResponderQuestao
    registrar_tempo: RegistrarTempo
    fechar: FecharNivelamento
    concluir: ConcluirNivelamento
    ver_meus_niveis: VerMeusNiveis
    dar_mais_tempo: DarMaisTempo
    liberar_refazer: LiberarRefazer
