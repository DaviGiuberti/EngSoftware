"""Nota do nivelamento (R34)."""


def calcular_nota(acertos: int, total_de_questoes: int) -> int:
    """Porcentagem de acertos sobre o total de questões, arredondada para baixo (R34).

    A divisão inteira arredonda para baixo: 399 acertos em 1000 dão 39, e não 40.
    """
    return acertos * 100 // total_de_questoes
