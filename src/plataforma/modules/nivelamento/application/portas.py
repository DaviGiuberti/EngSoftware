"""Portas do nivelamento: o que os casos de uso pedem à infraestrutura."""

from datetime import datetime
from typing import Protocol

from plataforma.modules.nivelamento.domain.nivelamento import Nivelamento, NivelDoAluno
from plataforma.modules.nivelamento.domain.questao import Questao, QuestaoNova


class RepositorioDeQuestoes(Protocol):
    def adicionar(self, materia_id: int, questao: QuestaoNova) -> Questao: ...

    def listar(self, materia_id: int) -> list[Questao]:
        """As questões da matéria, na ordem em que foram cadastradas."""
        ...

    def contar_por_materia(self) -> dict[int, int]:
        """Quantas questões cada matéria tem. Matéria sem questões fica de fora."""
        ...


class RepositorioDeNivelamentos(Protocol):
    def criar(self, aluno_id: int, materia_id: int, agora: datetime) -> Nivelamento: ...

    def buscar(self, nivelamento_id: int) -> Nivelamento | None: ...

    def buscar_em_andamento(self, aluno_id: int, materia_id: int) -> Nivelamento | None: ...

    def salvar(self, nivelamento: Nivelamento) -> None:
        """Grava o tempo, as respostas e a conclusão do nivelamento."""
        ...

    def materias_em_andamento(self, aluno_id: int) -> set[int]: ...

    def nivel_do_aluno(self, aluno_id: int, materia_id: int) -> NivelDoAluno | None: ...

    def niveis_do_aluno(self, aluno_id: int) -> list[NivelDoAluno]: ...

    def salvar_nivel(self, aluno_id: int, nivel: NivelDoAluno) -> None: ...
