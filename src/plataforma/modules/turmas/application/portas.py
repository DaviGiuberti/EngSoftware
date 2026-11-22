"""Portas das turmas: o que os casos de uso pedem à infraestrutura."""

from collections.abc import Sequence
from datetime import date, datetime
from typing import Protocol

from plataforma.modules.turmas.domain.etapa import Etapa
from plataforma.modules.turmas.domain.lista_de_espera import ListaDeEspera
from plataforma.modules.turmas.domain.matricula import Matricula
from plataforma.modules.turmas.domain.mensalidade import Mensalidade
from plataforma.modules.turmas.domain.presenca import Presenca
from plataforma.modules.turmas.domain.prova_final import Nota, ProvaFinal, ResultadoEtapa
from plataforma.modules.turmas.domain.turma import MudancaDaTurma, Turma, TurmaNova


class RepositorioDeTurmas(Protocol):
    """A turma com o que é dela: as etapas, as matrículas, as mensalidades pagas, a lista de
    espera, as aulas não realizadas, as presenças e as provas finais.

    A turma lida vem na etapa atual, a do maior nível por que passou, com as datas das aulas não
    realizadas dela (R18), e com a data do encerramento, se encerrou (R09).
    """

    def adicionar(self, turma: TurmaNova) -> Turma:
        """Grava a turma com a 1ª etapa, no nível inicial (R24)."""
        ...

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

    def aplicar_mudanca(self, turma_id: int, mudanca: MudancaDaTurma) -> None:
        """Grava a passagem para a etapa seguinte (R04) ou o encerramento da turma (R09)."""
        ...

    def etapas(self, turma_id: int) -> list[Etapa]:
        """As etapas da turma, da primeira à atual, com as aulas não realizadas de cada uma."""
        ...

    def adicionar_matricula(
        self, turma_id: int, aluno_id: int, matriculada_em: datetime, primeira: Mensalidade
    ) -> Matricula:
        """Grava a matrícula com a primeira mensalidade, que é paga nela (R27)."""
        ...

    def matriculas_da_turma(self, turma_id: int) -> list[Matricula]:
        """As matrículas ativas da turma, na ordem em que foram feitas."""
        ...

    def todas_as_matriculas(self, turma_id: int) -> list[Matricula]:
        """As matrículas da turma, também as de quem já saiu, na ordem em que foram feitas."""
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

    def corrigir_presenca(
        self,
        turma_id: int,
        nivel: int,
        data_da_aula: date,
        presencas: Sequence[Presenca],
        corrigida_em: datetime,
        corrigida_por: int,
    ) -> None:
        """Troca a presença dos alunos da aula. Quando ela foi lançada não muda (R22)."""
        ...

    def datas_com_presenca(self, turma_id: int, nivel: int) -> set[date]:
        """As datas das aulas da etapa com a presença lançada."""
        ...

    def lancamentos_de_presenca(self, turma_id: int, nivel: int) -> dict[date, datetime]:
        """Quando foi lançada a presença de cada aula da etapa, pela data da aula."""
        ...

    def presencas(self, turma_id: int, nivel: int) -> list[Presenca]:
        """As presenças lançadas na etapa, em ordem de data."""
        ...

    def provas_finais(self, turma_id: int, nivel: int) -> list[ProvaFinal]:
        """As notas lançadas na prova final da etapa, na ordem dos alunos."""
        ...

    def lancar_prova_final(
        self, turma_id: int, nivel: int, prova: ProvaFinal, lancada_por: int
    ) -> None: ...

    def corrigir_prova_final(
        self,
        turma_id: int,
        nivel: int,
        aluno_id: int,
        nota: Nota,
        corrigida_em: datetime,
        corrigida_por: int,
    ) -> None:
        """Troca a nota. Quando ela foi lançada, que conta o prazo de correção, não muda (R22)."""
        ...

    def aplicar_resultado(
        self, turma_id: int, nivel: int, aluno_id: int, resultado: ResultadoEtapa
    ) -> None:
        """Guarda o resultado da etapa que passou a valer, com a promoção ou a saída feitas."""
        ...
