"""Fixtures dos testes de integração: um banco SQLite temporário com as migrações do app."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from functools import partial
from pathlib import Path

import pytest

from plataforma.banco import PASTA_MIGRACOES, aplicar_migracoes, conectar, transacao
from plataforma.compartilhado.transacao import Transacao


@pytest.fixture
def conexao(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """Banco temporário com as migrações do app, aberto do mesmo jeito que o app abre."""
    caminho_banco = tmp_path / "plataforma.db"
    aplicar_migracoes(caminho_banco, PASTA_MIGRACOES, tmp_path / "copias")
    with closing(conectar(caminho_banco)) as conexao:
        yield conexao


@pytest.fixture
def em_transacao(conexao: sqlite3.Connection) -> Transacao:
    """A transação que os casos de uso recebem, nessa mesma conexão (RNF05)."""
    return partial(transacao, conexao)
