"""Calendário da etapa: 24 aulas (R17), a partir da 1ª, nos dias e no horário da turma (R43). A
aula não realizada não conta nas 24 e é reposta no fim da etapa (R18). Só a aula ainda sem
presença pode ser marcada como não realizada, passada ou futura (R48)."""

from collections.abc import Collection, Iterator, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.turmas.domain.horario import Horario

AULAS_POR_ETAPA = 24


class SemAulaNaData(Recusa):
    """A mensagem diz a data em que a etapa não tem aula."""


class JaNaoRealizada(Recusa):
    """A mensagem diz a data da aula."""


class AulaComPresenca(Recusa):
    """R48: a mensagem diz que a aula aconteceu."""


@dataclass(frozen=True)
class AulaDaEtapa:
    """Uma data de aula da etapa. A não realizada não tem número: não conta nas 24 (R18)."""

    inicio: datetime
    numero: int | None

    @property
    def data(self) -> date:
        return self.inicio.date()


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


def calendario(
    horario: Horario, inicio_da_etapa: datetime, nao_realizadas: Collection[date] = frozenset()
) -> list[AulaDaEtapa]:
    """R43 e R18: as aulas da etapa, da 1ª à 24ª, com as não realizadas no meio, sem número.

    Cada não realizada empurra o fim da etapa para o próximo dia da turma, no mesmo horário.
    """
    aulas: list[AulaDaEtapa] = []
    dadas = 0
    datas = datas_das_aulas(horario, inicio_da_etapa)
    while dadas < AULAS_POR_ETAPA:
        inicio = next(datas)
        if inicio.date() in nao_realizadas:
            aulas.append(AulaDaEtapa(inicio, None))
        else:
            dadas += 1
            aulas.append(AulaDaEtapa(inicio, dadas))
    return aulas


def aulas_dadas(
    horario: Horario,
    inicio_da_etapa: datetime,
    agora: datetime,
    nao_realizadas: Collection[date] = frozenset(),
) -> int:
    """R43: quantas aulas da etapa já começaram, sem as não realizadas (R18). Para na 24ª (R17)."""
    return sum(
        1
        for aula in calendario(horario, inicio_da_etapa, nao_realizadas)
        if aula.numero is not None and aula.inicio <= agora
    )


def proxima_aula(aulas: Sequence[AulaDaEtapa], agora: datetime) -> AulaDaEtapa | None:
    """A próxima aula realizada da etapa depois de agora, ou None se a etapa já deu as 24."""
    return next((a for a in aulas if a.numero is not None and a.inicio > agora), None)


def aula_na_data(aulas: Sequence[AulaDaEtapa], data: date) -> AulaDaEtapa:
    aula = next((aula for aula in aulas if aula.data == data), None)
    if aula is None:
        raise SemAulaNaData(f"A etapa não tem aula em {data:%d/%m/%Y}.")
    return aula


def marcar_nao_realizada(
    aulas: Sequence[AulaDaEtapa],
    nao_realizadas: frozenset[date],
    data: date,
    datas_com_presenca: Collection[date],
) -> frozenset[date]:
    """R18 e R48: a aula ainda sem presença, passada ou futura, sai das 24 e é reposta no fim.

    A aula com presença lançada aconteceu e não pode ser marcada.
    """
    aula = aula_na_data(aulas, data)
    if aula.numero is None:
        raise JaNaoRealizada(f"A aula de {data:%d/%m/%Y} já está marcada como não realizada.")
    if data in datas_com_presenca:
        raise AulaComPresenca(
            f"A {aula.numero}ª aula, de {data:%d/%m/%Y}, já tem presença lançada: ela aconteceu "
            "e não pode ser marcada como não realizada."
        )
    return nao_realizadas | {data}
