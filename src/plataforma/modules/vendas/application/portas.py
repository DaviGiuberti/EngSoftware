"""Portas das vendas: o que os casos de uso pedem à infraestrutura."""

from datetime import datetime
from typing import Protocol

from plataforma.modules.vendas.domain.compra import Compra, CompraNova


class RepositorioDeCompras(Protocol):
    def adicionar(self, compra: CompraNova) -> Compra: ...

    def do_aluno(self, aluno_id: int) -> list[Compra]:
        """As compras do aluno, de todos os pacotes, na ordem em que foram feitas."""
        ...

    def reembolsar(self, compra_id: int, reembolsada_em: datetime) -> None:
        """Grava o reembolso aceito (R13). Ele é simulado (ADR 0003)."""
        ...
