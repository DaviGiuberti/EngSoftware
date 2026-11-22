"""Calendário da etapa: 24 aulas (R17), a partir da 1ª, nos dias e no horário da turma (R43)."""

from collections.abc import Iterator
from datetime import datetime, timedelta
from itertools import islice, takewhile

from plataforma.modules.turmas.domain.horario import Horario

AULAS_POR_ETAPA = 24


def primeira_aula_depois(horario: Horario, momento: datetime) -> datetime:
    """R43: o primeiro dia da turma em que a aula começa depois do momento da criação."""
    candidatas = []
    for dia in horario.dias:
        data = momento.date() + timedelta(days=(dia - momento.weekday()) % 7)
        inicio = datetime.combine(data, horario.inicio, tzinfo=momento.tzinfo)
        # No dia da semana da criação, a aula de hoje só serve se ainda não começou.
        if inicio <= momento:
            inicio += timedelta(weeks=1)
        candidatas.append(inicio)
    return min(candidatas)


def datas_das_aulas(horario: Horario, inicio_da_etapa: datetime) -> Iterator[datetime]:
    """R43: o início de cada aula da etapa, da 1ª em diante, nos dias e no horário da turma.

    A sequência não acaba: quem a usa pega as aulas de que precisa.
    """
    data = inicio_da_etapa.date()
    while True:
        if data.weekday() in horario.dias:
            yield datetime.combine(data, horario.inicio, tzinfo=inicio_da_etapa.tzinfo)
        data += timedelta(days=1)


def aulas_dadas(horario: Horario, inicio_da_etapa: datetime, agora: datetime) -> int:
    """R43: quantas aulas da etapa já começaram. Depois da 24ª, a contagem para (R17)."""
    aulas_da_etapa = islice(datas_das_aulas(horario, inicio_da_etapa), AULAS_POR_ETAPA)
    return sum(1 for _ in takewhile(lambda inicio: inicio <= agora, aulas_da_etapa))
