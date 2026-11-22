"""Turma (H30, H31): matéria, nível, professor, horário fixo e 12 vagas (R04, R24), professor sem
conflito de horário (R07) e troca de professor (R26)."""

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import date, datetime

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.materias.domain.materia import nome_do_nivel
from plataforma.modules.turmas.domain.etapa import (
    AulaDaEtapa,
    aulas_dadas,
    calendario,
    primeira_aula_depois,
)
from plataforma.modules.turmas.domain.horario import (
    Horario,
    descrever_horario,
    horario_em_conflito,
)

VAGAS_POR_TURMA = 12


class TurmaNaoEncontrada(Recusa):
    mensagem = "Turma não encontrada."


class NivelForaDaMateria(Recusa):
    """R24: a mensagem diz quais níveis a matéria tem."""


class ConflitoDeHorario(Recusa):
    """R07: a mensagem diz com que horário a turma se sobrepõe."""


class HorarioFixo(Recusa):
    """R24: a mensagem diz o horário que a turma continua tendo."""


class MesmoProfessor(Recusa):
    """A mensagem diz quem já dá aula na turma."""


@dataclass(frozen=True)
class TurmaNova:
    """Turma conferida e pronta para gravar, antes da 1ª aula da etapa."""

    materia_id: int
    nivel: int
    professor_id: int
    horario: Horario
    inicio_da_etapa: datetime


@dataclass(frozen=True)
class Turma:
    """inicio_da_etapa é o início da 1ª aula da etapa atual (R43), e nao_realizadas, as datas
    das aulas dela que não aconteceram (R18)."""

    id: int
    materia_id: int
    nivel: int
    professor_id: int
    horario: Horario
    inicio_da_etapa: datetime
    nao_realizadas: frozenset[date] = field(default_factory=frozenset)

    def calendario(self) -> list[AulaDaEtapa]:
        return calendario(self.horario, self.inicio_da_etapa, self.nao_realizadas)

    def aulas_dadas(self, agora: datetime) -> int:
        return aulas_dadas(self.horario, self.inicio_da_etapa, agora, self.nao_realizadas)


def nova_turma(
    materia_id: int, nivel: int, professor_id: int, horario: Horario, agora: datetime
) -> TurmaNova:
    """R24: a turma nasce com o nível inicial, o professor e o horário que o ADM escolheu.

    A 1ª aula é no primeiro dia da turma depois da criação (R43).
    """
    return TurmaNova(
        materia_id, nivel, professor_id, horario, primeira_aula_depois(horario, agora)
    )


def exigir_nivel_da_materia(nivel: int, nivel_maximo: int, nome_da_materia: str) -> None:
    """R24: a turma pode começar em qualquer nível da matéria, e só neles."""
    if 1 <= nivel <= nivel_maximo:
        return
    if nivel_maximo == 1:
        raise NivelForaDaMateria(f"{nome_da_materia} só tem o nível {nome_do_nivel(1)}.")
    raise NivelForaDaMateria(
        f"{nome_da_materia} tem os níveis {nome_do_nivel(1)} a {nome_do_nivel(nivel_maximo)}."
    )


def exigir_professor_livre(
    email_do_professor: str, horario: Horario, horarios_do_professor: Iterable[Horario]
) -> None:
    """R07: o professor não dá aula em duas turmas com horários que se sobrepõem."""
    conflito = horario_em_conflito(horario, horarios_do_professor)
    if conflito is not None:
        raise ConflitoDeHorario(
            f"{email_do_professor} já dá aula numa turma às {descrever_horario(conflito)}."
        )


def mudar_horario(turma: Turma, horario: Horario) -> Turma:
    """R24: o horário não muda durante a vida da turma. Pedir o mesmo horário não muda nada."""
    if horario != turma.horario:
        raise HorarioFixo(
            f"O horário da turma não muda: ela continua às {descrever_horario(turma.horario)}."
        )
    return turma


def trocar_professor(turma: Turma, professor_id: int, email_do_professor: str) -> Turma:
    """R26: o ADM troca o professor quando quiser. O nível e o horário continuam os mesmos."""
    if professor_id == turma.professor_id:
        raise MesmoProfessor(f"{email_do_professor} já dá aula nesta turma.")
    return replace(turma, professor_id=professor_id)
