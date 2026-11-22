"""Promoção (H09, H32): aprovado na etapa, o aluno sobe exatamente um nível, sem pular (R08, R09).
No nível máximo, ele continua nele e conclui a trilha (R09). O nível nunca desce (R22)."""

from datetime import datetime

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.nivelamento.domain.promocao import (
    Promocao,
    conclui_a_trilha,
    promover,
)

FISICA = 1
# R49: a nota lançada em 10/03 às 10h passa a valer em 13/03 às 10h.
EM_13_03_AS_10H = datetime(2027, 3, 13, 10, 0, tzinfo=BRASILIA)


def test_r08_aprovado_na_etapa_do_n2_sobe_para_o_n3() -> None:
    promocao = promover(FISICA, nivel_atual=2, nivel_da_etapa=2, nivel_maximo=3, em=EM_13_03_AS_10H)

    assert promocao == Promocao(FISICA, nivel_anterior=2, nivel_novo=3, em=EM_13_03_AS_10H)


def test_r09_aprovado_no_n1_sobe_para_o_n2_e_nao_para_o_n3() -> None:
    promocao = promover(FISICA, nivel_atual=1, nivel_da_etapa=1, nivel_maximo=3, em=EM_13_03_AS_10H)

    assert promocao is not None
    assert promocao.nivel_novo == 2


def test_r09_aprovado_no_nivel_maximo_continua_nele_e_conclui_a_trilha() -> None:
    promocao = promover(FISICA, nivel_atual=3, nivel_da_etapa=3, nivel_maximo=3, em=EM_13_03_AS_10H)

    assert promocao is None
    assert conclui_a_trilha(nivel_da_etapa=3, nivel_maximo=3)


def test_r09_aprovacao_abaixo_do_nivel_maximo_nao_conclui_a_trilha() -> None:
    assert not conclui_a_trilha(nivel_da_etapa=2, nivel_maximo=3)


def test_r22_r52_quem_ja_subiu_e_aprovado_de_novo_no_nivel_anterior_nao_muda_de_nivel() -> None:
    # Ana subiu para o N3 pela correção do ADM e continuou noutra turma do N2 (R52).
    promocao = promover(FISICA, nivel_atual=3, nivel_da_etapa=2, nivel_maximo=3, em=EM_13_03_AS_10H)

    assert promocao is None


def test_r09_quem_ainda_esta_no_n2_e_e_aprovado_na_etapa_do_n3_sobe_so_um_nivel() -> None:
    # A nota do N2 não saiu, e o aluno seguiu com a turma na etapa do N3 (R23).
    promocao = promover(1, nivel_atual=2, nivel_da_etapa=3, nivel_maximo=5, em=EM_13_03_AS_10H)

    assert promocao == Promocao(1, nivel_anterior=2, nivel_novo=3, em=EM_13_03_AS_10H)
