"""Mensalidade (H04, H07): a primeira é paga na matrícula, e as seguintes vencem todo mês no dia
da matrícula (R27), ou no último dia do mês que não tem esse dia (R46)."""

from datetime import date, datetime

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.turmas.domain.mensalidade import (
    Mensalidade,
    primeira_mensalidade,
    proximo_vencimento,
    vencimento,
)


def test_r27_a_primeira_mensalidade_e_paga_na_matricula_e_vence_no_mesmo_dia() -> None:
    dez_de_marco = datetime(2027, 3, 10, 10, 0, tzinfo=BRASILIA)

    assert primeira_mensalidade(20000, dez_de_marco) == Mensalidade(
        vencimento=date(2027, 3, 10), valor_em_centavos=20000, paga_em=dez_de_marco
    )


def test_r27_matricula_em_10_03_a_proxima_mensalidade_vence_em_10_04() -> None:
    assert proximo_vencimento(date(2027, 3, 10), mensalidades_pagas=1) == date(2027, 4, 10)


def test_r27_as_mensalidades_seguintes_vencem_todo_mes_no_dia_da_matricula() -> None:
    assert [vencimento(date(2027, 3, 10), numero) for numero in (1, 2, 3)] == [
        date(2027, 3, 10),
        date(2027, 4, 10),
        date(2027, 5, 10),
    ]


def test_r46_matricula_em_31_01_vence_em_28_02_e_depois_em_31_03() -> None:
    assert vencimento(date(2027, 1, 31), 2) == date(2027, 2, 28)
    assert vencimento(date(2027, 1, 31), 3) == date(2027, 3, 31)


def test_r46_em_ano_bissexto_vence_em_29_02() -> None:
    assert vencimento(date(2028, 1, 31), 2) == date(2028, 2, 29)


def test_r27_a_mensalidade_seguinte_a_de_dezembro_vence_em_janeiro_do_ano_seguinte() -> None:
    assert vencimento(date(2026, 12, 30), 2) == date(2027, 1, 30)
