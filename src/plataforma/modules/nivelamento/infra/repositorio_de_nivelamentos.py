"""Nivelamentos, respostas e níveis dos alunos no SQLite, nas tabelas da migração 0005, e as
promoções e trilhas concluídas da 0011.

Todo SQL usa parâmetros "?" (RNF08). As datas vão como texto ISO 8601, com o fuso.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Any

from plataforma.modules.nivelamento.domain.nivelamento import (
    Conclusao,
    Nivelamento,
    NivelDoAluno,
    TempoDoNivelamento,
)
from plataforma.modules.nivelamento.domain.promocao import Promocao

_POR_ID = (
    "SELECT id, aluno_id, materia_id, tempo_usado_em_segundos, tempo_extra_em_segundos, "
    "aberto_desde, concluido_em, nota, nivel FROM nivelamento WHERE id = ?"
)
_EM_ANDAMENTO = (
    "SELECT id, aluno_id, materia_id, tempo_usado_em_segundos, tempo_extra_em_segundos, "
    "aberto_desde, concluido_em, nota, nivel FROM nivelamento "
    "WHERE aluno_id = ? AND materia_id = ? AND concluido_em IS NULL"
)


def _data(texto: str | None) -> datetime | None:
    return None if texto is None else datetime.fromisoformat(texto)


def _texto(data: datetime | None) -> str | None:
    return None if data is None else data.isoformat()


class RepositorioDeNivelamentosSqlite:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self._conexao = conexao

    def criar(self, aluno_id: int, materia_id: int, agora: datetime) -> Nivelamento:
        (nivelamento_id,) = self._conexao.execute(
            "INSERT INTO nivelamento (aluno_id, materia_id, iniciado_em) VALUES (?, ?, ?) "
            "RETURNING id",
            (aluno_id, materia_id, agora.isoformat()),
        ).fetchone()
        return Nivelamento(nivelamento_id, aluno_id, materia_id, TempoDoNivelamento(timedelta(0)))

    def buscar(self, nivelamento_id: int) -> Nivelamento | None:
        return self._montar(self._conexao.execute(_POR_ID, (nivelamento_id,)).fetchone())

    def buscar_em_andamento(self, aluno_id: int, materia_id: int) -> Nivelamento | None:
        linha = self._conexao.execute(_EM_ANDAMENTO, (aluno_id, materia_id)).fetchone()
        return self._montar(linha)

    def salvar(self, nivelamento: Nivelamento) -> None:
        tempo, conclusao = nivelamento.tempo, nivelamento.conclusao
        self._conexao.execute(
            "UPDATE nivelamento SET tempo_usado_em_segundos = ?, tempo_extra_em_segundos = ?, "
            "aberto_desde = ?, concluido_em = ?, nota = ?, nivel = ? WHERE id = ?",
            (
                tempo.usado.total_seconds(),
                tempo.extra.total_seconds(),
                _texto(tempo.aberto_desde),
                _texto(conclusao.em) if conclusao else None,
                conclusao.nota if conclusao else None,
                conclusao.nivel if conclusao else None,
                nivelamento.id,
            ),
        )
        self._conexao.executemany(
            "INSERT INTO resposta (nivelamento_id, questao_id, posicao) VALUES (?, ?, ?) "
            "ON CONFLICT (nivelamento_id, questao_id) DO UPDATE SET posicao = excluded.posicao",
            [
                (nivelamento.id, questao_id, posicao)
                for questao_id, posicao in nivelamento.respostas.items()
            ],
        )

    def materias_em_andamento(self, aluno_id: int) -> set[int]:
        linhas = self._conexao.execute(
            "SELECT materia_id FROM nivelamento WHERE aluno_id = ? AND concluido_em IS NULL",
            (aluno_id,),
        )
        return {materia_id for (materia_id,) in linhas}

    def nivel_do_aluno(self, aluno_id: int, materia_id: int) -> NivelDoAluno | None:
        linha = self._conexao.execute(
            "SELECT materia_id, nivel, refazer_liberado FROM nivel_do_aluno "
            "WHERE aluno_id = ? AND materia_id = ?",
            (aluno_id, materia_id),
        ).fetchone()
        return None if linha is None else NivelDoAluno(linha[0], linha[1], bool(linha[2]))

    def niveis_do_aluno(self, aluno_id: int) -> list[NivelDoAluno]:
        linhas = self._conexao.execute(
            "SELECT materia_id, nivel, refazer_liberado FROM nivel_do_aluno WHERE aluno_id = ? "
            "ORDER BY materia_id",
            (aluno_id,),
        )
        return [NivelDoAluno(materia, nivel, bool(liberado)) for materia, nivel, liberado in linhas]

    def salvar_nivel(self, aluno_id: int, nivel: NivelDoAluno) -> None:
        self._conexao.execute(
            "INSERT INTO nivel_do_aluno (aluno_id, materia_id, nivel, refazer_liberado) "
            "VALUES (?, ?, ?, ?) ON CONFLICT (aluno_id, materia_id) DO UPDATE SET "
            "nivel = excluded.nivel, refazer_liberado = excluded.refazer_liberado",
            (aluno_id, nivel.materia_id, nivel.nivel, nivel.refazer_liberado),
        )

    def adicionar_promocao(self, aluno_id: int, promocao: Promocao) -> None:
        self._conexao.execute(
            "INSERT INTO promocao (aluno_id, materia_id, nivel_anterior, nivel_novo, "
            "promovido_em) VALUES (?, ?, ?, ?, ?)",
            (
                aluno_id,
                promocao.materia_id,
                promocao.nivel_anterior,
                promocao.nivel_novo,
                promocao.em.isoformat(),
            ),
        )

    def promocoes(self, aluno_id: int) -> list[Promocao]:
        linhas = self._conexao.execute(
            "SELECT materia_id, nivel_anterior, nivel_novo, promovido_em FROM promocao "
            "WHERE aluno_id = ? ORDER BY promovido_em, materia_id",
            (aluno_id,),
        )
        return [
            Promocao(materia_id, anterior, novo, datetime.fromisoformat(em))
            for materia_id, anterior, novo, em in linhas
        ]

    def concluir_trilha(self, aluno_id: int, materia_id: int, em: datetime) -> None:
        self._conexao.execute(
            "INSERT INTO trilha_concluida (aluno_id, materia_id, concluida_em) VALUES (?, ?, ?) "
            "ON CONFLICT (aluno_id, materia_id) DO NOTHING",
            (aluno_id, materia_id, em.isoformat()),
        )

    def trilhas_concluidas(self, aluno_id: int) -> set[int]:
        linhas = self._conexao.execute(
            "SELECT materia_id FROM trilha_concluida WHERE aluno_id = ?", (aluno_id,)
        )
        return {materia_id for (materia_id,) in linhas}

    def _montar(self, linha: tuple[Any, ...] | None) -> Nivelamento | None:
        if linha is None:
            return None
        nivelamento_id, aluno_id, materia_id, usado, extra, aberto_desde, concluido_em = linha[:7]
        nota, nivel = linha[7:]
        respostas = dict(
            self._conexao.execute(
                "SELECT questao_id, posicao FROM resposta WHERE nivelamento_id = ?",
                (nivelamento_id,),
            ).fetchall()
        )
        tempo = TempoDoNivelamento(
            usado=timedelta(seconds=usado),
            extra=timedelta(seconds=extra),
            aberto_desde=_data(aberto_desde),
        )
        conclusao = None
        if concluido_em is not None:
            conclusao = Conclusao(datetime.fromisoformat(concluido_em), nota, nivel)
        return Nivelamento(nivelamento_id, aluno_id, materia_id, tempo, respostas, conclusao)
