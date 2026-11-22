"""Calendário da etapa (H30): a 1ª aula é no primeiro dia da turma depois da criação, as aulas
seguem os dias e o horário da turma, e a aula conta como dada quando começa (R43). A etapa tem
24 aulas (R17)."""

from datetime import datetime, time
from itertools import islice

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.turmas.domain.etapa import (
    AULAS_POR_ETAPA,
    aulas_dadas,
    datas_das_aulas,
    primeira_aula_depois,
)
from plataforma.modules.turmas.domain.horario import DiaDaSemana, novo_horario

TER_E_QUI_19H = novo_horario([DiaDaSemana.TERCA, DiaDaSemana.QUINTA], time(19), time(20, 30))
SEGUNDA_23_11_14H = datetime(2026, 11, 23, 14, 0, tzinfo=BRASILIA)
TERCA_24_11_19H = datetime(2026, 11, 24, 19, 0, tzinfo=BRASILIA)


def em(dia: int, mes: int, hora: int = 19, minuto: int = 0, ano: int = 2026) -> datetime:
    return datetime(ano, mes, dia, hora, minuto, tzinfo=BRASILIA)


def test_r43_criada_na_segunda_23_11_as_14h_a_turma_de_terca_e_quinta_comeca_dia_24_as_19h(
) -> None:
    assert primeira_aula_depois(TER_E_QUI_19H, SEGUNDA_23_11_14H) == TERCA_24_11_19H


def test_r43_criada_no_dia_da_aula_antes_do_inicio_comeca_no_mesmo_dia() -> None:
    assert primeira_aula_depois(TER_E_QUI_19H, em(24, 11, 18, 59)) == TERCA_24_11_19H


def test_r43_criada_na_hora_do_inicio_comeca_no_dia_seguinte_da_turma() -> None:
    assert primeira_aula_depois(TER_E_QUI_19H, TERCA_24_11_19H) == em(26, 11)


def test_r43_criada_na_sexta_comeca_na_terca_seguinte() -> None:
    assert primeira_aula_depois(TER_E_QUI_19H, em(27, 11, 10)) == em(1, 12)


def test_r43_turma_de_1_aula_por_semana_criada_depois_do_horario_comeca_na_semana_seguinte(
) -> None:
    segunda_8h = novo_horario([DiaDaSemana.SEGUNDA], time(8), time(9, 30))

    assert primeira_aula_depois(segunda_8h, SEGUNDA_23_11_14H) == em(30, 11, 8)


def test_r43_as_aulas_seguem_os_dias_e_o_horario_da_turma() -> None:
    quatro_primeiras = list(islice(datas_das_aulas(TER_E_QUI_19H, TERCA_24_11_19H), 4))

    assert quatro_primeiras == [em(24, 11), em(26, 11), em(1, 12), em(3, 12)]


def test_r43_antes_da_1a_aula_nenhuma_aula_foi_dada() -> None:
    assert aulas_dadas(TER_E_QUI_19H, TERCA_24_11_19H, SEGUNDA_23_11_14H) == 0


def test_r43_a_aula_conta_como_dada_quando_comeca() -> None:
    assert aulas_dadas(TER_E_QUI_19H, TERCA_24_11_19H, em(24, 11, 18, 59)) == 0
    assert aulas_dadas(TER_E_QUI_19H, TERCA_24_11_19H, TERCA_24_11_19H) == 1


def test_r43_seis_semanas_de_terca_e_quinta_dao_12_aulas_e_a_13a_e_em_5_de_janeiro() -> None:
    assert aulas_dadas(TER_E_QUI_19H, TERCA_24_11_19H, em(31, 12)) == 12
    assert aulas_dadas(TER_E_QUI_19H, TERCA_24_11_19H, em(5, 1, 18, 59, ano=2027)) == 12
    assert aulas_dadas(TER_E_QUI_19H, TERCA_24_11_19H, em(5, 1, ano=2027)) == 13


def test_r17_a_etapa_tem_24_aulas_e_a_contagem_para_na_24a() -> None:
    um_ano_depois = em(24, 11, ano=2027)

    assert AULAS_POR_ETAPA == 24
    assert aulas_dadas(TER_E_QUI_19H, TERCA_24_11_19H, um_ano_depois) == 24
