"""Fixtures dos testes de integração: um banco SQLite temporário com as migrações do app e um
relógio que só anda quando o teste manda."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path

import pytest

from plataforma.banco import PASTA_MIGRACOES, aplicar_migracoes, conectar, transacao
from plataforma.compartilhado.horario import BRASILIA
from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.turmas.domain.mensalidade import Mensalidade, vencimento
from plataforma.modules.turmas.infra.repositorio_de_turmas import RepositorioDeTurmasSqlite


class RelogioDeTeste:
    """Relógio falso: fica parado, e o teste o avança quando quiser."""

    def __init__(self, inicio: datetime) -> None:
        self._agora = inicio

    def agora(self) -> datetime:
        return self._agora

    def avancar(self, **intervalo: float) -> None:
        self._agora += timedelta(**intervalo)


def pagar_mensalidades(
    conexao: sqlite3.Connection, aluno_id: int, turma_id: int, quantas: int = 12
) -> None:
    """Grava as próximas mensalidades da matrícula como pagas no dia do vencimento, como se o
    aluno tivesse pago em dia. Assim ele não perde a vaga por atraso (R28) nos testes de outras
    regras, que avançam meses."""
    turmas = RepositorioDeTurmasSqlite(conexao)
    matricula = next(m for m in turmas.matriculas_do_aluno(aluno_id) if m.turma_id == turma_id)
    pagas = turmas.mensalidades(matricula.id)
    valor = pagas[0].valor_em_centavos
    data_da_matricula = matricula.matriculada_em.date()
    for numero in range(len(pagas) + 1, len(pagas) + quantas + 1):
        vence_em = vencimento(data_da_matricula, numero)
        paga_em = datetime.combine(vence_em, matricula.matriculada_em.timetz())
        turmas.pagar_mensalidade(matricula.id, Mensalidade(vence_em, valor, paga_em))


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


@pytest.fixture
def relogio() -> RelogioDeTeste:
    return RelogioDeTeste(datetime(2026, 11, 23, 14, 0, tzinfo=BRASILIA))
