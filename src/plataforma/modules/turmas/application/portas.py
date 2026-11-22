"""Portas das turmas: o que os casos de uso pedem à infraestrutura."""

from typing import Protocol

from plataforma.modules.turmas.domain.turma import Turma, TurmaNova


class RepositorioDeTurmas(Protocol):
    def adicionar(self, turma: TurmaNova) -> Turma: ...

    def buscar(self, turma_id: int) -> Turma | None: ...

    def listar(self) -> list[Turma]:
        """Todas as turmas, na ordem em que foram criadas."""
        ...

    def do_professor(self, professor_id: int) -> list[Turma]:
        """As turmas do professor, na ordem em que foram criadas."""
        ...

    def salvar(self, turma: Turma) -> None:
        """Grava o que pode mudar na turma: o professor (R26). O horário não muda (R24)."""
        ...
