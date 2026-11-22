"""Horário da turma (H30): 1 ou 2 aulas por semana (R04), com as mesmas horas em todos os dias,
e horários que se sobrepõem (R07)."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import time
from enum import IntEnum

from plataforma.compartilhado.recusa import Recusa

MAXIMO_DE_AULAS_POR_SEMANA = 2


class DiaDaSemana(IntEnum):
    """Na mesma ordem do date.weekday(): a segunda é 0."""

    SEGUNDA = 0
    TERCA = 1
    QUARTA = 2
    QUINTA = 3
    SEXTA = 4
    SABADO = 5
    DOMINGO = 6


NOME_NO_PLURAL = {
    DiaDaSemana.SEGUNDA: "segundas",
    DiaDaSemana.TERCA: "terças",
    DiaDaSemana.QUARTA: "quartas",
    DiaDaSemana.QUINTA: "quintas",
    DiaDaSemana.SEXTA: "sextas",
    DiaDaSemana.SABADO: "sábados",
    DiaDaSemana.DOMINGO: "domingos",
}


class HorarioInvalido(Recusa):
    """R04: a mensagem diz o que está errado no horário."""


@dataclass(frozen=True)
class Horario:
    """Os dias das aulas, em ordem, e as horas de início e de fim, iguais em todos os dias."""

    dias: tuple[DiaDaSemana, ...]
    inicio: time
    fim: time


def novo_horario(dias: Iterable[DiaDaSemana], inicio: time, fim: time) -> Horario:
    """R04: 1 ou 2 aulas por semana, em dias diferentes, e a aula termina depois de começar."""
    dias_em_ordem = tuple(sorted(set(dias)))
    if not dias_em_ordem:
        raise HorarioInvalido("Escolha 1 ou 2 dias da semana para as aulas.")
    if len(dias_em_ordem) > MAXIMO_DE_AULAS_POR_SEMANA:
        raise HorarioInvalido(
            f"A turma tem no máximo {MAXIMO_DE_AULAS_POR_SEMANA} aulas por semana."
        )
    if fim <= inicio:
        raise HorarioInvalido("A aula precisa terminar depois de começar.")
    return Horario(dias_em_ordem, inicio, fim)


def se_sobrepoem(um: Horario, outro: Horario) -> bool:
    """R07: dois horários se sobrepõem quando têm um dia em comum e as horas se cruzam.

    Horários que só se encostam, como 19h–20h e 20h–21h, não se sobrepõem.
    """
    dia_em_comum = bool(set(um.dias) & set(outro.dias))
    return dia_em_comum and um.inicio < outro.fim and outro.inicio < um.fim


def horario_em_conflito(horario: Horario, ocupados: Iterable[Horario]) -> Horario | None:
    """O primeiro dos horários ocupados que se sobrepõe ao horário, ou None (R07)."""
    return next((ocupado for ocupado in ocupados if se_sobrepoem(horario, ocupado)), None)


def formatar_hora(hora: time) -> str:
    """19h00 vira "19h", e 20h30 vira "20h30"."""
    return f"{hora.hour}h" if hora.minute == 0 else f"{hora.hour}h{hora.minute:02d}"


def descrever_horario(horario: Horario) -> str:
    """Como nos critérios: "terças e quintas, das 19h às 20h30"."""
    dias = " e ".join(NOME_NO_PLURAL[dia] for dia in horario.dias)
    return f"{dias}, das {formatar_hora(horario.inicio)} às {formatar_hora(horario.fim)}"
