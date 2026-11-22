"""Consulta pública das presenças das turmas, para as métricas (ADR 0002)."""

from plataforma.modules.turmas.application.portas import RepositorioDeTurmas
from plataforma.modules.turmas.domain.presenca import PresencaNaMateria


class ConsultaDePresencas:
    """As métricas leem as presenças sem ler as tabelas das turmas."""

    def __init__(self, turmas: RepositorioDeTurmas) -> None:
        self._turmas = turmas

    def presentes(self) -> list[PresencaNaMateria]:
        """As presenças de todos os alunos, sem as faltas, com a matéria e o nível (R64)."""
        return self._turmas.presentes_de_todos()
