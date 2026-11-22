"""Compra de pacote (H15): só o pacote publicado é vendido, pelo preço do momento (R15, R59), e
libera o acesso por 12 meses, até as 23h59 do dia (R12, R60). Com acesso ativo, o aluno não compra
o mesmo pacote de novo (R12)."""

from datetime import date, datetime

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.vendas.domain.compra import (
    AcessoAtivo,
    Compra,
    CompraNova,
    ForaDeVenda,
    acesso,
    acesso_ate,
    nova_compra,
)

ANA = 2
CINEMATICA = 5


def em(dia: int, mes: int, ano: int, hora: int = 15, minuto: int = 0) -> datetime:
    return datetime(ano, mes, dia, hora, minuto, tzinfo=BRASILIA)


COMPRA_EM_10_03_2027 = Compra(1, ANA, CINEMATICA, 12000, em(10, 3, 2027))


def test_r12_r31_compra_em_10_03_2027_da_acesso_ate_10_03_2028() -> None:
    nova = nova_compra(ANA, CINEMATICA, 12000, publicado=True, anteriores=[], agora=em(10, 3, 2027))

    assert nova == CompraNova(ANA, CINEMATICA, 12000, em(10, 3, 2027))
    assert acesso_ate(nova.comprada_em) == date(2028, 3, 10)


def test_r60_compra_em_29_02_2028_da_acesso_ate_28_02_2029() -> None:
    assert acesso_ate(em(29, 2, 2028)) == date(2029, 2, 28)


def test_r60_o_acesso_vale_ate_as_23h59_do_ultimo_dia() -> None:
    assert acesso(COMPRA_EM_10_03_2027, em(10, 3, 2028, 23, 59)).ativo
    assert not acesso(COMPRA_EM_10_03_2027, em(11, 3, 2028, 0, 0)).ativo
    assert acesso(COMPRA_EM_10_03_2027, em(11, 3, 2028)).ate == date(2028, 3, 10)


def test_r12_compra_bloqueada_com_acesso_ativo() -> None:
    with pytest.raises(AcessoAtivo, match="Você já tem acesso a este pacote até 10/03/2028."):
        nova_compra(
            ANA, CINEMATICA, 12000, True, anteriores=[COMPRA_EM_10_03_2027], agora=em(10, 3, 2028)
        )


def test_r12_nova_compra_depois_que_o_acesso_vence() -> None:
    nova = nova_compra(
        ANA, CINEMATICA, 12000, True, anteriores=[COMPRA_EM_10_03_2027], agora=em(15, 3, 2028)
    )

    assert acesso_ate(nova.comprada_em) == date(2029, 3, 15)


def test_r15_pacote_que_nao_esta_publicado_nao_e_vendido() -> None:
    with pytest.raises(ForaDeVenda, match="Este pacote não está à venda."):
        nova_compra(ANA, CINEMATICA, 12000, publicado=False, anteriores=[], agora=em(10, 3, 2027))


def test_r59_a_compra_guarda_o_preco_do_momento() -> None:
    assert nova_compra(ANA, CINEMATICA, 10000, True, [], em(10, 3, 2027)).valor_em_centavos == (
        10000
    )
