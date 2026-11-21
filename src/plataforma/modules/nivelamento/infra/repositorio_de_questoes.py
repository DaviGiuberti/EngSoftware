"""Questões no SQLite, nas tabelas questao e alternativa da migração 0004 (RNF08: SQL com "?")."""

import sqlite3
from collections import defaultdict

from plataforma.modules.nivelamento.domain.questao import Alternativa, Questao, QuestaoNova


class RepositorioDeQuestoesSqlite:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self._conexao = conexao

    def adicionar(self, materia_id: int, questao: QuestaoNova) -> Questao:
        (questao_id,) = self._conexao.execute(
            "INSERT INTO questao (materia_id, enunciado) VALUES (?, ?) RETURNING id",
            (materia_id, questao.enunciado),
        ).fetchone()
        self._conexao.executemany(
            "INSERT INTO alternativa (questao_id, posicao, texto, correta) VALUES (?, ?, ?, ?)",
            [
                (questao_id, posicao, alternativa.texto, alternativa.correta)
                for posicao, alternativa in enumerate(questao.alternativas)
            ],
        )
        return Questao(questao_id, materia_id, questao.enunciado, questao.alternativas)

    def listar(self, materia_id: int) -> list[Questao]:
        linhas = self._conexao.execute(
            "SELECT q.id, q.enunciado, a.texto, a.correta "
            "FROM questao q JOIN alternativa a ON a.questao_id = q.id "
            "WHERE q.materia_id = ? ORDER BY q.id, a.posicao",
            (materia_id,),
        ).fetchall()
        enunciados: dict[int, str] = {}
        alternativas: defaultdict[int, list[Alternativa]] = defaultdict(list)
        for questao_id, enunciado, texto, correta in linhas:
            enunciados[questao_id] = enunciado
            alternativas[questao_id].append(Alternativa(texto, bool(correta)))
        return [
            Questao(questao_id, materia_id, enunciado, tuple(alternativas[questao_id]))
            for questao_id, enunciado in enunciados.items()
        ]
