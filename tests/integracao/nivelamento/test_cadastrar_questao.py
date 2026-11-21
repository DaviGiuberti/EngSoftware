"""Cadastro de questões do nivelamento com o banco SQLite (H28): R41 e RNF07."""

import sqlite3

import pytest

from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.domain.autorizacao import AcessoNegado
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.materias.application.casos_de_uso import (
    CadastrarMateria,
    ConsultaDeMaterias,
)
from plataforma.modules.materias.domain.materia import Materia, MateriaNaoEncontrada
from plataforma.modules.materias.infra.repositorio_de_materias import (
    RepositorioDeMateriasSqlite,
)
from plataforma.modules.nivelamento.application.casos_de_uso import (
    CadastrarQuestao,
    ListarQuestoes,
)
from plataforma.modules.nivelamento.domain.questao import AlternativasIncompletas
from plataforma.modules.nivelamento.infra.repositorio_de_questoes import (
    RepositorioDeQuestoesSqlite,
)

ADM = Usuario(id=1, email="adm@exemplo.com", perfil=Perfil.ADM)
ANA = Usuario(id=2, email="ana@exemplo.com", perfil=Perfil.ALUNO)
ENUNCIADO = "Um carro anda 100 m em 25 s. Qual é a velocidade média?"
ALTERNATIVAS = ["2 m/s", "4 m/s", "6 m/s", "8 m/s", "10 m/s"]


@pytest.fixture
def materias(conexao: sqlite3.Connection) -> ConsultaDeMaterias:
    return ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao))


@pytest.fixture
def fisica(conexao: sqlite3.Connection, em_transacao: Transacao) -> Materia:
    cadastrar_materia = CadastrarMateria(RepositorioDeMateriasSqlite(conexao), em_transacao)
    return cadastrar_materia.executar(ADM, "Física", 3, [40, 70], 20000)


@pytest.fixture
def questoes(conexao: sqlite3.Connection) -> RepositorioDeQuestoesSqlite:
    return RepositorioDeQuestoesSqlite(conexao)


@pytest.fixture
def cadastrar_questao(
    questoes: RepositorioDeQuestoesSqlite,
    materias: ConsultaDeMaterias,
    em_transacao: Transacao,
) -> CadastrarQuestao:
    return CadastrarQuestao(questoes, materias, em_transacao)


@pytest.fixture
def listar_questoes(questoes: RepositorioDeQuestoesSqlite) -> ListarQuestoes:
    return ListarQuestoes(questoes)


def test_questao_de_fisica_com_5_alternativas_passa_a_fazer_parte_do_nivelamento(
    cadastrar_questao: CadastrarQuestao, listar_questoes: ListarQuestoes, fisica: Materia
) -> None:
    questao = cadastrar_questao.executar(ADM, fisica.id, ENUNCIADO, ALTERNATIVAS, 1)

    assert listar_questoes.executar(ADM, fisica.id) == [questao]
    assert [alternativa.texto for alternativa in questao.alternativas] == ALTERNATIVAS
    assert questao.letra_da_correta == "B"


def test_r41_questao_com_4_alternativas_e_recusada_e_nada_e_gravado(
    cadastrar_questao: CadastrarQuestao, listar_questoes: ListarQuestoes, fisica: Materia
) -> None:
    with pytest.raises(AlternativasIncompletas):
        cadastrar_questao.executar(ADM, fisica.id, ENUNCIADO, ALTERNATIVAS[:4], 1)

    assert listar_questoes.executar(ADM, fisica.id) == []


def test_as_questoes_ficam_na_ordem_em_que_foram_cadastradas(
    cadastrar_questao: CadastrarQuestao, listar_questoes: ListarQuestoes, fisica: Materia
) -> None:
    primeira = cadastrar_questao.executar(ADM, fisica.id, "Primeira?", ALTERNATIVAS, 0)
    segunda = cadastrar_questao.executar(ADM, fisica.id, "Segunda?", ALTERNATIVAS, 4)

    assert listar_questoes.executar(ADM, fisica.id) == [primeira, segunda]


def test_as_questoes_de_uma_materia_nao_aparecem_em_outra(
    conexao: sqlite3.Connection,
    em_transacao: Transacao,
    cadastrar_questao: CadastrarQuestao,
    listar_questoes: ListarQuestoes,
    fisica: Materia,
) -> None:
    cadastrar_materia = CadastrarMateria(RepositorioDeMateriasSqlite(conexao), em_transacao)
    matematica = cadastrar_materia.executar(ADM, "Matemática", 5, [20, 40, 60, 80], 25000)

    cadastrar_questao.executar(ADM, fisica.id, ENUNCIADO, ALTERNATIVAS, 1)

    assert listar_questoes.executar(ADM, matematica.id) == []


def test_questao_de_materia_que_nao_existe_e_recusada(
    cadastrar_questao: CadastrarQuestao,
) -> None:
    with pytest.raises(MateriaNaoEncontrada):
        cadastrar_questao.executar(ADM, 999, ENUNCIADO, ALTERNATIVAS, 1)


def test_rnf07_aluno_nao_cadastra_questao(
    cadastrar_questao: CadastrarQuestao, listar_questoes: ListarQuestoes, fisica: Materia
) -> None:
    with pytest.raises(AcessoNegado, match="Só o ADM pode cadastrar questão."):
        cadastrar_questao.executar(ANA, fisica.id, ENUNCIADO, ALTERNATIVAS, 1)

    assert listar_questoes.executar(ADM, fisica.id) == []


def test_rnf07_aluno_nao_ve_as_questoes_com_as_respostas(
    listar_questoes: ListarQuestoes, fisica: Materia
) -> None:
    with pytest.raises(AcessoNegado, match="Só o ADM pode ver as questões do nivelamento."):
        listar_questoes.executar(ANA, fisica.id)
