"""Turma (H30, H31): nível inicial da matéria e horário fixo (R24), 12 vagas (R04), professor sem
conflito de horário (R07) e troca de professor (R26)."""

from dataclasses import replace
from datetime import date, datetime, time

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.turmas.domain.horario import DiaDaSemana, novo_horario
from plataforma.modules.turmas.domain.turma import (
    VAGAS_POR_TURMA,
    ConflitoDeHorario,
    HorarioFixo,
    MesmoProfessor,
    NivelForaDaMateria,
    Turma,
    TurmaNova,
    exigir_nivel_da_materia,
    exigir_professor_livre,
    mudar_horario,
    nova_turma,
    trocar_professor,
)

FISICA = 1
CARLOS = 10
DORA = 11
TER, QUI = DiaDaSemana.TERCA, DiaDaSemana.QUINTA
TER_E_QUI_19H = novo_horario([TER, QUI], time(19), time(20, 30))
SEGUNDA_23_11_14H = datetime(2026, 11, 23, 14, 0, tzinfo=BRASILIA)
TERCA_24_11_19H = datetime(2026, 11, 24, 19, 0, tzinfo=BRASILIA)

TURMA_DE_FISICA = Turma(
    id=1,
    materia_id=FISICA,
    nivel=2,
    professor_id=CARLOS,
    horario=TER_E_QUI_19H,
    inicio_da_etapa=TERCA_24_11_19H,
)


def test_r24_r43_turma_nova_no_n2_com_a_1a_aula_no_primeiro_dia_dela() -> None:
    nova = nova_turma(FISICA, 2, CARLOS, TER_E_QUI_19H, SEGUNDA_23_11_14H)

    assert nova == TurmaNova(FISICA, 2, CARLOS, TER_E_QUI_19H, TERCA_24_11_19H)


def test_r04_a_turma_tem_12_vagas() -> None:
    assert VAGAS_POR_TURMA == 12


@pytest.mark.parametrize("nivel", [1, 3])
def test_r24_a_turma_comeca_em_qualquer_nivel_da_materia(nivel: int) -> None:
    exigir_nivel_da_materia(nivel, nivel_maximo=3, nome_da_materia="Física")


@pytest.mark.parametrize("nivel", [0, 4])
def test_r24_nivel_que_a_materia_nao_tem_e_recusado(nivel: int) -> None:
    with pytest.raises(NivelForaDaMateria, match="Física tem os níveis N1 a N3."):
        exigir_nivel_da_materia(nivel, nivel_maximo=3, nome_da_materia="Física")


def test_r24_materia_de_um_nivel_so_aceita_so_o_n1() -> None:
    with pytest.raises(NivelForaDaMateria, match="Química só tem o nível N1."):
        exigir_nivel_da_materia(2, nivel_maximo=1, nome_da_materia="Química")


def test_r07_carlos_com_turma_as_tercas_19h_nao_pega_outra_as_tercas_20h() -> None:
    terca_20h = novo_horario([TER], time(20), time(21, 30))

    with pytest.raises(
        ConflitoDeHorario,
        match="carlos@exemplo.com já dá aula numa turma às terças e quintas, das 19h às 20h30.",
    ):
        exigir_professor_livre("carlos@exemplo.com", terca_20h, [TER_E_QUI_19H])


def test_r07_professor_sem_turma_que_se_sobreponha_esta_livre() -> None:
    quarta_19h = novo_horario([DiaDaSemana.QUARTA], time(19), time(20, 30))

    exigir_professor_livre("carlos@exemplo.com", quarta_19h, [TER_E_QUI_19H])


def test_r24_o_adm_nao_muda_o_horario_da_turma_para_as_18h() -> None:
    as_18h = novo_horario([TER, QUI], time(18), time(19, 30))

    with pytest.raises(
        HorarioFixo,
        match="O horário da turma não muda: ela continua às terças e quintas, das 19h às 20h30.",
    ):
        mudar_horario(TURMA_DE_FISICA, as_18h)


def test_r24_pedir_o_horario_que_a_turma_ja_tem_nao_muda_nada() -> None:
    assert mudar_horario(TURMA_DE_FISICA, TER_E_QUI_19H) == TURMA_DE_FISICA


def test_r26_o_adm_troca_o_professor_e_o_nivel_e_o_horario_continuam() -> None:
    trocada = trocar_professor(TURMA_DE_FISICA, DORA, "dora@exemplo.com")

    assert trocada.professor_id == DORA
    assert (trocada.nivel, trocada.horario) == (2, TER_E_QUI_19H)


def test_r26_trocar_pelo_professor_que_ja_da_aula_na_turma_e_recusado() -> None:
    with pytest.raises(MesmoProfessor, match="carlos@exemplo.com já dá aula nesta turma."):
        trocar_professor(TURMA_DE_FISICA, CARLOS, "carlos@exemplo.com")


def test_r18_a_turma_nao_conta_entre_as_dadas_a_aula_nao_realizada() -> None:
    quinta_26_11 = date(2026, 11, 26)
    com_nao_realizada = replace(TURMA_DE_FISICA, nao_realizadas=frozenset({quinta_26_11}))
    sexta_27_11 = datetime(2026, 11, 27, 10, 0, tzinfo=BRASILIA)

    assert TURMA_DE_FISICA.aulas_dadas(sexta_27_11) == 2
    assert com_nao_realizada.aulas_dadas(sexta_27_11) == 1
    assert com_nao_realizada.calendario()[1].numero is None
