"""Compras de pacote no SQLite, na tabela compra da migração 0014 (RNF08: só SQL com "?")."""

import sqlite3
from datetime import datetime

from plataforma.modules.vendas.domain.compra import Compra, CompraNova


class RepositorioDeComprasSqlite:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self._conexao = conexao

    def adicionar(self, compra: CompraNova) -> Compra:
        (compra_id,) = self._conexao.execute(
            "INSERT INTO compra (aluno_id, pacote_id, valor_em_centavos, comprada_em) "
            "VALUES (?, ?, ?, ?) RETURNING id",
            (
                compra.aluno_id,
                compra.pacote_id,
                compra.valor_em_centavos,
                compra.comprada_em.isoformat(),
            ),
        ).fetchone()
        return Compra(
            compra_id,
            compra.aluno_id,
            compra.pacote_id,
            compra.valor_em_centavos,
            compra.comprada_em,
        )

    def do_aluno(self, aluno_id: int) -> list[Compra]:
        linhas = self._conexao.execute(
            "SELECT id, aluno_id, pacote_id, valor_em_centavos, comprada_em FROM compra "
            "WHERE aluno_id = ? ORDER BY comprada_em, id",
            (aluno_id,),
        )
        return [
            Compra(compra_id, aluno, pacote_id, valor, datetime.fromisoformat(comprada_em))
            for compra_id, aluno, pacote_id, valor, comprada_em in linhas
        ]
