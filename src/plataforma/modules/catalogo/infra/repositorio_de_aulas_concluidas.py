"""Aulas gravadas concluídas no SQLite, na tabela aula_concluida da migração 0015 (RNF08)."""

import sqlite3
from datetime import datetime

from plataforma.modules.catalogo.domain.aulas_do_aluno import AulaConcluida


class RepositorioDeAulasConcluidasSqlite:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self._conexao = conexao

    def do_aluno(self, aluno_id: int) -> list[AulaConcluida]:
        linhas = self._conexao.execute(
            "SELECT pacote_id, numero, concluida_em FROM aula_concluida WHERE aluno_id = ? "
            "ORDER BY concluida_em, pacote_id, numero",
            (aluno_id,),
        )
        return [
            AulaConcluida(pacote_id, numero, datetime.fromisoformat(concluida_em))
            for pacote_id, numero, concluida_em in linhas
        ]

    def adicionar(self, aluno_id: int, concluida: AulaConcluida) -> None:
        self._conexao.execute(
            "INSERT INTO aula_concluida (aluno_id, pacote_id, numero, concluida_em) "
            "VALUES (?, ?, ?, ?)",
            (aluno_id, concluida.pacote_id, concluida.numero, concluida.concluida_em.isoformat()),
        )

    def apagar(self, aluno_id: int, pacote_id: int) -> None:
        self._conexao.execute(
            "DELETE FROM aula_concluida WHERE aluno_id = ? AND pacote_id = ?",
            (aluno_id, pacote_id),
        )
