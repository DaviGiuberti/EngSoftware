"""Porta do relógio. Os casos de uso pedem a hora por ela, e o domínio a recebe como parâmetro."""

from datetime import datetime
from typing import Protocol


class Relogio(Protocol):
    def agora(self) -> datetime: ...
