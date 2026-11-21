"""RNF06: senha com no mínimo 8 caracteres, guardada só como hash com sal (H38)."""

import pytest

from plataforma.modules.identidade.domain.senha import (
    SenhaCurta,
    gerar_hash,
    senha_confere,
    validar_senha,
)

SAL = bytes(16)
OUTRO_SAL = bytes(range(16))


def test_rnf06_senha_com_7_caracteres_e_recusada() -> None:
    with pytest.raises(SenhaCurta, match="A senha precisa ter pelo menos 8 caracteres."):
        validar_senha("abc1234")


def test_rnf06_senha_com_8_caracteres_e_aceita() -> None:
    validar_senha("abcd1234")


def test_rnf06_valor_guardado_e_diferente_da_senha() -> None:
    valor_guardado = gerar_hash("abcd1234", SAL)

    assert valor_guardado != "abcd1234"
    assert "abcd1234" not in valor_guardado


def test_rnf06_a_mesma_senha_com_sais_diferentes_da_valores_diferentes() -> None:
    assert gerar_hash("abcd1234", SAL) != gerar_hash("abcd1234", OUTRO_SAL)


def test_rnf06_a_senha_confere_com_o_proprio_hash() -> None:
    assert senha_confere("abcd1234", gerar_hash("abcd1234", SAL))


def test_rnf06_outra_senha_nao_confere() -> None:
    assert not senha_confere("abcd9999", gerar_hash("abcd1234", SAL))
