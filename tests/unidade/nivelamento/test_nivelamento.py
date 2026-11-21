"""Nivelamento (H01, H02, H03, H33): uma vez por matéria (R03), 60 minutos que só correm com o
teste aberto (R30) e o resultado do nivelamento refeito (R42)."""

from datetime import datetime, timedelta

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.nivelamento.domain.nivelamento import (
    Conclusao,
    NadaParaRefazer,
    Nivelamento,
    NivelamentoConcluido,
    NivelamentoEmAndamento,
    NivelamentoJaFeito,
    QuestaoForaDoNivelamento,
    SemNivelamentoEmAndamento,
    SituacaoNaMateria,
    TempoDoNivelamento,
    TempoExtraInvalido,
    abrir,
    acabou,
    com_mais_tempo,
    concluir,
    exigir_em_andamento,
    exigir_que_pode_iniciar,
    exigir_que_pode_liberar,
    fechar,
    nivel_depois_do_nivelamento,
    registrar,
    responder,
    restante,
    situacao_na_materia,
)

INICIO = datetime(2026, 11, 23, 14, 0, tzinfo=BRASILIA)


def minutos(quantidade: int) -> timedelta:
    return timedelta(minutes=quantidade)


def aberto_em(momento: datetime, usado: timedelta = timedelta(0)) -> TempoDoNivelamento:
    return abrir(TempoDoNivelamento(usado=usado), momento)


def nivelamento_aberto() -> Nivelamento:
    return Nivelamento(id=1, aluno_id=10, materia_id=1, tempo=aberto_em(INICIO))


def test_r30_o_nivelamento_tem_60_minutos() -> None:
    assert restante(aberto_em(INICIO), INICIO) == minutos(60)


def test_r30_o_tempo_corre_com_o_teste_aberto() -> None:
    assert restante(aberto_em(INICIO), INICIO + minutos(10)) == minutos(50)


def test_r30_fechado_com_25_minutos_usados_e_reaberto_dois_dias_depois_tem_35() -> None:
    fechado = fechar(aberto_em(INICIO), INICIO + minutos(25))
    dois_dias_depois = INICIO + timedelta(days=2)

    reaberto = abrir(fechado, dois_dias_depois)

    assert restante(reaberto, dois_dias_depois) == minutos(35)


def test_r30_com_o_teste_fechado_o_tempo_nao_corre() -> None:
    fechado = fechar(aberto_em(INICIO), INICIO + minutos(25))

    assert restante(fechado, INICIO + timedelta(days=2)) == minutos(35)


def test_r30_se_o_app_cai_o_tempo_depois_do_ultimo_registro_nao_conta() -> None:
    registrado = registrar(aberto_em(INICIO), INICIO + minutos(20))
    um_dia_depois = INICIO + timedelta(days=1)

    reaberto = abrir(registrado, um_dia_depois)

    assert restante(reaberto, um_dia_depois) == minutos(40)


def test_r30_o_tempo_acaba_aos_60_minutos_e_o_restante_nao_fica_negativo() -> None:
    tempo = aberto_em(INICIO)

    assert not acabou(tempo, INICIO + timedelta(minutes=59, seconds=59))
    assert acabou(tempo, INICIO + minutos(60))
    assert restante(tempo, INICIO + minutos(90)) == timedelta(0)


def test_r30_relogio_que_volta_no_tempo_nao_devolve_minutos() -> None:
    tempo = aberto_em(INICIO, usado=minutos(10))

    assert restante(tempo, INICIO - timedelta(hours=1)) == minutos(50)


def test_r30_o_adm_da_20_minutos_a_quem_tem_5_restantes_e_ele_fica_com_25() -> None:
    tempo = aberto_em(INICIO, usado=minutos(55))
    assert restante(tempo, INICIO) == minutos(5)

    assert restante(com_mais_tempo(tempo, 20), INICIO) == minutos(25)


@pytest.mark.parametrize("minutos_a_mais", [0, -5])
def test_r30_mais_tempo_precisa_ser_de_pelo_menos_1_minuto(minutos_a_mais: int) -> None:
    with pytest.raises(
        TempoExtraInvalido, match="Informe quantos minutos a mais, de 1 em diante."
    ):
        com_mais_tempo(aberto_em(INICIO), minutos_a_mais)


def test_r30_so_ganha_mais_tempo_quem_esta_fazendo_o_nivelamento() -> None:
    with pytest.raises(
        SemNivelamentoEmAndamento, match="Este aluno não está fazendo o nivelamento de Física."
    ):
        exigir_em_andamento("Física", em_andamento=False)

    exigir_em_andamento("Física", em_andamento=True)


def test_r03_quem_ja_tem_nivel_na_materia_nao_faz_o_nivelamento_de_novo() -> None:
    with pytest.raises(NivelamentoJaFeito, match="O nivelamento de Física já foi feito."):
        exigir_que_pode_iniciar("Física", tem_nivel=True, refazer_liberado=False)


def test_r03_quem_nao_tem_nivel_na_materia_faz_o_nivelamento() -> None:
    exigir_que_pode_iniciar("Física", tem_nivel=False, refazer_liberado=False)


def test_r03_com_a_liberacao_do_adm_quem_tem_nivel_refaz() -> None:
    exigir_que_pode_iniciar("Física", tem_nivel=True, refazer_liberado=True)


def test_r03_o_adm_so_libera_refazer_para_quem_ja_tem_nivel() -> None:
    with pytest.raises(
        NadaParaRefazer, match="Este aluno ainda não fez o nivelamento de Física."
    ):
        exigir_que_pode_liberar("Física", tem_nivel=False, em_andamento=False)


def test_r03_o_adm_libera_refazer_para_quem_tem_nivel_e_nao_esta_fazendo_o_teste() -> None:
    exigir_que_pode_liberar("Física", tem_nivel=True, em_andamento=False)


def test_r03_o_adm_nao_libera_refazer_durante_um_nivelamento_em_andamento() -> None:
    with pytest.raises(
        NivelamentoEmAndamento, match="Este aluno está fazendo o nivelamento de Física agora."
    ):
        exigir_que_pode_liberar("Física", tem_nivel=True, em_andamento=True)


def test_o_aluno_marca_e_troca_a_resposta_de_uma_questao() -> None:
    respondido = responder(nivelamento_aberto(), {7, 8}, questao_id=7, posicao=1)

    trocado = responder(respondido, {7, 8}, questao_id=7, posicao=3)

    assert trocado.respostas == {7: 3}


def test_questao_de_fora_do_nivelamento_e_recusada() -> None:
    with pytest.raises(QuestaoForaDoNivelamento, match="Esta questão não é deste nivelamento."):
        responder(nivelamento_aberto(), {7, 8}, questao_id=99, posicao=1)


def test_posicao_fora_de_a_a_e_e_erro_de_programacao() -> None:
    with pytest.raises(ValueError, match="5"):
        responder(nivelamento_aberto(), {7}, questao_id=7, posicao=5)


def test_concluir_para_o_tempo_e_guarda_a_nota_e_o_nivel() -> None:
    meia_hora_depois = INICIO + minutos(30)

    concluido = concluir(nivelamento_aberto(), meia_hora_depois, nota=40, nivel=2)

    assert concluido.conclusao == Conclusao(em=meia_hora_depois, nota=40, nivel=2)
    assert concluido.tempo.aberto_desde is None
    assert concluido.tempo.usado == minutos(30)


def test_nivelamento_concluido_nao_recebe_mais_respostas() -> None:
    concluido = concluir(nivelamento_aberto(), INICIO + minutos(30), nota=40, nivel=2)

    with pytest.raises(NivelamentoConcluido, match="Este nivelamento já terminou."):
        responder(concluido, {7}, questao_id=7, posicao=1)


def test_o_primeiro_nivelamento_define_o_nivel() -> None:
    assert nivel_depois_do_nivelamento(nivel_atual=None, nivel_da_nota=2) == 2


def test_r42_nivelamento_refeito_com_resultado_maior_sobe_o_nivel() -> None:
    assert nivel_depois_do_nivelamento(nivel_atual=1, nivel_da_nota=3) == 3


def test_r42_nivelamento_refeito_com_resultado_menor_mantem_o_nivel() -> None:
    assert nivel_depois_do_nivelamento(nivel_atual=2, nivel_da_nota=1) == 2


@pytest.mark.parametrize(
    ("nivel", "refazer_liberado", "em_andamento", "questoes", "situacao"),
    [
        (None, False, False, 10, SituacaoNaMateria.SEM_NIVEL),
        (None, False, False, 0, SituacaoNaMateria.INDISPONIVEL),
        (None, False, True, 10, SituacaoNaMateria.EM_ANDAMENTO),
        (2, False, False, 10, SituacaoNaMateria.COM_NIVEL),
        (2, True, False, 10, SituacaoNaMateria.REFAZER_LIBERADO),
        (2, False, True, 10, SituacaoNaMateria.EM_ANDAMENTO),
    ],
)
def test_r01_r03_situacao_do_aluno_em_cada_materia(
    nivel: int | None,
    refazer_liberado: bool,
    em_andamento: bool,
    questoes: int,
    situacao: SituacaoNaMateria,
) -> None:
    assert situacao_na_materia(nivel, refazer_liberado, em_andamento, questoes) == situacao
