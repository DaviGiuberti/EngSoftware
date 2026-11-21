"""Valores em reais na tela, a partir dos centavos guardados no banco."""

import pytest

from plataforma.compartilhado.dinheiro import formatar_reais


@pytest.mark.parametrize(
    ("centavos", "texto"),
    [(20000, "R$ 200,00"), (25050, "R$ 250,50"), (5, "R$ 0,05"), (123456789, "R$ 1.234.567,89")],
)
def test_centavos_viram_reais_com_virgula_e_ponto_de_milhar(centavos: int, texto: str) -> None:
    assert formatar_reais(centavos) == texto
