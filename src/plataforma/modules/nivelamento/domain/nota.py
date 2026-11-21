"""Nota do nivelamento (R34)."""

from collections.abc import Mapping, Sequence

from plataforma.modules.nivelamento.domain.questao import Questao


def calcular_nota(acertos: int, total_de_questoes: int) -> int:
    """Porcentagem de acertos sobre o total de questões, arredondada para baixo (R34).

    A divisão inteira arredonda para baixo: 399 acertos em 1000 dão 39, e não 40.
    """
    return acertos * 100 // total_de_questoes


def corrigir(questoes: Sequence[Questao], respostas: Mapping[int, int]) -> int:
    """A nota sobre todas as questões do nivelamento. A questão sem resposta conta como erro.

    respostas leva o id da questão à posição da alternativa marcada (0 é a A).
    """
    acertos = sum(
        1 for questao in questoes if respostas.get(questao.id) == questao.posicao_da_correta
    )
    return calcular_nota(acertos, len(questoes))
