"""Matrícula (H04, H05, H06, H13, H07): só na turma do nível do aluno (R06), sem conflito de
horário (R07), até antes da 13ª aula da etapa (R19), uma turma por matéria (R44) e com vaga livre
(R04, R05). Quem perde a vaga por atraso vê um aviso até entrar em outra turma da matéria (R55)."""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.materias.domain.materia import nome_do_nivel
from plataforma.modules.turmas.domain.horario import (
    Horario,
    descrever_horario,
    horario_em_conflito,
)
from plataforma.modules.turmas.domain.turma import VAGAS_POR_TURMA, ConflitoDeHorario

# R19: dá para entrar até antes da 13ª aula, para fazer no mínimo 12 aulas da etapa.
AULA_QUE_FECHA_A_MATRICULA = 13


class SemNivelNaMateria(Recusa):
    """R06: a mensagem diz qual nivelamento fazer."""


class NivelDiferenteDaTurma(Recusa):
    """R06: a mensagem diz o nível da turma e o do aluno."""


class JaTemTurmaNaMateria(Recusa):
    """R44: a mensagem diz a matéria."""


class MatriculaFechada(Recusa):
    mensagem = (
        "A matrícula nesta turma fechou: só dá para entrar até antes da 13ª aula da etapa."
    )


class TurmaCheia(Recusa):
    """R04 e R05: a mensagem oferece a lista de espera."""


class SemMatricula(Recusa):
    mensagem = "Você não tem matrícula nesta turma."


class MotivoDaSaida(StrEnum):
    """Por que a matrícula terminou."""

    VONTADE = "vontade"  # R29: o aluno saiu da turma
    REPROVACAO = "reprovacao"  # R21: o resultado da etapa valeu, reprovado
    CONCLUSAO = "conclusao"  # R09: aprovado na etapa do nível máximo, na turma que encerrou
    ATRASO = "atraso"  # R28: a mensalidade não foi paga até o fim da tolerância


@dataclass(frozen=True)
class Matricula:
    """O aluno na turma desde matriculada_em. A aula de entrada sai das aulas dadas até ali.

    saiu_em é quando o aluno saiu da turma, e saiu_por, o motivo.
    """

    id: int
    turma_id: int
    aluno_id: int
    matriculada_em: datetime
    saiu_em: datetime | None = None
    saiu_por: MotivoDaSaida | None = None


class SituacaoNaTurma(StrEnum):
    """O que o aluno pode fazer numa turma do nível dele."""

    MATRICULADO = "matriculado"
    VAGA_OFERECIDA = "vaga_oferecida"
    NA_LISTA = "na_lista"
    COM_VAGA = "com_vaga"
    CHEIA = "cheia"


def exigir_nivel_da_turma(
    nivel_do_aluno: int | None, nivel_da_turma: int, nome_da_materia: str
) -> None:
    """R06: o aluno só entra em turma do nível dele na matéria."""
    if nivel_do_aluno is None:
        raise SemNivelNaMateria(
            f"Faça o nivelamento de {nome_da_materia} antes de entrar numa turma dela."
        )
    if nivel_do_aluno != nivel_da_turma:
        raise NivelDiferenteDaTurma(
            f"Esta turma é do {nome_do_nivel(nivel_da_turma)} de {nome_da_materia}, e você está "
            f"no {nome_do_nivel(nivel_do_aluno)}."
        )


def exigir_sem_turma_na_materia(tem_turma_na_materia: bool, nome_da_materia: str) -> None:
    """R44: o aluno tem no máximo uma turma em cada matéria."""
    if tem_turma_na_materia:
        raise JaTemTurmaNaMateria(f"Você já está numa turma de {nome_da_materia}.")


def exigir_aluno_livre(horario: Horario, horarios_do_aluno: Iterable[Horario]) -> None:
    """R07: o aluno não tem duas turmas com horários que se sobrepõem."""
    conflito = horario_em_conflito(horario, horarios_do_aluno)
    if conflito is not None:
        raise ConflitoDeHorario(
            f"Conflito de horário: você já tem uma turma às {descrever_horario(conflito)}."
        )


def matricula_aberta(aulas_dadas: int) -> bool:
    """R19: a turma recebe alunos até antes da 13ª aula da etapa."""
    return aulas_dadas < AULA_QUE_FECHA_A_MATRICULA


def exigir_matricula_aberta(aulas_dadas: int) -> None:
    if not matricula_aberta(aulas_dadas):
        raise MatriculaFechada()


def aula_de_entrada(aulas_dadas: int) -> int:
    """R08: as faltas do aluno contam a partir da aula seguinte às que a turma já deu."""
    return aulas_dadas + 1


def vagas_livres(matriculados: int, reservadas: int) -> int:
    """R04 e R05: das 12 vagas, saem as dos matriculados e as reservadas para a lista."""
    return VAGAS_POR_TURMA - matriculados - reservadas


def exigir_vaga(matriculados: int, reservadas: int) -> None:
    """R04: sem vaga, a matrícula é recusada e a lista de espera, oferecida.

    R05: a vaga oferecida a quem está na lista fica reservada durante o prazo.
    """
    if vagas_livres(matriculados, reservadas) > 0:
        return
    if reservadas > 0:
        raise TurmaCheia(
            "A vaga desta turma está reservada para a lista de espera. Você pode entrar na lista."
        )
    raise TurmaCheia("Turma cheia: você pode entrar na lista de espera.")


def situacao_na_turma(
    matriculado: bool, na_lista: bool, com_oferta: bool, vagas_livres: int
) -> SituacaoNaTurma:
    if matriculado:
        return SituacaoNaTurma.MATRICULADO
    if com_oferta:
        return SituacaoNaTurma.VAGA_OFERECIDA
    if na_lista:
        return SituacaoNaTurma.NA_LISTA
    if vagas_livres > 0:
        return SituacaoNaTurma.COM_VAGA
    return SituacaoNaTurma.CHEIA


def vagas_perdidas(
    matriculas: Sequence[Matricula], materia_da_turma: Mapping[int, int]
) -> list[Matricula]:
    """R55: as matrículas que o aluno perdeu por atraso da mensalidade e cujo aviso ele ainda vê,
    porque não entrou depois em outra turma da mesma matéria.

    materia_da_turma leva o id de cada turma das matrículas ao id da matéria dela.
    """
    return [
        perdida
        for perdida in matriculas
        if perdida.saiu_por == MotivoDaSaida.ATRASO
        and perdida.saiu_em is not None
        and not any(
            materia_da_turma[outra.turma_id] == materia_da_turma[perdida.turma_id]
            and outra.matriculada_em >= perdida.saiu_em
            for outra in matriculas
        )
    ]
