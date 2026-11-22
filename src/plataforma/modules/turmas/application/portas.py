"""Portas das turmas: o que os casos de uso pedem à infraestrutura."""

from collections.abc import Sequence
from datetime import date, datetime
from typing import Protocol

from plataforma.modules.turmas.domain.lista_de_espera import ListaDeEspera
from plataforma.modules.turmas.domain.matricula import Matricula
from plataforma.modules.turmas.domain.mensalidade import Mensalidade
from plataforma.modules.turmas.domain.presenca import Presenca
from plataforma.modules.turmas.domain.turma import Turma, TurmaNova


class RepositorioDeTurmas(Protocol):
    """A turma com o que é dela: as matrículas, as mensalidades pagas, a lista de espera, as
    aulas não realizadas e as presenças.

    A turma lida vem com as datas das aulas não realizadas da etapa atual (R18).
    """

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

    def marcar_nao_realizada(
        self, turma_id: int, nivel: int, data: date, marcada_em: datetime
    ) -> None: ...

    def lancar_presenca(
        self,
        turma_id: int,
        nivel: int,
        data_da_aula: date,
        presencas: Sequence[Presenca],
        lancada_em: datetime,
        lancada_por: int,
    ) -> None:
        """Grava a presença dos alunos numa aula da etapa e quando e por quem ela foi lançada."""
        ...

    def datas_com_presenca(self, turma_id: int, nivel: int) -> set[date]:
        """As datas das aulas da etapa com a presença lançada."""
        ...

    def presencas(self, turma_id: int, nivel: int) -> list[Presenca]:
        """As presenças lançadas na etapa, em ordem de data."""
        ...
