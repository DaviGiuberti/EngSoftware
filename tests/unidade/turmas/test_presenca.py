"""Presença e faltas (H21, H22, H08): a presença é lançada por aula, só em aula que já começou
(R43) e que foi realizada (R18), para os alunos que estão na turma desde aquela aula. As faltas
contam a partir da entrada do aluno, com limite de 6 por etapa (R08)."""

from datetime import date, datetime, time

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.turmas.domain.etapa import aula_na_data, calendario
from plataforma.modules.turmas.domain.horario import DiaDaSemana, novo_horario
from plataforma.modules.turmas.domain.presenca import (
    AulaAindaNaoComecou,
    FaltaDeQuemNaoEstaNaAula,
    Presenca,
    PresencaEmAulaNaoRealizada,
    PresencaJaLancada,
    alunos_da_aula,
    exigir_aula_para_presenca,
    faltas,
    lancar,
    passou_do_limite,
)

ANA, BRUNO = 1, 2
TER_E_QUI_19H = novo_horario([DiaDaSemana.TERCA, DiaDaSemana.QUINTA], time(19), time(20, 30))
# A 1ª aula é na quinta 11/03/2027. A 5ª é na quinta 25/03, e a 10ª, na terça 13/04.
QUINTA_11_03_19H = datetime(2027, 3, 11, 19, 0, tzinfo=BRASILIA)
QUINTA_25_03 = date(2027, 3, 25)
TERCA_13_04 = date(2027, 4, 13)
AULAS = calendario(TER_E_QUI_19H, QUINTA_11_03_19H)


def data_da(numero: int) -> date:
    return AULAS[numero - 1].data


def ausencias(aluno: int, *numeros: int) -> list[Presenca]:
    return [Presenca(aluno, data_da(numero), presente=False) for numero in numeros]


def test_r10_carlos_lanca_a_5a_aula_com_ana_presente_e_bruno_ausente() -> None:
    presencas = lancar(QUINTA_25_03, alunos=[ANA, BRUNO], ausentes={BRUNO})

    assert presencas == [
        Presenca(ANA, QUINTA_25_03, presente=True),
        Presenca(BRUNO, QUINTA_25_03, presente=False),
    ]
    assert faltas([p for p in presencas if p.aluno_id == BRUNO], AULAS, aula_de_entrada=1) == 1


def test_so_quem_esta_na_aula_recebe_falta_nela() -> None:
    with pytest.raises(
        FaltaDeQuemNaoEstaNaAula, match="Só quem está na turma desde esta aula recebe falta nela."
    ):
        lancar(QUINTA_25_03, alunos=[ANA], ausentes={BRUNO})


def test_r18_aula_nao_realizada_nao_recebe_presenca() -> None:
    aulas = calendario(TER_E_QUI_19H, QUINTA_11_03_19H, {TERCA_13_04})

    with pytest.raises(
        PresencaEmAulaNaoRealizada,
        match="A aula de 13/04/2027 não foi realizada: ela não recebe presença.",
    ):
        exigir_aula_para_presenca(
            aula_na_data(aulas, TERCA_13_04), datetime(2027, 4, 14, tzinfo=BRASILIA), False
        )


def test_r43_aula_que_ainda_nao_comecou_nao_recebe_presenca() -> None:
    with pytest.raises(
        AulaAindaNaoComecou,
        match="A 10ª aula começa em 13/04/2027, às 19h: a presença só é lançada depois que "
        "ela começa.",
    ):
        exigir_aula_para_presenca(
            aula_na_data(AULAS, TERCA_13_04), datetime(2027, 4, 13, 18, 59, tzinfo=BRASILIA), False
        )


def test_a_presenca_de_uma_aula_e_lancada_uma_vez() -> None:
    with pytest.raises(PresencaJaLancada, match="A presença da 5ª aula já foi lançada."):
        exigir_aula_para_presenca(
            aula_na_data(AULAS, QUINTA_25_03), datetime(2027, 3, 26, tzinfo=BRASILIA), True
        )


def test_r43_a_aula_que_ja_comecou_recebe_presenca() -> None:
    numero = exigir_aula_para_presenca(
        aula_na_data(AULAS, QUINTA_25_03), datetime(2027, 3, 25, 19, 0, tzinfo=BRASILIA), False
    )

    assert numero == 5


def test_r08_a_aula_tem_os_alunos_que_entraram_ate_ela() -> None:
    entradas = {ANA: 1, BRUNO: 10}

    assert alunos_da_aula(entradas, 5) == [ANA]
    assert alunos_da_aula(entradas, 10) == [ANA, BRUNO]


def test_r08_4_faltas_nas_15_aulas_dadas_ficam_dentro_do_limite_de_6() -> None:
    quatro = faltas(ausencias(ANA, 2, 5, 8, 13), AULAS, aula_de_entrada=1)

    assert quatro == 4
    assert not passou_do_limite(quatro)


def test_r08_quem_entrou_antes_da_10a_aula_e_faltou_a_2_tem_2_faltas() -> None:
    # As faltas lançadas antes da entrada não contam: as aulas anteriores valem como presença.
    lancadas = ausencias(ANA, 3, 5, 11, 12)

    assert faltas(lancadas, AULAS, aula_de_entrada=10) == 2


def test_r08_7_faltas_passam_do_limite_de_6() -> None:
    assert passou_do_limite(faltas(ausencias(ANA, 1, 2, 3, 4, 5, 6, 7), AULAS, 1))
    assert not passou_do_limite(6)


def test_r18_presenca_numa_data_fora_das_aulas_da_etapa_nao_conta() -> None:
    fora = [Presenca(ANA, date(2027, 4, 14), presente=False)]

    assert faltas(fora, AULAS, aula_de_entrada=1) == 0
