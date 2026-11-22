"""Turmas no SQLite, na tabela turma da migração 0007.

Todo SQL usa parâmetros (RNF08). O início da etapa vai como texto ISO 8601, com o fuso.
"""

import sqlite3
from datetime import datetime, time
from typing import Any

from plataforma.modules.turmas.domain.horario import DiaDaSemana, Horario
from plataforma.modules.turmas.domain.turma import Turma, TurmaNova

# Cada filtro NULL deixa passar todas as turmas: sem filtro, a consulta traz todas.
_TURMAS = (
    "SELECT id, materia_id, nivel, professor_id, primeiro_dia, segundo_dia, inicio, fim, "
    "inicio_da_etapa FROM turma "
    "WHERE (:turma_id IS NULL OR id = :turma_id) "
    "AND (:professor_id IS NULL OR professor_id = :professor_id) "
    "ORDER BY id"
)


def _hora(hora: time) -> str:
    return hora.isoformat(timespec="minutes")


class RepositorioDeTurmasSqlite:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self._conexao = conexao

    def adicionar(self, turma: TurmaNova) -> Turma:
        dias = turma.horario.dias
        segundo_dia = int(dias[1]) if len(dias) > 1 else None
        (turma_id,) = self._conexao.execute(
            "INSERT INTO turma (materia_id, nivel, professor_id, primeiro_dia, segundo_dia, "
            "inicio, fim, inicio_da_etapa) VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
            (
                turma.materia_id,
                turma.nivel,
                turma.professor_id,
                int(dias[0]),
                segundo_dia,
                _hora(turma.horario.inicio),
                _hora(turma.horario.fim),
                turma.inicio_da_etapa.isoformat(),
            ),
        ).fetchone()
        return Turma(
            turma_id,
            turma.materia_id,
            turma.nivel,
            turma.professor_id,
            turma.horario,
            turma.inicio_da_etapa,
        )

    def buscar(self, turma_id: int) -> Turma | None:
        return next(iter(self._ler(turma_id=turma_id)), None)

    def listar(self) -> list[Turma]:
        return self._ler()

    def do_professor(self, professor_id: int) -> list[Turma]:
        return self._ler(professor_id=professor_id)

    def salvar(self, turma: Turma) -> None:
        self._conexao.execute(
            "UPDATE turma SET professor_id = ? WHERE id = ?", (turma.professor_id, turma.id)
        )

    def _ler(self, turma_id: int | None = None, professor_id: int | None = None) -> list[Turma]:
        linhas = self._conexao.execute(
            _TURMAS, {"turma_id": turma_id, "professor_id": professor_id}
        ).fetchall()
        return [self._montar(linha) for linha in linhas]

    def _montar(self, linha: tuple[Any, ...]) -> Turma:
        turma_id, materia_id, nivel, professor_id, primeiro_dia, segundo_dia = linha[:6]
        inicio, fim, inicio_da_etapa = linha[6:]
        dias = [DiaDaSemana(primeiro_dia)]
        if segundo_dia is not None:
            dias.append(DiaDaSemana(segundo_dia))
        horario = Horario(tuple(dias), time.fromisoformat(inicio), time.fromisoformat(fim))
        return Turma(
            turma_id,
            materia_id,
            nivel,
            professor_id,
            horario,
            datetime.fromisoformat(inicio_da_etapa),
        )
