"""Nota do nivelamento (H28): porcentagem de acertos, arredondada para baixo (R34)."""

from plataforma.modules.materias.domain.materia import montar_faixas, nivel_da_nota
from plataforma.modules.nivelamento.domain.nota import calcular_nota


def test_r02_8_acertos_em_20_questoes_dao_nota_40_e_o_n2_de_fisica() -> None:
    nota = calcular_nota(acertos=8, total_de_questoes=20)

    assert nota == 40
    assert nivel_da_nota(montar_faixas([40, 70]), nota) == 2


def test_r34_a_nota_e_arredondada_para_baixo() -> None:
    assert calcular_nota(acertos=2, total_de_questoes=3) == 66


def test_r34_39_9_por_cento_vira_39() -> None:
    assert calcular_nota(acertos=399, total_de_questoes=1000) == 39


def test_r34_nenhum_acerto_da_nota_0() -> None:
    assert calcular_nota(acertos=0, total_de_questoes=30) == 0
