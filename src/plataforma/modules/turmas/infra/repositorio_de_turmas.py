"""Turmas no SQLite: a tabela turma da migração 0007; da 0008, as matrículas, as mensalidades
pagas e as listas de espera; e da 0009, as aulas não realizadas e as presenças.

Todo SQL usa parâmetros (RNF08). Datas e horas vão como texto ISO 8601, com o fuso.
"""

import sqlite3
from collections.abc import Sequence
from datetime import date, datetime, time
from typing import Any

from plataforma.modules.turmas.domain.horario import DiaDaSemana, Horario
from plataforma.modules.turmas.domain.lista_de_espera import ListaDeEspera, NaLista
from plataforma.modules.turmas.domain.matricula import Matricula
from plataforma.modules.turmas.domain.mensalidade import Mensalidade
from plataforma.modules.turmas.domain.presenca import Presenca
from plataforma.modules.turmas.domain.turma import Turma, TurmaNova

# Cada filtro NULL deixa passar todas as matrículas ativas.
_MATRICULAS_ATIVAS = (
    "SELECT id, turma_id, aluno_id, matriculada_em FROM matricula "
    "WHERE saiu_em IS NULL "
    "AND (:turma_id IS NULL OR turma_id = :turma_id) "
    "AND (:aluno_id IS NULL OR aluno_id = :aluno_id) "
    "ORDER BY id"
)

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

    def adicionar_matricula(
        self, turma_id: int, aluno_id: int, matriculada_em: datetime, primeira: Mensalidade
    ) -> Matricula:
        (matricula_id,) = self._conexao.execute(
            "INSERT INTO matricula (turma_id, aluno_id, matriculada_em) VALUES (?, ?, ?) "
            "RETURNING id",
            (turma_id, aluno_id, matriculada_em.isoformat()),
        ).fetchone()
        self._conexao.execute(
            "INSERT INTO mensalidade (matricula_id, vencimento, valor_em_centavos, paga_em) "
            "VALUES (?, ?, ?, ?)",
            (
                matricula_id,
                primeira.vencimento.isoformat(),
                primeira.valor_em_centavos,
                primeira.paga_em.isoformat(),
            ),
        )
        return Matricula(matricula_id, turma_id, aluno_id, matriculada_em)

    def matriculas_da_turma(self, turma_id: int) -> list[Matricula]:
        return self._matriculas(turma_id=turma_id)

    def matriculas_do_aluno(self, aluno_id: int) -> list[Matricula]:
        return self._matriculas(aluno_id=aluno_id)

    def encerrar_matricula(self, matricula_id: int, saiu_em: datetime) -> None:
        self._conexao.execute(
            "UPDATE matricula SET saiu_em = ? WHERE id = ?", (saiu_em.isoformat(), matricula_id)
        )

    def mensalidades(self, matricula_id: int) -> list[Mensalidade]:
        linhas = self._conexao.execute(
            "SELECT vencimento, valor_em_centavos, paga_em FROM mensalidade "
            "WHERE matricula_id = ? ORDER BY vencimento",
            (matricula_id,),
        ).fetchall()
        return [
            Mensalidade(date.fromisoformat(vencimento), valor, datetime.fromisoformat(paga_em))
            for vencimento, valor, paga_em in linhas
        ]

    def lista_de_espera(self, turma_id: int) -> ListaDeEspera:
        linhas = self._conexao.execute(
            "SELECT aluno_id, entrou_em, prazo FROM lista_de_espera WHERE turma_id = ? "
            "ORDER BY entrou_em, rowid",
            (turma_id,),
        ).fetchall()
        return tuple(
            NaLista(
                aluno_id,
                datetime.fromisoformat(entrou_em),
                None if prazo is None else datetime.fromisoformat(prazo),
            )
            for aluno_id, entrou_em, prazo in linhas
        )

    def salvar_lista_de_espera(self, turma_id: int, lista: ListaDeEspera) -> None:
        self._conexao.execute("DELETE FROM lista_de_espera WHERE turma_id = ?", (turma_id,))
        self._conexao.executemany(
            "INSERT INTO lista_de_espera (turma_id, aluno_id, entrou_em, prazo) "
            "VALUES (?, ?, ?, ?)",
            [
                (
                    turma_id,
                    na_lista.aluno_id,
                    na_lista.entrou_em.isoformat(),
                    None if na_lista.prazo is None else na_lista.prazo.isoformat(),
                )
                for na_lista in lista
            ],
        )

    def turmas_com_o_aluno_na_lista(self, aluno_id: int) -> list[int]:
        linhas = self._conexao.execute(
            "SELECT turma_id FROM lista_de_espera WHERE aluno_id = ? ORDER BY turma_id",
            (aluno_id,),
        ).fetchall()
        return [turma_id for (turma_id,) in linhas]

    def marcar_nao_realizada(
        self, turma_id: int, nivel: int, data: date, marcada_em: datetime
    ) -> None:
        self._conexao.execute(
            "INSERT INTO aula_nao_realizada (turma_id, nivel, data, marcada_em) "
            "VALUES (?, ?, ?, ?)",
            (turma_id, nivel, data.isoformat(), marcada_em.isoformat()),
        )

    def lancar_presenca(
        self,
        turma_id: int,
        nivel: int,
        data_da_aula: date,
        presencas: Sequence[Presenca],
        lancada_em: datetime,
        lancada_por: int,
    ) -> None:
        self._conexao.execute(
            "INSERT INTO lancamento_de_presenca "
            "(turma_id, nivel, data_da_aula, lancada_em, lancada_por) VALUES (?, ?, ?, ?, ?)",
            (turma_id, nivel, data_da_aula.isoformat(), lancada_em.isoformat(), lancada_por),
        )
        self._conexao.executemany(
            "INSERT INTO presenca (turma_id, nivel, data_da_aula, aluno_id, presente) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (turma_id, nivel, p.data_da_aula.isoformat(), p.aluno_id, p.presente)
                for p in presencas
            ],
        )

    def datas_com_presenca(self, turma_id: int, nivel: int) -> set[date]:
        linhas = self._conexao.execute(
            "SELECT data_da_aula FROM lancamento_de_presenca WHERE turma_id = ? AND nivel = ?",
            (turma_id, nivel),
        ).fetchall()
        return {date.fromisoformat(data) for (data,) in linhas}

    def presencas(self, turma_id: int, nivel: int) -> list[Presenca]:
        linhas = self._conexao.execute(
            "SELECT aluno_id, data_da_aula, presente FROM presenca "
            "WHERE turma_id = ? AND nivel = ? ORDER BY data_da_aula, aluno_id",
            (turma_id, nivel),
        ).fetchall()
        return [
            Presenca(aluno_id, date.fromisoformat(data), bool(presente))
            for aluno_id, data, presente in linhas
        ]

    def _nao_realizadas(self, turma_id: int, nivel: int) -> frozenset[date]:
        linhas = self._conexao.execute(
            "SELECT data FROM aula_nao_realizada WHERE turma_id = ? AND nivel = ?",
            (turma_id, nivel),
        ).fetchall()
        return frozenset(date.fromisoformat(data) for (data,) in linhas)

    def _matriculas(
        self, turma_id: int | None = None, aluno_id: int | None = None
    ) -> list[Matricula]:
        linhas = self._conexao.execute(
            _MATRICULAS_ATIVAS, {"turma_id": turma_id, "aluno_id": aluno_id}
        ).fetchall()
        return [
            Matricula(matricula_id, id_da_turma, id_do_aluno, datetime.fromisoformat(em))
            for matricula_id, id_da_turma, id_do_aluno, em in linhas
        ]

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
            self._nao_realizadas(turma_id, nivel),
        )
