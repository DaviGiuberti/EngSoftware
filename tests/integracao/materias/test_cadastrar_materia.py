"""Cadastro de matéria com o banco SQLite (H27): R01, R27, R40, RNF05 e RNF07."""

import sqlite3

import pytest

from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.domain.autorizacao import AcessoNegado
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.materias.application.casos_de_uso import (
    CadastrarMateria,
    ConsultaDeMaterias,
)
from plataforma.modules.materias.domain.materia import (
    Faixa,
    FaixasInvalidas,
    Materia,
    MateriaNaoEncontrada,
    NomeJaCadastrado,
)
from plataforma.modules.materias.infra.repositorio_de_materias import (
    RepositorioDeMateriasSqlite,
)

ADM = Usuario(id=1, email="adm@exemplo.com", perfil=Perfil.ADM)
ANA = Usuario(id=2, email="ana@exemplo.com", perfil=Perfil.ALUNO)


@pytest.fixture
def materias(conexao: sqlite3.Connection) -> RepositorioDeMateriasSqlite:
    return RepositorioDeMateriasSqlite(conexao)


@pytest.fixture
def cadastrar_materia(
    materias: RepositorioDeMateriasSqlite, em_transacao: Transacao
) -> CadastrarMateria:
    return CadastrarMateria(materias, em_transacao)


@pytest.fixture
def consulta(materias: RepositorioDeMateriasSqlite) -> ConsultaDeMaterias:
    return ConsultaDeMaterias(materias)


def test_r40_r27_fisica_cadastrada_e_lida_de_volta_com_as_faixas_e_a_mensalidade(
    cadastrar_materia: CadastrarMateria, consulta: ConsultaDeMaterias
) -> None:
    fisica = cadastrar_materia.executar(ADM, "Física", 3, [40, 70], 20000)

    assert consulta.obter(fisica.id) == Materia(
        id=fisica.id,
        nome="Física",
        faixas=(Faixa(1, 0, 39), Faixa(2, 40, 69), Faixa(3, 70, 100)),
        mensalidade_em_centavos=20000,
    )


def test_r01_matematica_com_5_niveis_e_gravada_com_os_niveis_n1_a_n5(
    cadastrar_materia: CadastrarMateria, consulta: ConsultaDeMaterias
) -> None:
    matematica = cadastrar_materia.executar(ADM, "Matemática", 5, [20, 40, 60, 80], 25000)

    gravada = consulta.obter(matematica.id)

    assert gravada.nivel_maximo == 5
    assert [faixa.nivel for faixa in gravada.faixas] == [1, 2, 3, 4, 5]


def test_as_materias_sao_listadas_em_ordem_alfabetica(
    cadastrar_materia: CadastrarMateria, consulta: ConsultaDeMaterias
) -> None:
    cadastrar_materia.executar(ADM, "Matemática", 5, [20, 40, 60, 80], 25000)
    cadastrar_materia.executar(ADM, "Física", 3, [40, 70], 20000)

    assert [materia.nome for materia in consulta.listar()] == ["Física", "Matemática"]


def test_nome_repetido_com_outras_maiusculas_e_recusado(
    cadastrar_materia: CadastrarMateria, consulta: ConsultaDeMaterias
) -> None:
    cadastrar_materia.executar(ADM, "Física", 3, [40, 70], 20000)

    with pytest.raises(NomeJaCadastrado):
        cadastrar_materia.executar(ADM, "FÍSICA", 2, [50], 15000)

    assert [materia.nome for materia in consulta.listar()] == ["Física"]


def test_r40_nota_minima_fora_de_ordem_e_recusada_e_nada_e_gravado(
    cadastrar_materia: CadastrarMateria, consulta: ConsultaDeMaterias
) -> None:
    with pytest.raises(FaixasInvalidas, match="A nota mínima do N3 precisa ser maior que a do N2."):
        cadastrar_materia.executar(ADM, "Física", 3, [70, 40], 20000)

    assert consulta.listar() == []


def test_rnf07_aluno_chamando_cadastrar_materia_e_recusado(
    cadastrar_materia: CadastrarMateria, consulta: ConsultaDeMaterias
) -> None:
    with pytest.raises(AcessoNegado, match="Só o ADM pode cadastrar matéria."):
        cadastrar_materia.executar(ANA, "Física", 3, [40, 70], 20000)

    assert consulta.listar() == []


def test_rnf05_erro_no_meio_do_cadastro_nao_deixa_a_materia_pela_metade(
    conexao: sqlite3.Connection, cadastrar_materia: CadastrarMateria
) -> None:
    # A matéria é gravada antes das faixas. O trigger faz a gravação das faixas falhar.
    conexao.execute(
        "CREATE TRIGGER falha_na_faixa BEFORE INSERT ON faixa "
        "BEGIN SELECT RAISE(ABORT, 'falha forçada no teste'); END"
    )

    with pytest.raises(sqlite3.DatabaseError, match="falha forçada no teste"):
        cadastrar_materia.executar(ADM, "Física", 3, [40, 70], 20000)

    assert conexao.execute("SELECT COUNT(*) FROM materia").fetchone() == (0,)


def test_materia_que_nao_existe_e_recusada(consulta: ConsultaDeMaterias) -> None:
    with pytest.raises(MateriaNaoEncontrada, match="Matéria não encontrada."):
        consulta.obter(999)
