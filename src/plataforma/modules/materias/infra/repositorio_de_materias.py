"""Matérias no SQLite, nas tabelas materia e faixa da migração 0003 (RNF08: só SQL com "?")."""

import sqlite3
from collections import defaultdict

from plataforma.modules.materias.domain.materia import Faixa, Materia, MateriaNova

# Com materia_id NULL, a consulta traz todas as matérias; com um id, só aquela.
_MATERIAS_COM_FAIXAS = (
    "SELECT m.id, m.nome, m.mensalidade_em_centavos, f.nivel, f.nota_minima, f.nota_maxima "
    "FROM materia m JOIN faixa f ON f.materia_id = m.id "
    "WHERE :materia_id IS NULL OR m.id = :materia_id "
    "ORDER BY m.nome COLLATE NOCASE, m.id, f.nivel"
)


class RepositorioDeMateriasSqlite:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self._conexao = conexao

    def adicionar(self, materia: MateriaNova) -> Materia:
        (materia_id,) = self._conexao.execute(
            "INSERT INTO materia (nome, mensalidade_em_centavos) VALUES (?, ?) RETURNING id",
            (materia.nome, materia.mensalidade_em_centavos),
        ).fetchone()
        self._conexao.executemany(
            "INSERT INTO faixa (materia_id, nivel, nota_minima, nota_maxima) VALUES (?, ?, ?, ?)",
            [(materia_id, f.nivel, f.nota_minima, f.nota_maxima) for f in materia.faixas],
        )
        return Materia(materia_id, materia.nome, materia.faixas, materia.mensalidade_em_centavos)

    def buscar(self, materia_id: int) -> Materia | None:
        return next(iter(self._ler(materia_id)), None)

    def listar(self) -> list[Materia]:
        return self._ler(None)

    def _ler(self, materia_id: int | None) -> list[Materia]:
        linhas = self._conexao.execute(
            _MATERIAS_COM_FAIXAS, {"materia_id": materia_id}
        ).fetchall()
        dados: dict[int, tuple[str, int]] = {}
        faixas: defaultdict[int, list[Faixa]] = defaultdict(list)
        for id_materia, nome, mensalidade, nivel, nota_minima, nota_maxima in linhas:
            dados[id_materia] = (nome, mensalidade)
            faixas[id_materia].append(Faixa(nivel, nota_minima, nota_maxima))
        return [
            Materia(id_materia, nome, tuple(faixas[id_materia]), mensalidade)
            for id_materia, (nome, mensalidade) in dados.items()
        ]
