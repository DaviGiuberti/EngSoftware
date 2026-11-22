"""Turma (H30, H31, H10): matéria, nível, professor, horário fixo e 12 vagas (R04, R24), professor
sem conflito de horário (R07) e troca de professor (R26). No fim de cada etapa, a turma passa para
o nível seguinte com o mesmo professor e o mesmo horário (R04, R26) e, depois da etapa do nível
máximo, encerra (R09). Ninguém encerra a turma antes disso (R25)."""

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import NoReturn

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.materias.domain.materia import nome_do_nivel
from plataforma.modules.turmas.domain.etapa import (
    AulaDaEtapa,
    Etapa,
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


class TurmaAberta(Recusa):
    """R25: a mensagem diz quando a turma encerra."""


class TurmaEncerrada(Recusa):
    """R09: a mensagem diz que a turma concluiu o nível máximo."""


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
    """nivel e inicio_da_etapa são os da etapa atual (R04, R43), e nao_realizadas, as datas das
    aulas dela que não aconteceram (R18). encerrada_em é o fim da etapa do nível máximo (R09)."""

    id: int
    materia_id: int
    nivel: int
    professor_id: int
    horario: Horario
    inicio_da_etapa: datetime
    nao_realizadas: frozenset[date] = field(default_factory=frozenset)
    encerrada_em: datetime | None = None

    @property
    def etapa(self) -> Etapa:
        return Etapa(self.horario, self.nivel, self.inicio_da_etapa, self.nao_realizadas)

    @property
    def encerrada(self) -> bool:
        return self.encerrada_em is not None

    def calendario(self) -> list[AulaDaEtapa]:
        return self.etapa.calendario()

    def aulas_dadas(self, agora: datetime) -> int:
        return self.etapa.aulas_dadas(agora)


@dataclass(frozen=True)
class PassagemDeEtapa:
    """R04: no fim de uma etapa, em, a turma passa para a etapa do nível seguinte."""

    em: datetime
    etapa: Etapa


@dataclass(frozen=True)
class Encerramento:
    """R09: no fim da etapa do nível máximo, em, a turma encerra."""

    em: datetime


type MudancaDaTurma = PassagemDeEtapa | Encerramento


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


def mudancas_ate(turma: Turma, nivel_maximo: int, agora: datetime) -> list[MudancaDaTurma]:
    """R04, R09 e R17: as passagens de etapa e o encerramento da turma até agora, em ordem.

    No fim de cada etapa, a turma passa para o nível seguinte, com o mesmo professor e o mesmo
    horário (R24, R26). No fim da etapa do nível máximo, ela encerra.
    """
    if turma.encerrada:
        return []
    mudancas: list[MudancaDaTurma] = []
    etapa = turma.etapa
    while etapa.terminou(agora):
        if etapa.nivel >= nivel_maximo:
            mudancas.append(Encerramento(etapa.fim))
            break
        seguinte = etapa.seguinte()
        mudancas.append(PassagemDeEtapa(etapa.fim, seguinte))
        etapa = seguinte
    return mudancas


def com_a_mudanca(turma: Turma, mudanca: MudancaDaTurma) -> Turma:
    """A turma depois de encerrar (R09) ou de passar para a etapa seguinte (R04)."""
    if isinstance(mudanca, Encerramento):
        return replace(turma, encerrada_em=mudanca.em)
    etapa = mudanca.etapa
    return replace(
        turma, nivel=etapa.nivel, inicio_da_etapa=etapa.inicio, nao_realizadas=etapa.nao_realizadas
    )


def encerrar(turma: Turma, nivel_maximo: int) -> NoReturn:
    """R25: o ADM não encerra a turma, nem quando ela fica sem alunos. Ela encerra sozinha no fim
    da etapa do nível máximo (R09)."""
    if turma.encerrada:
        raise TurmaEncerrada("Esta turma já está encerrada.")
    raise TurmaAberta(
        "A turma não pode ser encerrada: ela encerra sozinha no fim da etapa do "
        f"{nome_do_nivel(nivel_maximo)}, o nível máximo."
    )


def exigir_aberta(turma: Turma) -> None:
    """R09: a turma encerrada não tem mais aulas, então não recebe matrícula nem lista de espera."""
    if turma.encerrada:
        raise TurmaEncerrada("Esta turma foi encerrada: ela concluiu o nível máximo da matéria.")


def horarios_ocupados(turmas: Iterable[Turma]) -> list[Horario]:
    """R07: só a turma aberta ocupa o horário. A encerrada não tem mais aulas (R09)."""
    return [turma.horario for turma in turmas if not turma.encerrada]
