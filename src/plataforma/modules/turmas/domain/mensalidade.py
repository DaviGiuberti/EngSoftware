"""Mensalidade da turma (H04, H07): a primeira é paga na matrícula, e as seguintes vencem todo mês
no dia da matrícula (R27), ou no último dia do mês que não tem esse dia (R46).

Só a mensalidade seguinte às pagas fica em aberto, desde o vencimento da anterior (R53). Atrasada,
ela ainda pode ser paga durante os 7 dias de tolerância, até as 23h59 do 7º dia; na virada para o
8º, o aluno perde a vaga (R28, R37). Depois que a turma encerra, nenhuma mensalidade vence (R54).
"""

import calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum

from plataforma.compartilhado.horario import BRASILIA
from plataforma.compartilhado.recusa import Recusa

# R28: os 7 dias depois do vencimento em que o aluno ainda mantém a vaga.
TOLERANCIA = timedelta(days=7)


class MensalidadeNaoAberta(Recusa):
    """R53: a mensagem diz a partir de quando a mensalidade pode ser paga."""


class SemMensalidade(Recusa):
    mensagem = "A turma encerrou: não há mensalidade a pagar."


@dataclass(frozen=True)
class Mensalidade:
    """Uma mensalidade paga. O pagamento é simulado e conta na hora (ADR 0003)."""

    vencimento: date
    valor_em_centavos: int
    paga_em: datetime


@dataclass(frozen=True)
class MensalidadeDevida:
    """A mensalidade seguinte às que o aluno pagou: o número dela, o vencimento (R27), o dia em
    que ela fica em aberto (R53) e quando o aluno perde a vaga sem pagá-la (R28, R37)."""

    numero: int
    vencimento: date
    abre_em: date
    perde_a_vaga_em: datetime


class SituacaoDaMensalidade(StrEnum):
    A_ABRIR = "a_abrir"
    EM_ABERTO = "em_aberto"
    ATRASADA = "atrasada"
    SEM_MENSALIDADE = "sem_mensalidade"


def vencimento(data_da_matricula: date, numero: int) -> date:
    """R27 e R46: a 1ª mensalidade vence na matrícula, e a de número n, n - 1 meses depois.

    No mês que não tem o dia da matrícula, ela vence no último dia dele.
    """
    meses_desde_janeiro = data_da_matricula.month - 1 + numero - 1
    ano = data_da_matricula.year + meses_desde_janeiro // 12
    mes = meses_desde_janeiro % 12 + 1
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(data_da_matricula.day, ultimo_dia))


def primeira_mensalidade(valor_em_centavos: int, agora: datetime) -> Mensalidade:
    """R27: a primeira mensalidade é paga na matrícula e vence no próprio dia."""
    return Mensalidade(agora.date(), valor_em_centavos, agora)


def proximo_vencimento(data_da_matricula: date, mensalidades_pagas: int) -> date:
    """O vencimento da mensalidade seguinte às que o aluno já pagou."""
    return vencimento(data_da_matricula, mensalidades_pagas + 1)


def proxima_mensalidade(data_da_matricula: date, mensalidades_pagas: int) -> MensalidadeDevida:
    """R53: a mensalidade seguinte às pagas, que fica em aberto quando a anterior vence. R37: sem
    pagá-la, o aluno perde a vaga à 0h do 8º dia depois do vencimento."""
    numero = mensalidades_pagas + 1
    vence_em = vencimento(data_da_matricula, numero)
    perde_em = datetime.combine(vence_em + TOLERANCIA + timedelta(days=1), time(0), BRASILIA)
    return MensalidadeDevida(
        numero, vence_em, vencimento(data_da_matricula, numero - 1), perde_em
    )


def vence(devida: MensalidadeDevida, encerrada_em: datetime | None) -> bool:
    """R54: depois que a turma encerra, nenhuma mensalidade vence. A que venceu antes, vale."""
    return encerrada_em is None or devida.vencimento <= encerrada_em.date()


def situacao_da_mensalidade(
    devida: MensalidadeDevida, agora: datetime, encerrada_em: datetime | None
) -> SituacaoDaMensalidade:
    """Se a mensalidade seguinte ainda vai abrir, está em aberto ou já venceu (R28, R53, R54).

    No dia do vencimento, ela ainda não está atrasada.
    """
    if not vence(devida, encerrada_em):
        return SituacaoDaMensalidade.SEM_MENSALIDADE
    if agora.date() < devida.abre_em:
        return SituacaoDaMensalidade.A_ABRIR
    if agora.date() > devida.vencimento:
        return SituacaoDaMensalidade.ATRASADA
    return SituacaoDaMensalidade.EM_ABERTO


def exigir_em_aberto(
    devida: MensalidadeDevida, agora: datetime, encerrada_em: datetime | None
) -> None:
    """R53 e R54: só a mensalidade em aberto, ou atrasada dentro da tolerância, é paga.

    Depois da tolerância, o aluno já perdeu a vaga e não tem mais o que pagar nesta turma (R28).
    """
    match situacao_da_mensalidade(devida, agora, encerrada_em):
        case SituacaoDaMensalidade.SEM_MENSALIDADE:
            raise SemMensalidade()
        case SituacaoDaMensalidade.A_ABRIR:
            raise MensalidadeNaoAberta(
                f"A mensalidade de {devida.vencimento:%d/%m/%Y} só pode ser paga a partir de "
                f"{devida.abre_em:%d/%m/%Y}, quando vence a anterior."
            )
        case _:
            return
