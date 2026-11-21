"""Cadastro e habilitação de professores com o banco SQLite (H29): R11, R39, RNF06 e RNF07."""

import sqlite3
from dataclasses import dataclass

import pytest

from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.application.casos_de_uso import (
    CadastrarAluno,
    CadastrarProfessor,
    ConsultaDeProfessores,
    Entrar,
    HabilitarProfessor,
)
from plataforma.modules.identidade.domain.autorizacao import AcessoNegado
from plataforma.modules.identidade.domain.cadastro import EmailJaCadastrado
from plataforma.modules.identidade.domain.professor import (
    HabilitacaoRepetida,
    Professor,
    ProfessorNaoEncontrado,
)
from plataforma.modules.identidade.domain.senha import SenhaCurta
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.identidade.infra.repositorio_de_professores import (
    RepositorioDeProfessoresSqlite,
)
from plataforma.modules.identidade.infra.repositorio_de_usuarios import (
    RepositorioDeUsuariosSqlite,
)
from plataforma.modules.materias.application.casos_de_uso import (
    CadastrarMateria,
    ConsultaDeMaterias,
)
from plataforma.modules.materias.domain.materia import Materia, MateriaNaoEncontrada
from plataforma.modules.materias.infra.repositorio_de_materias import (
    RepositorioDeMateriasSqlite,
)

ADM = Usuario(id=1000, email="adm@exemplo.com", perfil=Perfil.ADM)


@dataclass(frozen=True)
class Casos:
    cadastrar_aluno: CadastrarAluno
    cadastrar_professor: CadastrarProfessor
    habilitar_professor: HabilitarProfessor
    professores: ConsultaDeProfessores
    entrar: Entrar
    cadastrar_materia: CadastrarMateria


@pytest.fixture
def casos(conexao: sqlite3.Connection, em_transacao: Transacao) -> Casos:
    usuarios = RepositorioDeUsuariosSqlite(conexao)
    professores = RepositorioDeProfessoresSqlite(conexao)
    materias = RepositorioDeMateriasSqlite(conexao)
    return Casos(
        cadastrar_aluno=CadastrarAluno(usuarios, em_transacao),
        cadastrar_professor=CadastrarProfessor(usuarios, em_transacao),
        habilitar_professor=HabilitarProfessor(
            professores, ConsultaDeMaterias(materias), em_transacao
        ),
        professores=ConsultaDeProfessores(professores),
        entrar=Entrar(usuarios),
        cadastrar_materia=CadastrarMateria(materias, em_transacao),
    )


@pytest.fixture
def fisica(casos: Casos) -> Materia:
    return casos.cadastrar_materia.executar(ADM, "Física", 3, [40, 70], 20000)


@pytest.fixture
def matematica(casos: Casos) -> Materia:
    return casos.cadastrar_materia.executar(ADM, "Matemática", 5, [20, 40, 60, 80], 25000)


@pytest.fixture
def carlos(casos: Casos) -> Usuario:
    return casos.cadastrar_professor.executar(ADM, "carlos@exemplo.com", "abcd1234")


def test_dora_cadastrada_pelo_adm_entra_na_plataforma_com_o_perfil_de_professor(
    casos: Casos,
) -> None:
    casos.cadastrar_professor.executar(ADM, "dora@exemplo.com", "abcd1234")

    dora = casos.entrar.executar("dora@exemplo.com", "abcd1234")

    assert dora.email == "dora@exemplo.com"
    assert dora.perfil is Perfil.PROFESSOR


def test_rnf06_senha_do_professor_com_7_caracteres_e_recusada_e_nada_e_gravado(
    casos: Casos,
) -> None:
    with pytest.raises(SenhaCurta):
        casos.cadastrar_professor.executar(ADM, "dora@exemplo.com", "abc1234")

    assert casos.professores.listar() == []


def test_r39_professor_com_o_email_de_um_aluno_e_recusado(casos: Casos) -> None:
    casos.cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")

    with pytest.raises(EmailJaCadastrado, match="Este e-mail já está cadastrado."):
        casos.cadastrar_professor.executar(ADM, "Ana@Exemplo.com", "abcd1234")

    assert casos.professores.listar() == []


def test_rnf07_aluno_nao_cadastra_professor(casos: Casos) -> None:
    ana = casos.cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")

    with pytest.raises(AcessoNegado, match="Só o ADM pode cadastrar professor."):
        casos.cadastrar_professor.executar(ana, "dora@exemplo.com", "abcd1234")

    assert casos.professores.listar() == []


def test_r11_carlos_habilitado_em_fisica_fica_com_a_habilitacao_gravada(
    casos: Casos, carlos: Usuario, fisica: Materia
) -> None:
    habilitado = casos.habilitar_professor.executar(ADM, carlos.id, fisica.id)

    assert habilitado.materias_habilitadas == {fisica.id}
    assert casos.professores.obter(carlos.id).materias_habilitadas == {fisica.id}


def test_r11_dora_habilitada_em_fisica_e_em_matematica(
    casos: Casos, fisica: Materia, matematica: Materia
) -> None:
    dora = casos.cadastrar_professor.executar(ADM, "dora@exemplo.com", "abcd1234")

    casos.habilitar_professor.executar(ADM, dora.id, fisica.id)
    casos.habilitar_professor.executar(ADM, dora.id, matematica.id)

    assert casos.professores.obter(dora.id).materias_habilitadas == {fisica.id, matematica.id}


def test_r11_habilitacao_repetida_e_recusada_e_a_habilitacao_continua_uma_so(
    casos: Casos, carlos: Usuario, fisica: Materia
) -> None:
    casos.habilitar_professor.executar(ADM, carlos.id, fisica.id)

    with pytest.raises(
        HabilitacaoRepetida, match="carlos@exemplo.com já tem habilitação em Física."
    ):
        casos.habilitar_professor.executar(ADM, carlos.id, fisica.id)

    assert casos.professores.obter(carlos.id).materias_habilitadas == {fisica.id}


def test_habilitar_numa_materia_que_nao_existe_e_recusado(
    casos: Casos, carlos: Usuario
) -> None:
    with pytest.raises(MateriaNaoEncontrada):
        casos.habilitar_professor.executar(ADM, carlos.id, 999)

    assert casos.professores.obter(carlos.id).materias_habilitadas == frozenset()


def test_habilitar_quem_nao_e_professor_e_recusado(casos: Casos, fisica: Materia) -> None:
    ana = casos.cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")

    with pytest.raises(ProfessorNaoEncontrado, match="Professor não encontrado."):
        casos.habilitar_professor.executar(ADM, ana.id, fisica.id)


def test_rnf07_professor_nao_se_habilita_sozinho(
    casos: Casos, carlos: Usuario, fisica: Materia
) -> None:
    with pytest.raises(AcessoNegado, match="Só o ADM pode habilitar professor."):
        casos.habilitar_professor.executar(carlos, carlos.id, fisica.id)

    assert casos.professores.obter(carlos.id).materias_habilitadas == frozenset()


def test_os_professores_sao_listados_por_email_com_as_habilitacoes(
    casos: Casos, carlos: Usuario, fisica: Materia
) -> None:
    dora = casos.cadastrar_professor.executar(ADM, "dora@exemplo.com", "abcd1234")
    casos.cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")
    casos.habilitar_professor.executar(ADM, carlos.id, fisica.id)

    assert casos.professores.listar() == [
        Professor(carlos, frozenset({fisica.id})),
        Professor(dora, frozenset()),
    ]


def test_professor_que_nao_existe_e_recusado(casos: Casos) -> None:
    with pytest.raises(ProfessorNaoEncontrado, match="Professor não encontrado."):
        casos.professores.obter(999)
