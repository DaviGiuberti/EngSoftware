"""Horário da turma (H30): 1 ou 2 aulas por semana (R04) e horários que se sobrepõem (R07)."""

from datetime import time

import pytest

from plataforma.modules.turmas.domain.horario import (
    DiaDaSemana,
    Horario,
    HorarioInvalido,
    descrever_horario,
    horario_em_conflito,
    novo_horario,
    se_sobrepoem,
)

SEG, TER, QUA, QUI, SEX = (
    DiaDaSemana.SEGUNDA,
    DiaDaSemana.TERCA,
    DiaDaSemana.QUARTA,
    DiaDaSemana.QUINTA,
    DiaDaSemana.SEXTA,
)


def horario(*dias: DiaDaSemana, inicio: str = "19:00", fim: str = "20:30") -> Horario:
    return novo_horario(dias, time.fromisoformat(inicio), time.fromisoformat(fim))


TER_E_QUI_19H = horario(TER, QUI)


def test_r04_turma_com_1_aula_por_semana_e_aceita() -> None:
    assert horario(SEG).dias == (SEG,)


def test_r04_turma_com_2_aulas_por_semana_e_aceita_com_os_dias_em_ordem() -> None:
    assert horario(QUI, TER).dias == (TER, QUI)


def test_r04_aulas_as_segundas_quartas_e_sextas_sao_recusadas() -> None:
    with pytest.raises(HorarioInvalido, match="A turma tem no máximo 2 aulas por semana."):
        horario(SEG, QUA, SEX)


def test_r04_turma_sem_dia_de_aula_e_recusada() -> None:
    with pytest.raises(HorarioInvalido, match="Escolha 1 ou 2 dias da semana para as aulas."):
        horario()


@pytest.mark.parametrize(("inicio", "fim"), [("20:30", "19:00"), ("19:00", "19:00")])
def test_aula_que_nao_termina_depois_de_comecar_e_recusada(inicio: str, fim: str) -> None:
    with pytest.raises(HorarioInvalido, match="A aula precisa terminar depois de começar."):
        horario(TER, inicio=inicio, fim=fim)


def test_r07_19h_a_20h30_e_20h_a_21h30_no_mesmo_dia_se_sobrepoem() -> None:
    assert se_sobrepoem(horario(TER), horario(TER, inicio="20:00", fim="21:30"))


def test_r07_o_mesmo_horario_em_dias_diferentes_nao_se_sobrepoe() -> None:
    assert not se_sobrepoem(horario(TER), horario(QUA))


def test_r07_horarios_que_so_se_encostam_nao_se_sobrepoem() -> None:
    assert not se_sobrepoem(horario(TER), horario(TER, inicio="20:30", fim="22:00"))


def test_r07_um_dia_em_comum_basta_para_se_sobrepor() -> None:
    assert se_sobrepoem(TER_E_QUI_19H, horario(QUI, SEX, inicio="18:00", fim="19:30"))


def test_r07_horario_dentro_de_outro_se_sobrepoe() -> None:
    assert se_sobrepoem(horario(TER), horario(TER, inicio="19:30", fim="20:00"))


def test_r07_o_horario_em_conflito_e_o_primeiro_que_se_sobrepoe() -> None:
    quarta = horario(QUA)
    terca_mais_tarde = horario(TER, inicio="20:00", fim="21:30")

    assert horario_em_conflito(TER_E_QUI_19H, [quarta, terca_mais_tarde]) == terca_mais_tarde
    assert horario_em_conflito(TER_E_QUI_19H, [quarta]) is None


def test_o_horario_e_escrito_como_nos_criterios() -> None:
    assert descrever_horario(TER_E_QUI_19H) == "terças e quintas, das 19h às 20h30"
    assert descrever_horario(horario(SEG, inicio="08:00", fim="09:15")) == (
        "segundas, das 8h às 9h15"
    )
