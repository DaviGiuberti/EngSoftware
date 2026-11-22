"""Portas do nivelamento: o que os casos de uso pedem à infraestrutura."""

from datetime import datetime
from typing import Protocol

from plataforma.modules.nivelamento.domain.nivelamento import (
    Nivelamento,
    NivelamentoNoHistorico,
    NivelDoAluno,
)
from plataforma.modules.nivelamento.domain.promocao import Promocao, PromocaoDoAluno
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

    def adicionar_promocao(self, aluno_id: int, promocao: Promocao) -> None: ...

    def promocoes(self, aluno_id: int) -> list[Promocao]:
        """As promoções do aluno, da mais antiga à mais nova."""
        ...

    def concluir_trilha(self, aluno_id: int, materia_id: int, em: datetime) -> None:
        """Guarda a trilha concluída (R09). Se o aluno já a concluiu antes, nada muda."""
        ...

    def concluidos_de_todos(self) -> list[NivelamentoNoHistorico]:
        """Os nivelamentos concluídos de todos os alunos, também os refeitos, em ordem de data."""
        ...

    def promocoes_de_todos(self) -> list[PromocaoDoAluno]:
        """As promoções de todos os alunos, em ordem de data."""
        ...

    def trilhas_concluidas(self, aluno_id: int) -> dict[int, datetime]:
        """Quando o aluno concluiu a trilha, pelo id de cada matéria em que a concluiu."""
        ...
