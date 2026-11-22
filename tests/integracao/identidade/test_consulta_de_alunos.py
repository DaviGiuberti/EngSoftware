"""Os outros módulos acham o aluno pelo e-mail, como o ADM nas exceções do nivelamento (H33)."""

import sqlite3

import pytest

from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.application.casos_de_uso import (
    CadastrarAluno,
    ConsultaDeAlunos,
    CriarPrimeiroAdm,
)
from plataforma.modules.identidade.domain.cadastro import AlunoNaoEncontrado
from plataforma.modules.identidade.infra.repositorio_de_usuarios import (
    RepositorioDeUsuariosSqlite,
)


@pytest.fixture
def usuarios(conexao: sqlite3.Connection) -> RepositorioDeUsuariosSqlite:
    return RepositorioDeUsuariosSqlite(conexao)


def test_o_aluno_e_achado_pelo_email_sem_diferenciar_maiusculas(
    usuarios: RepositorioDeUsuariosSqlite, em_transacao: Transacao
) -> None:
    ana = CadastrarAluno(usuarios, em_transacao).executar("ana@exemplo.com", "abcd1234")

    assert ConsultaDeAlunos(usuarios).obter_por_email(" Ana@Exemplo.com ") == ana


def test_email_sem_conta_e_recusado(usuarios: RepositorioDeUsuariosSqlite) -> None:
    with pytest.raises(AlunoNaoEncontrado, match="Nenhum aluno com este e-mail."):
        ConsultaDeAlunos(usuarios).obter_por_email("ninguem@exemplo.com")


def test_o_email_do_adm_nao_e_de_aluno(
    usuarios: RepositorioDeUsuariosSqlite, em_transacao: Transacao
) -> None:
    CriarPrimeiroAdm(usuarios, em_transacao).executar("adm@exemplo.com", "admin123")

    with pytest.raises(AlunoNaoEncontrado):
        ConsultaDeAlunos(usuarios).obter_por_email("adm@exemplo.com")


def test_o_aluno_e_achado_pelo_id(
    usuarios: RepositorioDeUsuariosSqlite, em_transacao: Transacao
) -> None:
    ana = CadastrarAluno(usuarios, em_transacao).executar("ana@exemplo.com", "abcd1234")

    assert ConsultaDeAlunos(usuarios).obter(ana.id) == ana


def test_o_id_do_adm_nao_e_de_aluno(
    usuarios: RepositorioDeUsuariosSqlite, em_transacao: Transacao
) -> None:
    adm = CriarPrimeiroAdm(usuarios, em_transacao).executar("adm@exemplo.com", "admin123")

    with pytest.raises(AlunoNaoEncontrado):
        ConsultaDeAlunos(usuarios).obter(adm.id)
    with pytest.raises(AlunoNaoEncontrado):
        ConsultaDeAlunos(usuarios).obter(999)
