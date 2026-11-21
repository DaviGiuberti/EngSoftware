"""Matéria (H27): níveis (R01), faixas do nivelamento (R02, R40) e mensalidade (R27)."""

import pytest

from plataforma.modules.materias.domain.materia import (
    Faixa,
    FaixasInvalidas,
    MensalidadeInvalida,
    NomeJaCadastrado,
    NomeVazio,
    SemNiveis,
    exigir_nome_livre,
    montar_faixas,
    nivel_da_nota,
    nome_do_nivel,
    nova_materia,
)

FAIXAS_DE_FISICA = montar_faixas([40, 70])


def test_r01_matematica_cadastrada_com_5_niveis_tem_os_niveis_n1_a_n5() -> None:
    matematica = nova_materia("Matemática", 5, [20, 40, 60, 80], 25000)

    assert [nome_do_nivel(nivel) for nivel in matematica.niveis] == ["N1", "N2", "N3", "N4", "N5"]


def test_r01_materia_sem_nenhum_nivel_e_recusada() -> None:
    with pytest.raises(SemNiveis, match="A matéria precisa ter pelo menos 1 nível."):
        nova_materia("Física", 0, [], 20000)


def test_r40_as_faixas_cobrem_de_0_a_100_sem_buraco_nem_sobreposicao() -> None:
    faixas = montar_faixas([40, 70])

    assert faixas == (Faixa(1, 0, 39), Faixa(2, 40, 69), Faixa(3, 70, 100))


def test_r40_materia_com_1_nivel_tem_uma_faixa_de_0_a_100() -> None:
    assert montar_faixas([]) == (Faixa(1, 0, 100),)


def test_r40_nota_minima_fora_de_ordem_e_recusada() -> None:
    with pytest.raises(FaixasInvalidas, match="A nota mínima do N3 precisa ser maior que a do N2."):
        montar_faixas([70, 40])


def test_r40_nota_minima_igual_a_do_nivel_anterior_e_recusada() -> None:
    with pytest.raises(FaixasInvalidas, match="A nota mínima do N3 precisa ser maior que a do N2."):
        montar_faixas([40, 40])


@pytest.mark.parametrize("nota_minima", [0, 101])
def test_r40_nota_minima_fora_de_1_a_100_e_recusada(nota_minima: int) -> None:
    with pytest.raises(FaixasInvalidas, match="A nota mínima do N2 precisa estar entre 1% e 100%."):
        montar_faixas([nota_minima])


def test_r40_cada_nivel_a_partir_do_n2_precisa_de_nota_minima() -> None:
    with pytest.raises(
        FaixasInvalidas, match="Informe uma nota mínima para cada nível a partir do N2."
    ):
        nova_materia("Física", 3, [40], 20000)


def test_r02_matematica_com_45_por_cento_fica_no_n3() -> None:
    faixas_de_matematica = montar_faixas([20, 40, 60, 80])

    assert nivel_da_nota(faixas_de_matematica, 45) == 3


@pytest.mark.parametrize(
    ("nota", "nivel"), [(0, 1), (39, 1), (40, 2), (69, 2), (70, 3), (100, 3)]
)
def test_r02_limites_das_faixas_de_fisica(nota: int, nivel: int) -> None:
    assert nivel_da_nota(FAIXAS_DE_FISICA, nota) == nivel


def test_r02_nota_fora_de_0_a_100_e_erro_de_programacao() -> None:
    with pytest.raises(ValueError, match="101"):
        nivel_da_nota(FAIXAS_DE_FISICA, 101)


def test_r27_a_mensalidade_e_definida_na_materia() -> None:
    assert nova_materia("Física", 3, [40, 70], 20000).mensalidade_em_centavos == 20000


def test_r27_mensalidade_zero_e_recusada() -> None:
    with pytest.raises(MensalidadeInvalida, match="A mensalidade precisa ser maior que zero."):
        nova_materia("Física", 3, [40, 70], 0)


def test_nome_e_guardado_sem_espacos_nas_pontas() -> None:
    assert nova_materia("  Física ", 3, [40, 70], 20000).nome == "Física"


def test_nome_vazio_e_recusado() -> None:
    with pytest.raises(NomeVazio, match="Informe o nome da matéria."):
        nova_materia("   ", 3, [40, 70], 20000)


def test_nome_ja_cadastrado_com_outras_maiusculas_e_recusado() -> None:
    with pytest.raises(NomeJaCadastrado, match="Já existe uma matéria com esse nome."):
        exigir_nome_livre("FÍSICA", ["Física", "Matemática"])


def test_nome_novo_e_aceito() -> None:
    exigir_nome_livre("Química", ["Física", "Matemática"])
