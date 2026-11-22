"""Reembolso de pacote (H17): pedido até as 23h59 do 7º dia depois da compra, sem condição sobre o
quanto foi assistido (R13). Ele encerra o acesso na hora (R12, R63), e a compra feita depois de um
reembolso do mesmo pacote não tem direito a reembolso (R13)."""

from dataclasses import replace
from datetime import datetime

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.vendas.domain.compra import (
    Compra,
    JaReembolsada,
    PrazoDoReembolso,
    SemDireitoAReembolso,
    acesso,
    nova_compra,
    prazo_do_reembolso,
    reembolsar,
)

ANA = 2
CINEMATICA = 5


def em(dia: int, mes: int, hora: int = 15, minuto: int = 0) -> datetime:
    return datetime(2027, mes, dia, hora, minuto, tzinfo=BRASILIA)


COMPRA_EM_10_03 = Compra(1, ANA, CINEMATICA, 12000, em(10, 3))


def test_r13_o_prazo_termina_na_virada_para_o_8o_dia() -> None:
    assert prazo_do_reembolso(COMPRA_EM_10_03) == em(18, 3, 0)


def test_r13_pedido_no_ultimo_minuto_do_7o_dia_e_aceito() -> None:
    reembolsada = reembolsar(COMPRA_EM_10_03, em(17, 3, 23, 59))

    assert reembolsada == replace(COMPRA_EM_10_03, reembolsada_em=em(17, 3, 23, 59))


def test_r13_pedido_depois_do_7o_dia_e_recusado() -> None:
    with pytest.raises(
        PrazoDoReembolso,
        match="O reembolso só pode ser pedido até as 23h59 de 17/03/2027, o 7º dia depois da "
        "compra.",
    ):
        reembolsar(COMPRA_EM_10_03, em(18, 3, 0))


def test_r12_r63_o_reembolso_encerra_o_acesso() -> None:
    reembolsada = reembolsar(COMPRA_EM_10_03, em(12, 3))

    assert acesso(reembolsada, em(12, 3)) is None
    assert acesso(COMPRA_EM_10_03, em(12, 3)) is not None


def test_r13_r63_o_reembolsado_pode_comprar_de_novo_mas_sem_direito_a_reembolso() -> None:
    reembolsada = reembolsar(COMPRA_EM_10_03, em(12, 3))

    nova = nova_compra(ANA, CINEMATICA, 12000, True, anteriores=[reembolsada], agora=em(20, 3))

    assert not nova.com_direito_a_reembolso


def test_r13_compra_sem_reembolso_antes_tem_direito_a_reembolso() -> None:
    nova = nova_compra(ANA, CINEMATICA, 12000, True, anteriores=[], agora=em(10, 3))

    assert nova.com_direito_a_reembolso


def test_r13_recompra_sem_direito_a_reembolso_e_recusada() -> None:
    recompra = Compra(2, ANA, CINEMATICA, 12000, em(20, 3), com_direito_a_reembolso=False)

    with pytest.raises(
        SemDireitoAReembolso,
        match="Esta compra foi feita depois de um reembolso do mesmo pacote e não dá direito a "
        "reembolso.",
    ):
        reembolsar(recompra, em(21, 3))


def test_a_compra_nao_e_reembolsada_duas_vezes() -> None:
    reembolsada = reembolsar(COMPRA_EM_10_03, em(12, 3))

    with pytest.raises(JaReembolsada, match="Esta compra já foi reembolsada em 12/03/2027."):
        reembolsar(reembolsada, em(13, 3))
