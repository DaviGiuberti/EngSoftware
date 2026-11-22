"""Mensalidade da turma (H04, H07): a primeira é paga na matrícula, e as seguintes vencem todo mês
no dia da matrícula (R27), ou no último dia do mês que não tem esse dia (R46)."""

import calendar
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Mensalidade:
    """Uma mensalidade paga. O pagamento é simulado e conta na hora (ADR 0003)."""

    vencimento: date
    valor_em_centavos: int
    paga_em: datetime


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
