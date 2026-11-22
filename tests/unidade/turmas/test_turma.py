"""Turma (H30, H31, H10): nível inicial da matéria e horário fixo (R24), 12 vagas (R04), professor
sem conflito de horário (R07) e troca de professor (R26). No fim de cada etapa, a turma passa para
o nível seguinte (R04) e, depois do nível máximo, encerra (R09). Ninguém a encerra antes (R25)."""

from dataclasses import replace
from datetime import date, datetime, time, timedelta

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.turmas.domain.horario import DiaDaSemana, novo_horario
from plataforma.modules.turmas.domain.turma import (
    VAGAS_POR_TURMA,
    ConflitoDeHorario,
    Encerramento,
    HorarioFixo,
    MesmoProfessor,
    NivelForaDaMateria,
    PassagemDeEtapa,
    Turma,
    TurmaAberta,
    TurmaEncerrada,
    TurmaNova,
    com_a_mudanca,
    encerrar,
    exigir_aberta,
    exigir_nivel_da_materia,
    exigir_professor_livre,
    horarios_ocupados,
    mudancas_ate,
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


# A etapa do N2 da TURMA_DE_FISICA termina no fim da 24ª aula, na quinta 11/02/2027 às 20h30, e a
# do N3 começaria na terça 16/02, às 19h. Física tem 3 níveis.
FIM_DO_N2 = datetime(2027, 2, 11, 20, 30, tzinfo=BRASILIA)
TERCA_16_02_19H = datetime(2027, 2, 16, 19, 0, tzinfo=BRASILIA)


def test_r04_r26_no_fim_da_etapa_do_n2_a_turma_passa_para_o_n3_com_o_mesmo_professor() -> None:
    [passagem] = mudancas_ate(TURMA_DE_FISICA, nivel_maximo=3, agora=FIM_DO_N2)

    no_n3 = com_a_mudanca(TURMA_DE_FISICA, passagem)

    assert passagem.em == FIM_DO_N2
    assert (no_n3.nivel, no_n3.professor_id, no_n3.horario) == (3, CARLOS, TER_E_QUI_19H)


def test_r04_a_etapa_nova_comeca_a_partir_da_1a_aula_no_proximo_dia_da_turma() -> None:
    [passagem] = mudancas_ate(TURMA_DE_FISICA, nivel_maximo=3, agora=FIM_DO_N2)

    no_n3 = com_a_mudanca(TURMA_DE_FISICA, passagem)

    assert no_n3.inicio_da_etapa == TERCA_16_02_19H
    assert no_n3.aulas_dadas(FIM_DO_N2) == 0
    assert no_n3.nao_realizadas == frozenset()


def test_r17_antes_do_fim_da_24a_aula_a_turma_continua_na_etapa() -> None:
    assert mudancas_ate(TURMA_DE_FISICA, 3, FIM_DO_N2 - timedelta(minutes=1)) == []


def test_r09_no_fim_da_etapa_do_nivel_maximo_a_turma_encerra() -> None:
    no_n3 = replace(TURMA_DE_FISICA, nivel=3)

    [encerramento] = mudancas_ate(no_n3, nivel_maximo=3, agora=FIM_DO_N2)

    assert encerramento == Encerramento(FIM_DO_N2)
    assert com_a_mudanca(no_n3, encerramento).encerrada


def test_r04_r09_a_turma_passa_por_cada_etapa_que_terminou_e_encerra_no_nivel_maximo() -> None:
    um_ano_depois = datetime(2027, 11, 24, tzinfo=BRASILIA)

    mudancas = mudancas_ate(TURMA_DE_FISICA, nivel_maximo=3, agora=um_ano_depois)

    assert [type(mudanca) for mudanca in mudancas] == [PassagemDeEtapa, Encerramento]
    passagem, encerramento = mudancas
    assert isinstance(passagem, PassagemDeEtapa)
    assert encerramento.em == passagem.etapa.fim


def test_r09_a_turma_encerrada_nao_muda_mais() -> None:
    encerrada = replace(TURMA_DE_FISICA, nivel=3, encerrada_em=FIM_DO_N2)

    assert mudancas_ate(encerrada, 3, datetime(2028, 1, 1, tzinfo=BRASILIA)) == []


def test_r25_o_adm_nao_encerra_a_turma_aberta() -> None:
    with pytest.raises(
        TurmaAberta,
        match="A turma não pode ser encerrada: ela encerra sozinha no fim da etapa do N3, o "
        "nível máximo.",
    ):
        encerrar(TURMA_DE_FISICA, nivel_maximo=3)


def test_r25_a_turma_encerrada_nao_e_encerrada_de_novo() -> None:
    encerrada = replace(TURMA_DE_FISICA, nivel=3, encerrada_em=FIM_DO_N2)

    with pytest.raises(TurmaEncerrada, match="Esta turma já está encerrada."):
        encerrar(encerrada, nivel_maximo=3)


def test_r09_a_turma_encerrada_nao_recebe_matricula_nem_lista_de_espera() -> None:
    encerrada = replace(TURMA_DE_FISICA, nivel=3, encerrada_em=FIM_DO_N2)

    with pytest.raises(
        TurmaEncerrada, match="Esta turma foi encerrada: ela concluiu o nível máximo da matéria."
    ):
        exigir_aberta(encerrada)
    exigir_aberta(TURMA_DE_FISICA)


def test_r07_a_turma_encerrada_nao_ocupa_mais_o_horario() -> None:
    encerrada = replace(TURMA_DE_FISICA, id=2, encerrada_em=FIM_DO_N2)
    quarta_19h = novo_horario([DiaDaSemana.QUARTA], time(19), time(20, 30))
    aberta = replace(TURMA_DE_FISICA, id=3, horario=quarta_19h)

    assert horarios_ocupados([encerrada, aberta]) == [quarta_19h]
