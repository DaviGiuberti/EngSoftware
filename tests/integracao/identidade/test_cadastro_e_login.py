"""Cadastro, login e primeiro ADM com o banco SQLite (H38): RNF06, RNF08 e R39."""

import sqlite3

import pytest

from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.application.casos_de_uso import (
    CadastrarAluno,
    CriarPrimeiroAdm,
    Entrar,
)
from plataforma.modules.identidade.domain.cadastro import EmailJaCadastrado, PrimeiroAdmJaCriado
from plataforma.modules.identidade.domain.login import LoginInvalido
from plataforma.modules.identidade.domain.senha import SenhaCurta
from plataforma.modules.identidade.domain.usuario import Perfil
from plataforma.modules.identidade.infra.repositorio_de_usuarios import (
    RepositorioDeUsuariosSqlite,
)


@pytest.fixture
def usuarios(conexao: sqlite3.Connection) -> RepositorioDeUsuariosSqlite:
    return RepositorioDeUsuariosSqlite(conexao)


@pytest.fixture
def cadastrar_aluno(
    usuarios: RepositorioDeUsuariosSqlite, em_transacao: Transacao
) -> CadastrarAluno:
    return CadastrarAluno(usuarios, em_transacao)


@pytest.fixture
def entrar(usuarios: RepositorioDeUsuariosSqlite) -> Entrar:
    return Entrar(usuarios)


@pytest.fixture
def criar_primeiro_adm(
    usuarios: RepositorioDeUsuariosSqlite, em_transacao: Transacao
) -> CriarPrimeiroAdm:
    return CriarPrimeiroAdm(usuarios, em_transacao)


def emails_cadastrados(conexao: sqlite3.Connection) -> list[str]:
    return [email for (email,) in conexao.execute("SELECT email FROM usuario ORDER BY id")]


def valores_guardados_das_senhas(conexao: sqlite3.Connection) -> list[str]:
    return [valor for (valor,) in conexao.execute("SELECT hash_da_senha FROM usuario")]


def test_rnf06_senha_com_7_caracteres_e_recusada_e_nada_e_gravado(
    cadastrar_aluno: CadastrarAluno, conexao: sqlite3.Connection
) -> None:
    with pytest.raises(SenhaCurta):
        cadastrar_aluno.executar("ana@exemplo.com", "abc1234")

    assert emails_cadastrados(conexao) == []


def test_rnf06_com_senha_de_8_caracteres_o_aluno_entra_e_o_banco_nao_guarda_a_senha(
    cadastrar_aluno: CadastrarAluno, entrar: Entrar, conexao: sqlite3.Connection
) -> None:
    cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")

    ana = entrar.executar("ana@exemplo.com", "abcd1234")

    assert ana.email == "ana@exemplo.com"
    assert ana.perfil is Perfil.ALUNO
    [valor_guardado] = valores_guardados_das_senhas(conexao)
    assert valor_guardado != "abcd1234"
    assert "abcd1234" not in valor_guardado


def test_r39_email_ja_cadastrado_com_outras_maiusculas_e_recusado(
    cadastrar_aluno: CadastrarAluno, conexao: sqlite3.Connection
) -> None:
    cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")

    with pytest.raises(EmailJaCadastrado, match="Este e-mail já está cadastrado."):
        cadastrar_aluno.executar("Ana@Exemplo.com", "outra-senha")

    assert emails_cadastrados(conexao) == ["ana@exemplo.com"]


def test_r39_o_aluno_entra_mesmo_digitando_o_email_com_maiusculas_e_espacos(
    cadastrar_aluno: CadastrarAluno, entrar: Entrar
) -> None:
    cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")

    assert entrar.executar(" Ana@Exemplo.com ", "abcd1234").email == "ana@exemplo.com"


def test_senha_errada_e_recusada(cadastrar_aluno: CadastrarAluno, entrar: Entrar) -> None:
    cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")

    with pytest.raises(LoginInvalido, match="E-mail ou senha incorretos."):
        entrar.executar("ana@exemplo.com", "abcd9999")


def test_email_sem_cadastro_e_recusado(entrar: Entrar) -> None:
    with pytest.raises(LoginInvalido, match="E-mail ou senha incorretos."):
        entrar.executar("bruno@exemplo.com", "abcd1234")


def test_primeiro_adm_e_criado_uma_vez_so(
    criar_primeiro_adm: CriarPrimeiroAdm, entrar: Entrar
) -> None:
    assert criar_primeiro_adm.pendente()

    criar_primeiro_adm.executar("adm@exemplo.com", "admin123")

    assert entrar.executar("adm@exemplo.com", "admin123").perfil is Perfil.ADM
    assert not criar_primeiro_adm.pendente()
    with pytest.raises(PrimeiroAdmJaCriado, match="O primeiro ADM já foi criado."):
        criar_primeiro_adm.executar("outro@exemplo.com", "admin123")


def test_rnf06_o_primeiro_adm_tambem_precisa_de_senha_com_8_caracteres(
    criar_primeiro_adm: CriarPrimeiroAdm,
) -> None:
    with pytest.raises(SenhaCurta):
        criar_primeiro_adm.executar("adm@exemplo.com", "admin12")

    assert criar_primeiro_adm.pendente()


def test_r39_o_primeiro_adm_nao_usa_o_email_de_uma_conta_que_ja_existe(
    cadastrar_aluno: CadastrarAluno, criar_primeiro_adm: CriarPrimeiroAdm
) -> None:
    cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")

    with pytest.raises(EmailJaCadastrado):
        criar_primeiro_adm.executar("Ana@Exemplo.com", "admin123")


def test_rnf08_email_com_aspas_e_ponto_e_virgula_e_gravado_e_lido_igual(
    cadastrar_aluno: CadastrarAluno, entrar: Entrar
) -> None:
    email = "o'neil;--@exemplo.com"

    cadastrar_aluno.executar(email, "abcd1234")

    assert entrar.executar(email, "abcd1234").email == email
