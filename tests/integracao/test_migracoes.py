"""Migrações do banco: ordem, tabela de controle e cópia antes de migrar (RNF16)."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from plataforma.banco import aplicar_migracoes

CRIA_EXEMPLO = "CREATE TABLE exemplo (id INTEGER PRIMARY KEY, nome TEXT NOT NULL);"
INSERE_EXEMPLO = "INSERT INTO exemplo (nome) VALUES ('primeiro');"


@pytest.fixture
def caminho_banco(tmp_path: Path) -> Path:
    return tmp_path / "plataforma.db"


@pytest.fixture
def pasta_migracoes(tmp_path: Path) -> Path:
    pasta = tmp_path / "migracoes"
    pasta.mkdir()
    return pasta


@pytest.fixture
def pasta_copias(tmp_path: Path) -> Path:
    return tmp_path / "copias"


def criar_migracao(pasta: Path, nome: str, sql: str) -> None:
    (pasta / nome).write_text(sql, encoding="utf-8")


def consultar(caminho_banco: Path, sql: str) -> list[tuple[object, ...]]:
    with closing(sqlite3.connect(caminho_banco)) as conexao:
        return conexao.execute(sql).fetchall()


def ultima_aplicada(caminho_banco: Path) -> object:
    [(numero,)] = consultar(caminho_banco, "SELECT ultima_aplicada FROM controle_migracao")
    return numero


def tabelas(caminho_banco: Path) -> set[object]:
    linhas = consultar(caminho_banco, "SELECT name FROM sqlite_master WHERE type = 'table'")
    return {nome for (nome,) in linhas}


def copias(pasta_copias: Path) -> list[str]:
    if not pasta_copias.exists():
        return []
    return sorted(arquivo.name for arquivo in pasta_copias.iterdir())


def test_aplica_as_migracoes_em_ordem_numerica(
    caminho_banco: Path, pasta_migracoes: Path, pasta_copias: Path
) -> None:
    criar_migracao(pasta_migracoes, "0002_insere_exemplo.sql", INSERE_EXEMPLO)
    criar_migracao(pasta_migracoes, "0001_cria_exemplo.sql", CRIA_EXEMPLO)

    aplicar_migracoes(caminho_banco, pasta_migracoes, pasta_copias)

    assert consultar(caminho_banco, "SELECT nome FROM exemplo") == [("primeiro",)]
    assert ultima_aplicada(caminho_banco) == 2


def test_nao_reaplica_migracao_ja_aplicada(
    caminho_banco: Path, pasta_migracoes: Path, pasta_copias: Path
) -> None:
    criar_migracao(pasta_migracoes, "0001_cria_exemplo.sql", CRIA_EXEMPLO)
    criar_migracao(pasta_migracoes, "0002_insere_exemplo.sql", INSERE_EXEMPLO)
    aplicar_migracoes(caminho_banco, pasta_migracoes, pasta_copias)

    aplicar_migracoes(caminho_banco, pasta_migracoes, pasta_copias)

    assert consultar(caminho_banco, "SELECT nome FROM exemplo") == [("primeiro",)]
    assert ultima_aplicada(caminho_banco) == 2
    assert copias(pasta_copias) == []


def test_guarda_copia_do_banco_antes_de_aplicar_migracao_nova(
    caminho_banco: Path, pasta_migracoes: Path, pasta_copias: Path
) -> None:
    criar_migracao(pasta_migracoes, "0001_cria_exemplo.sql", CRIA_EXEMPLO)
    criar_migracao(pasta_migracoes, "0002_insere_exemplo.sql", INSERE_EXEMPLO)
    aplicar_migracoes(caminho_banco, pasta_migracoes, pasta_copias)
    criar_migracao(pasta_migracoes, "0003_cria_outra.sql", "CREATE TABLE outra (id INTEGER);")

    aplicar_migracoes(caminho_banco, pasta_migracoes, pasta_copias)

    assert copias(pasta_copias) == ["plataforma-antes-da-0003.db"]
    copia = pasta_copias / "plataforma-antes-da-0003.db"
    assert ultima_aplicada(copia) == 2
    assert consultar(copia, "SELECT nome FROM exemplo") == [("primeiro",)]
    assert "outra" not in tabelas(copia)
    assert ultima_aplicada(caminho_banco) == 3


def test_mantem_so_as_3_copias_mais_recentes(
    caminho_banco: Path, pasta_migracoes: Path, pasta_copias: Path
) -> None:
    criar_migracao(pasta_migracoes, "0001_cria_exemplo.sql", CRIA_EXEMPLO)
    aplicar_migracoes(caminho_banco, pasta_migracoes, pasta_copias)

    for numero in range(2, 6):
        criar_migracao(pasta_migracoes, f"{numero:04d}_vazia.sql", f"-- migração {numero}")
        aplicar_migracoes(caminho_banco, pasta_migracoes, pasta_copias)

    assert copias(pasta_copias) == [
        "plataforma-antes-da-0003.db",
        "plataforma-antes-da-0004.db",
        "plataforma-antes-da-0005.db",
    ]


def test_banco_novo_nao_gera_copia(
    caminho_banco: Path, pasta_migracoes: Path, pasta_copias: Path
) -> None:
    criar_migracao(pasta_migracoes, "0001_cria_exemplo.sql", CRIA_EXEMPLO)

    aplicar_migracoes(caminho_banco, pasta_migracoes, pasta_copias)

    assert ultima_aplicada(caminho_banco) == 1
    assert copias(pasta_copias) == []


def test_migracao_com_erro_e_desfeita_e_a_versao_nao_muda(
    caminho_banco: Path, pasta_migracoes: Path, pasta_copias: Path
) -> None:
    criar_migracao(pasta_migracoes, "0001_cria_exemplo.sql", CRIA_EXEMPLO)
    criar_migracao(
        pasta_migracoes,
        "0002_com_erro.sql",
        "CREATE TABLE parcial (id INTEGER);\nINSERT INTO tabela_que_nao_existe VALUES (1);",
    )

    with pytest.raises(sqlite3.Error) as erro:
        aplicar_migracoes(caminho_banco, pasta_migracoes, pasta_copias)

    assert "0002_com_erro.sql" in " ".join(getattr(erro.value, "__notes__", []))
    assert ultima_aplicada(caminho_banco) == 1
    assert "parcial" not in tabelas(caminho_banco)
