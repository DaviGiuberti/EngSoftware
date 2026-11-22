"""Compras de pacote no SQLite, na tabela compra da migração 0014, com o reembolso da 0016 (RNF08:
só SQL com "?")."""

import sqlite3
from datetime import datetime

from plataforma.modules.vendas.domain.compra import Compra, CompraNova


def _data_e_hora(texto: str | None) -> datetime | None:
    return None if texto is None else datetime.fromisoformat(texto)


class RepositorioDeComprasSqlite:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self._conexao = conexao

    def adicionar(self, compra: CompraNova) -> Compra:
        (compra_id,) = self._conexao.execute(
            "INSERT INTO compra (aluno_id, pacote_id, valor_em_centavos, comprada_em, "
            "com_direito_a_reembolso) VALUES (?, ?, ?, ?, ?) RETURNING id",
            (
                compra.aluno_id,
                compra.pacote_id,
                compra.valor_em_centavos,
                compra.comprada_em.isoformat(),
                compra.com_direito_a_reembolso,
            ),
        ).fetchone()
        return Compra(
            compra_id,
            compra.aluno_id,
            compra.pacote_id,
            compra.valor_em_centavos,
            compra.comprada_em,
            compra.com_direito_a_reembolso,
        )

    def do_aluno(self, aluno_id: int) -> list[Compra]:
        linhas = self._conexao.execute(
            "SELECT id, aluno_id, pacote_id, valor_em_centavos, comprada_em, "
            "com_direito_a_reembolso, reembolsada_em FROM compra "
            "WHERE aluno_id = ? ORDER BY comprada_em, id",
            (aluno_id,),
        )
        return [
            Compra(
                id=compra_id,
                aluno_id=aluno,
                pacote_id=pacote_id,
                valor_em_centavos=valor,
                comprada_em=datetime.fromisoformat(comprada_em),
                com_direito_a_reembolso=bool(com_direito),
                reembolsada_em=_data_e_hora(reembolsada_em),
            )
            for compra_id, aluno, pacote_id, valor, comprada_em, com_direito, reembolsada_em in (
                linhas
            )
        ]

    def reembolsar(self, compra_id: int, reembolsada_em: datetime) -> None:
        self._conexao.execute(
            "UPDATE compra SET reembolsada_em = ? WHERE id = ?",
            (reembolsada_em.isoformat(), compra_id),
        )
