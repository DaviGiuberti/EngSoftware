"""Porta de transação dos casos de uso (RNF05)."""

from collections.abc import Callable
from contextlib import AbstractContextManager

# Abre uma transação: o bloco `with transacao(): ...` grava tudo no fim ou nada, se falhar.
type Transacao = Callable[[], AbstractContextManager[None]]
