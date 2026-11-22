"""Portas das turmas: o que os casos de uso pedem à infraestrutura."""

from datetime import datetime
from typing import Protocol

from plataforma.modules.turmas.domain.lista_de_espera import ListaDeEspera
from plataforma.modules.turmas.domain.matricula import Matricula
from plataforma.modules.turmas.domain.mensalidade import Mensalidade
from plataforma.modules.turmas.domain.turma import Turma, TurmaNova


class RepositorioDeTurmas(Protocol):
    """A turma com o que é dela: as matrículas, as mensalidades pagas e a lista de espera."""

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

    def adicionar_matricula(
        self, turma_id: int, aluno_id: int, matriculada_em: datetime, primeira: Mensalidade
    ) -> Matricula:
        """Grava a matrícula com a primeira mensalidade, que é paga nela (R27)."""
        ...

    def matriculas_da_turma(self, turma_id: int) -> list[Matricula]:
        """As matrículas ativas da turma, na ordem em que foram feitas."""
        ...

    def matriculas_do_aluno(self, aluno_id: int) -> list[Matricula]:
        """As matrículas ativas do aluno, na ordem em que foram feitas."""
        ...

    def encerrar_matricula(self, matricula_id: int, saiu_em: datetime) -> None: ...

    def mensalidades(self, matricula_id: int) -> list[Mensalidade]:
        """As mensalidades pagas da matrícula, da mais antiga à mais nova."""
        ...

    def lista_de_espera(self, turma_id: int) -> ListaDeEspera:
        """A lista de espera como foi gravada, sem aplicar os prazos vencidos."""
        ...

    def salvar_lista_de_espera(self, turma_id: int, lista: ListaDeEspera) -> None: ...

    def turmas_com_o_aluno_na_lista(self, aluno_id: int) -> list[int]:
        """O id das turmas em cuja lista de espera o aluno está."""
        ...
