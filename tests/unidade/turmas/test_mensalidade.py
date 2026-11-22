"""Mensalidade (H04, H07): a primeira é paga na matrícula, e as seguintes vencem todo mês no dia
da matrícula (R27), ou no último dia do mês que não tem esse dia (R46). Só a mensalidade seguinte
às pagas fica em aberto, desde o vencimento da anterior (R53). Com ela atrasada, o aluno tem 7
dias de tolerância, até as 23h59 do 7º dia (R28, R37). Depois que a turma encerra, nenhuma
mensalidade vence (R54)."""

from datetime import date, datetime, timedelta

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.turmas.domain.mensalidade import (
    TOLERANCIA,
    Mensalidade,
    MensalidadeNaoAberta,
    SemMensalidade,
    SituacaoDaMensalidade,
    exigir_em_aberto,
    primeira_mensalidade,
    proxima_mensalidade,
    proximo_vencimento,
    situacao_da_mensalidade,
    vence,
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


# Matrícula em 10/03/2027, com a 1ª mensalidade paga nela: a 2ª vence em 10/04.
MATRICULA_EM_10_03 = date(2027, 3, 10)
DE_10_04 = proxima_mensalidade(MATRICULA_EM_10_03, mensalidades_pagas=1)


def em(dia: int, mes: int, hora: int = 10, minuto: int = 0) -> datetime:
    return datetime(2027, mes, dia, hora, minuto, tzinfo=BRASILIA)


def test_r53_a_mensalidade_de_10_04_fica_em_aberto_quando_vence_a_de_10_03() -> None:
    assert (DE_10_04.numero, DE_10_04.vencimento, DE_10_04.abre_em) == (
        2,
        date(2027, 4, 10),
        date(2027, 3, 10),
    )


def test_r28_r37_sem_pagar_a_de_10_04_o_aluno_perde_a_vaga_na_virada_para_18_04() -> None:
    assert DE_10_04.perde_a_vaga_em == em(18, 4, 0)
    assert timedelta(days=7) == TOLERANCIA


def test_r27_em_08_04_a_mensalidade_de_10_04_esta_em_aberto() -> None:
    assert situacao_da_mensalidade(DE_10_04, em(8, 4), None) == SituacaoDaMensalidade.EM_ABERTO
    exigir_em_aberto(DE_10_04, em(8, 4), None)


def test_r28_em_17_04_as_23h_a_mensalidade_esta_atrasada_mas_ainda_e_paga() -> None:
    atrasada = situacao_da_mensalidade(DE_10_04, em(17, 4, 23), None)

    assert atrasada == SituacaoDaMensalidade.ATRASADA
    exigir_em_aberto(DE_10_04, em(17, 4, 23), None)


def test_r28_no_dia_do_vencimento_a_mensalidade_ainda_nao_esta_atrasada() -> None:
    no_dia = situacao_da_mensalidade(DE_10_04, em(10, 4, 23, 59), None)

    assert no_dia == SituacaoDaMensalidade.EM_ABERTO


def test_r53_paga_a_de_10_04_a_de_10_05_so_abre_em_10_04() -> None:
    de_10_05 = proxima_mensalidade(MATRICULA_EM_10_03, mensalidades_pagas=2)

    assert situacao_da_mensalidade(de_10_05, em(9, 4), None) == SituacaoDaMensalidade.A_ABRIR
    with pytest.raises(
        MensalidadeNaoAberta,
        match="A mensalidade de 10/05/2027 só pode ser paga a partir de 10/04/2027, quando vence "
        "a anterior.",
    ):
        exigir_em_aberto(de_10_05, em(9, 4), None)
    exigir_em_aberto(de_10_05, em(10, 4, 0), None)


def test_r54_depois_que_a_turma_encerra_nenhuma_mensalidade_vence() -> None:
    encerrada_em_09_04 = em(9, 4, 20, 30)

    assert situacao_da_mensalidade(DE_10_04, em(11, 4), encerrada_em_09_04) == (
        SituacaoDaMensalidade.SEM_MENSALIDADE
    )
    assert not vence(DE_10_04, encerrada_em_09_04)
    with pytest.raises(SemMensalidade, match="A turma encerrou: não há mensalidade a pagar."):
        exigir_em_aberto(DE_10_04, em(11, 4), encerrada_em_09_04)


def test_r54_a_mensalidade_que_venceu_antes_do_encerramento_continua_valendo() -> None:
    encerrada_em_12_04 = em(12, 4, 20, 30)

    assert vence(DE_10_04, encerrada_em_12_04)
    assert vence(DE_10_04, None)
    assert situacao_da_mensalidade(DE_10_04, em(13, 4), encerrada_em_12_04) == (
        SituacaoDaMensalidade.ATRASADA
    )
