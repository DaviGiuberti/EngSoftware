"""Calendário da etapa (H30, H22): a 1ª aula é no primeiro dia da turma depois da criação, as
aulas seguem os dias e o horário da turma, e a aula conta como dada quando começa (R43). A etapa
tem 24 aulas (R17), e a aula não realizada não conta nelas: é reposta no fim (R18). Só a aula
ainda sem presença pode ser marcada como não realizada (R48)."""

from datetime import date, datetime, time, timedelta
from itertools import islice

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.turmas.domain.etapa import (
    AULAS_POR_ETAPA,
    AulaComPresenca,
    Etapa,
    EtapaNaoEncontrada,
    EtapaTerminada,
    JaNaoRealizada,
    SemAulaNaData,
    aula_na_data,
    aula_nas_etapas,
    aulas_dadas,
    calendario,
    datas_das_aulas,
    etapa_do_nivel,
    exigir_etapa_em_andamento,
    marcar_nao_realizada,
    primeira_aula_depois,
    proxima_aula,
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


# Turma de terça e quinta com a 1ª aula na quinta 11/03/2027: as aulas ímpares caem nas quintas
# e as pares nas terças. A 10ª aula é na terça 13/04, e a 24ª, na terça 01/06.
QUINTA_11_03_19H = datetime(2027, 3, 11, 19, 0, tzinfo=BRASILIA)
TERCA_13_04 = date(2027, 4, 13)
QUINTA_25_03 = date(2027, 3, 25)


def test_r43_o_calendario_da_etapa_tem_24_aulas_numeradas() -> None:
    aulas = calendario(TER_E_QUI_19H, QUINTA_11_03_19H)

    assert [aula.numero for aula in aulas] == list(range(1, 25))
    assert aulas[9].data == TERCA_13_04
    assert aulas[-1].inicio == em(1, 6, ano=2027)


def test_r17_r18_ja_deu_9_aulas_marca_13_04_e_a_proxima_continua_sendo_a_10a() -> None:
    segunda_12_04 = em(12, 4, 10, ano=2027)
    aulas = calendario(TER_E_QUI_19H, QUINTA_11_03_19H, {TERCA_13_04})

    proxima = proxima_aula(aulas, segunda_12_04)

    assert aulas_dadas(TER_E_QUI_19H, QUINTA_11_03_19H, segunda_12_04, {TERCA_13_04}) == 9
    assert proxima is not None
    assert (proxima.numero, proxima.data) == (10, date(2027, 4, 15))


def test_r18_a_aula_nao_realizada_fica_no_calendario_sem_numero_e_nao_conta_como_dada() -> None:
    aulas = calendario(TER_E_QUI_19H, QUINTA_11_03_19H, {TERCA_13_04})

    assert aula_na_data(aulas, TERCA_13_04).numero is None
    assert aulas_dadas(TER_E_QUI_19H, QUINTA_11_03_19H, em(13, 4, 20, ano=2027), {TERCA_13_04}) == 9


def test_r18_a_24a_aula_que_seria_numa_terca_passa_para_a_quinta_seguinte() -> None:
    aulas = calendario(TER_E_QUI_19H, QUINTA_11_03_19H, {TERCA_13_04})

    assert len(aulas) == 25
    assert (aulas[-1].numero, aulas[-1].inicio) == (24, em(3, 6, ano=2027))


def test_r18_depois_da_24a_aula_nao_ha_proxima_aula_na_etapa() -> None:
    aulas = calendario(TER_E_QUI_19H, QUINTA_11_03_19H)

    assert proxima_aula(aulas, em(1, 6, 20, ano=2027)) is None


def test_r48_aula_futura_sem_presenca_pode_ser_marcada_como_nao_realizada() -> None:
    aulas = calendario(TER_E_QUI_19H, QUINTA_11_03_19H)

    assert marcar_nao_realizada(aulas, frozenset(), TERCA_13_04, set()) == {TERCA_13_04}


def test_r48_aula_passada_sem_presenca_tambem_pode_ser_marcada() -> None:
    aulas = calendario(TER_E_QUI_19H, QUINTA_11_03_19H)
    ja_marcada = frozenset({TERCA_13_04})

    assert marcar_nao_realizada(aulas, ja_marcada, date(2027, 3, 11), set()) == {
        TERCA_13_04,
        date(2027, 3, 11),
    }


def test_r48_a_5a_aula_com_presenca_lancada_nao_vira_nao_realizada() -> None:
    aulas = calendario(TER_E_QUI_19H, QUINTA_11_03_19H)

    with pytest.raises(
        AulaComPresenca,
        match="A 5ª aula, de 25/03/2027, já tem presença lançada: ela aconteceu e não pode ser "
        "marcada como não realizada.",
    ):
        marcar_nao_realizada(aulas, frozenset(), QUINTA_25_03, {QUINTA_25_03})


def test_aula_ja_marcada_como_nao_realizada_nao_e_marcada_de_novo() -> None:
    aulas = calendario(TER_E_QUI_19H, QUINTA_11_03_19H, {TERCA_13_04})

    with pytest.raises(
        JaNaoRealizada, match="A aula de 13/04/2027 já está marcada como não realizada."
    ):
        marcar_nao_realizada(aulas, frozenset({TERCA_13_04}), TERCA_13_04, set())


def test_dia_sem_aula_da_etapa_e_recusado() -> None:
    aulas = calendario(TER_E_QUI_19H, QUINTA_11_03_19H)

    with pytest.raises(SemAulaNaData, match="A etapa não tem aula em 14/04/2027."):
        aula_na_data(aulas, date(2027, 4, 14))


# A etapa do N2 da turma que começa na terça 24/11/2026 tem a 24ª aula na quinta 11/02/2027.
ETAPA_DO_N2 = Etapa(TER_E_QUI_19H, 2, TERCA_24_11_19H)


def test_r17_a_etapa_termina_no_fim_da_24a_aula() -> None:
    assert ETAPA_DO_N2.fim == em(11, 2, 20, 30, ano=2027)
    assert not ETAPA_DO_N2.terminou(em(11, 2, 20, 29, ano=2027))
    assert ETAPA_DO_N2.terminou(em(11, 2, 20, 30, ano=2027))


def test_r18_a_aula_nao_realizada_empurra_o_fim_da_etapa_para_o_proximo_dia_da_turma() -> None:
    com_nao_realizada = Etapa(TER_E_QUI_19H, 2, TERCA_24_11_19H, frozenset({date(2026, 11, 26)}))

    assert com_nao_realizada.fim == em(16, 2, 20, 30, ano=2027)


def test_r04_r43_a_etapa_seguinte_comeca_no_proximo_dia_da_turma_no_mesmo_horario() -> None:
    seguinte = ETAPA_DO_N2.seguinte()

    assert (seguinte.nivel, seguinte.horario) == (3, TER_E_QUI_19H)
    assert seguinte.inicio == em(16, 2, ano=2027)
    assert seguinte.nao_realizadas == frozenset()
    assert seguinte.aulas_dadas(ETAPA_DO_N2.fim) == 0


def test_r43_a_etapa_seguinte_da_turma_de_1_aula_por_semana_comeca_na_semana_seguinte() -> None:
    quinta_19h = novo_horario([DiaDaSemana.QUINTA], time(19), time(20, 30))
    etapa = Etapa(quinta_19h, 1, em(26, 11))

    assert etapa.seguinte().inicio == etapa.fim.replace(hour=19, minute=0) + timedelta(weeks=1)


def test_r48_depois_do_fim_da_etapa_as_aulas_dela_nao_mudam_mais() -> None:
    with pytest.raises(
        EtapaTerminada,
        match="A etapa do N2 terminou em 11/02/2027, às 20h30: as aulas dela não mudam mais.",
    ):
        exigir_etapa_em_andamento(ETAPA_DO_N2, em(12, 2, ano=2027))
    exigir_etapa_em_andamento(ETAPA_DO_N2, em(11, 2, 20, 29, ano=2027))


def test_a_aula_de_uma_data_e_achada_na_etapa_que_terminou_ou_na_atual() -> None:
    etapas = [ETAPA_DO_N2, ETAPA_DO_N2.seguinte()]

    etapa, aula = aula_nas_etapas(etapas, date(2027, 2, 11))
    assert (etapa.nivel, aula.numero) == (2, 24)
    etapa, aula = aula_nas_etapas(etapas, date(2027, 2, 16))
    assert (etapa.nivel, aula.numero) == (3, 1)


def test_data_sem_aula_em_nenhuma_etapa_da_turma_e_recusada() -> None:
    with pytest.raises(SemAulaNaData, match="A turma não tem aula em 15/02/2027."):
        aula_nas_etapas([ETAPA_DO_N2], date(2027, 2, 15))


def test_a_turma_so_tem_as_etapas_dos_niveis_por_que_passou() -> None:
    assert etapa_do_nivel([ETAPA_DO_N2], 2) == ETAPA_DO_N2
    with pytest.raises(EtapaNaoEncontrada, match="A turma não tem a etapa do N3."):
        etapa_do_nivel([ETAPA_DO_N2], 3)
