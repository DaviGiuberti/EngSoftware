"""Ponto único por onde as telas chamam os casos de uso.

Grava o resultado de cada ação no log (RNF14) e devolve à tela o que mostrar: o motivo da
recusa (RNF02) ou, num erro inesperado, uma mensagem curta, com o detalhe só no log (RNF10).
"""

from collections.abc import Callable
from dataclasses import dataclass

from plataforma.compartilhado.recusa import Recusa
from plataforma.log import registrar_acao, registrar_erro

MENSAGEM_DE_ERRO_INESPERADO = (
    "Ocorreu um erro inesperado. Tente de novo e, se continuar, avise o ADM."
)


@dataclass(frozen=True)
class Feito[T]:
    valor: T


@dataclass(frozen=True)
class Falhou:
    mensagem: str


def executar[T](acao: str, usuario: str | None, funcao: Callable[[], T]) -> Feito[T] | Falhou:
    """Roda a ação de uma tela. usuario é o e-mail de quem age, ou None antes do login."""
    try:
        valor = funcao()
    except Recusa as recusa:
        registrar_acao(acao, usuario, "recusado", motivo=str(recusa))
        return Falhou(str(recusa))
    except Exception:
        registrar_erro(acao, usuario)
        return Falhou(MENSAGEM_DE_ERRO_INESPERADO)
    registrar_acao(acao, usuario, "ok")
    return Feito(valor)
