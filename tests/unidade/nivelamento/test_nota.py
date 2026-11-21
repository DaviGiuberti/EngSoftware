"""Nota do nivelamento (H01, H28): porcentagem de acertos, arredondada para baixo, em que a
questão sem resposta conta como erro (R34)."""

import pytest

from plataforma.modules.materias.domain.materia import montar_faixas, nivel_da_nota
from plataforma.modules.nivelamento.domain.nota import calcular_nota, corrigir
from plataforma.modules.nivelamento.domain.questao import Questao, nova_questao

FISICA = montar_faixas([40, 70])
CORRETA_NA_B = nova_questao("Enunciado?", ["A", "B", "C", "D", "E"], 1).alternativas


def questoes(quantidade: int) -> list[Questao]:
    """Questões numeradas de 1 em diante, todas com a correta na alternativa B."""
    return [
        Questao(id=numero, materia_id=1, enunciado=f"Questão {numero}?", alternativas=CORRETA_NA_B)
        for numero in range(1, quantidade + 1)
    ]


def test_r02_8_acertos_em_20_questoes_dao_nota_40_e_o_n2_de_fisica() -> None:
    nota = calcular_nota(acertos=8, total_de_questoes=20)

    assert nota == 40
    assert nivel_da_nota(FISICA, nota) == 2


def test_r34_a_nota_e_arredondada_para_baixo() -> None:
    assert calcular_nota(acertos=2, total_de_questoes=3) == 66


def test_r34_39_9_por_cento_vira_39() -> None:
    assert calcular_nota(acertos=399, total_de_questoes=1000) == 39


def test_r34_nenhum_acerto_da_nota_0() -> None:
    assert calcular_nota(acertos=0, total_de_questoes=30) == 0


def test_r34_18_de_30_respondidas_com_o_tempo_acabado_dao_60_por_cento_e_o_n2() -> None:
    trinta = questoes(30)
    respostas = {questao.id: 1 for questao in trinta[:18]}

    nota = corrigir(trinta, respostas)

    # Se as 12 questões sem resposta não contassem como erro, a nota seria 100.
    assert nota == 60
    assert nivel_da_nota(FISICA, nota) == 2


def test_r34_resposta_errada_conta_como_erro() -> None:
    assert corrigir(questoes(3), {1: 1, 2: 0, 3: 4}) == 33


@pytest.mark.parametrize(("acertos", "nivel"), [(39, 1), (40, 2)])
def test_r02_39_por_cento_coloca_o_aluno_no_n1_e_40_no_n2(acertos: int, nivel: int) -> None:
    cem = questoes(100)
    respostas = {questao.id: 1 for questao in cem[:acertos]}

    assert nivel_da_nota(FISICA, corrigir(cem, respostas)) == nivel
