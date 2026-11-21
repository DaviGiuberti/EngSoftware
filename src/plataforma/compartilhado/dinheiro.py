"""Valores em dinheiro. O banco guarda centavos inteiros, e a tela mostra reais."""


def formatar_reais(centavos: int) -> str:
    """20000 vira "R$ 200,00", e 123456789 vira "R$ 1.234.567,89"."""
    reais, resto = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{resto:02d}"
