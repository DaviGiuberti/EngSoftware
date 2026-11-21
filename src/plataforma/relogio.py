"""Relógio do sistema, no horário de Brasília. Só a montagem do app (main.py) o conhece."""

from datetime import datetime

from plataforma.compartilhado.horario import BRASILIA


class RelogioDoSistema:
    def agora(self) -> datetime:
        return datetime.now(BRASILIA)
