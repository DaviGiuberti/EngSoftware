"""Portas do módulo materias: o que os casos de uso pedem à infraestrutura."""

from typing import Protocol

from plataforma.modules.materias.domain.materia import Materia, MateriaNova


class RepositorioDeMaterias(Protocol):
    def adicionar(self, materia: MateriaNova) -> Materia: ...

    def buscar(self, materia_id: int) -> Materia | None: ...

    def listar(self) -> list[Materia]:
        """Todas as matérias, em ordem alfabética."""
        ...
