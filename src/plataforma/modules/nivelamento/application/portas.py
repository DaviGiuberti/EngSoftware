"""Portas do nivelamento: o que os casos de uso pedem à infraestrutura."""

from typing import Protocol

from plataforma.modules.nivelamento.domain.questao import Questao, QuestaoNova


class RepositorioDeQuestoes(Protocol):
    def adicionar(self, materia_id: int, questao: QuestaoNova) -> Questao: ...

    def listar(self, materia_id: int) -> list[Questao]:
        """As questões da matéria, na ordem em que foram cadastradas."""
        ...
