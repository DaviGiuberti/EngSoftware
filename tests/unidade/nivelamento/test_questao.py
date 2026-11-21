"""Questões do nivelamento (H28): 5 alternativas e uma só correta (R41)."""

import pytest

from plataforma.modules.nivelamento.domain.questao import (
    AlternativasIncompletas,
    EnunciadoVazio,
    NivelamentoIndisponivel,
    Questao,
    QuestaoParaResponder,
    SemAlternativaCorreta,
    exigir_questoes,
    nova_questao,
    para_responder,
)

ENUNCIADO = "Um carro anda 100 m em 25 s. Qual é a velocidade média?"
ALTERNATIVAS = ["2 m/s", "4 m/s", "6 m/s", "8 m/s", "10 m/s"]


def test_r41_questao_com_5_alternativas_e_a_correta_marcada_e_aceita() -> None:
    questao = nova_questao(ENUNCIADO, ALTERNATIVAS, indice_da_correta=1)

    assert questao.enunciado == ENUNCIADO
    assert [alternativa.texto for alternativa in questao.alternativas] == ALTERNATIVAS
    assert [alternativa.correta for alternativa in questao.alternativas] == [
        False,
        True,
        False,
        False,
        False,
    ]


def test_r41_questao_com_4_alternativas_e_recusada() -> None:
    with pytest.raises(
        AlternativasIncompletas, match="A questão precisa ter 5 alternativas, de A a E."
    ):
        nova_questao(ENUNCIADO, ALTERNATIVAS[:4], indice_da_correta=1)


def test_r41_alternativa_em_branco_conta_como_faltando() -> None:
    with pytest.raises(AlternativasIncompletas):
        nova_questao(ENUNCIADO, [*ALTERNATIVAS[:4], "   "], indice_da_correta=1)


@pytest.mark.parametrize("indice_da_correta", [None, -1, 5])
def test_r41_questao_sem_uma_alternativa_correta_marcada_e_recusada(
    indice_da_correta: int | None,
) -> None:
    with pytest.raises(SemAlternativaCorreta, match="Marque qual alternativa é a correta."):
        nova_questao(ENUNCIADO, ALTERNATIVAS, indice_da_correta=indice_da_correta)


def test_questao_sem_enunciado_e_recusada() -> None:
    with pytest.raises(EnunciadoVazio, match="Escreva o enunciado da questão."):
        nova_questao("   ", ALTERNATIVAS, indice_da_correta=1)


def test_textos_sao_guardados_sem_espacos_nas_pontas() -> None:
    questao = nova_questao(f"  {ENUNCIADO} ", [f" {texto} " for texto in ALTERNATIVAS], 1)

    assert questao.enunciado == ENUNCIADO
    assert [alternativa.texto for alternativa in questao.alternativas] == ALTERNATIVAS


def test_a_letra_da_alternativa_correta_vai_de_a_a_e() -> None:
    alternativas = nova_questao(ENUNCIADO, ALTERNATIVAS, indice_da_correta=4).alternativas

    questao = Questao(id=1, materia_id=1, enunciado=ENUNCIADO, alternativas=alternativas)

    assert questao.letra_da_correta == "E"


def test_a_posicao_da_alternativa_correta_vai_de_0_a_4() -> None:
    alternativas = nova_questao(ENUNCIADO, ALTERNATIVAS, indice_da_correta=4).alternativas

    questao = Questao(id=1, materia_id=1, enunciado=ENUNCIADO, alternativas=alternativas)

    assert questao.posicao_da_correta == 4


def test_o_aluno_recebe_a_questao_sem_saber_qual_e_a_correta() -> None:
    alternativas = nova_questao(ENUNCIADO, ALTERNATIVAS, indice_da_correta=1).alternativas
    questao = Questao(id=7, materia_id=1, enunciado=ENUNCIADO, alternativas=alternativas)

    assert para_responder(questao) == QuestaoParaResponder(
        id=7, enunciado=ENUNCIADO, alternativas=tuple(ALTERNATIVAS)
    )


def test_materia_sem_questoes_recusa_o_nivelamento() -> None:
    with pytest.raises(
        NivelamentoIndisponivel, match="O nivelamento de Física ainda não está disponível."
    ):
        exigir_questoes("Física", quantidade_de_questoes=0)


def test_materia_com_questoes_libera_o_nivelamento() -> None:
    exigir_questoes("Física", quantidade_de_questoes=1)
