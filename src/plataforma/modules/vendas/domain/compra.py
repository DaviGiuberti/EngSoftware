"""Compra de pacote (H15): só o pacote publicado é vendido, pelo preço do momento (R15, R59). A
compra libera o acesso por 12 meses, até as 23h59 do dia, ou do último dia do mês que não tem o
dia da compra (R12, R60). Com acesso ativo, o aluno não compra o mesmo pacote de novo (R12).

O pagamento é simulado e conta na hora (ADR 0003).
"""

import calendar
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.catalogo.domain.aulas_do_aluno import AcessoAoPacote

MESES_DE_ACESSO = 12


class ForaDeVenda(Recusa):
    mensagem = "Este pacote não está à venda."


class AcessoAtivo(Recusa):
    """R12: a mensagem diz até quando vai o acesso que o aluno já tem."""


@dataclass(frozen=True)
class CompraNova:
    """Compra conferida e pronta para gravar."""

    aluno_id: int
    pacote_id: int
    valor_em_centavos: int
    comprada_em: datetime


@dataclass(frozen=True)
class Compra:
    id: int
    aluno_id: int
    pacote_id: int
    valor_em_centavos: int
    comprada_em: datetime


def acesso_ate(comprada_em: datetime) -> date:
    """R12 e R60: o último dia do acesso, 12 meses depois da compra. No mês que não tem o dia da
    compra, é o último dia dele."""
    dia = comprada_em.date()
    meses_desde_janeiro = dia.month - 1 + MESES_DE_ACESSO
    ano = dia.year + meses_desde_janeiro // 12
    mes = meses_desde_janeiro % 12 + 1
    return date(ano, mes, min(dia.day, calendar.monthrange(ano, mes)[1]))


def acesso(compra: Compra, agora: datetime) -> AcessoAoPacote:
    """R60: o acesso vale até as 23h59 do último dia e vence na virada para o dia seguinte."""
    ate = acesso_ate(compra.comprada_em)
    return AcessoAoPacote(ate, agora.date() <= ate)


def nova_compra(
    aluno_id: int,
    pacote_id: int,
    preco_em_centavos: int,
    publicado: bool,
    anteriores: Iterable[Compra],
    agora: datetime,
) -> CompraNova:
    """R15: só o publicado é vendido, pelo preço que tem agora (R59). R12: com acesso ativo ao
    mesmo pacote, a compra é recusada. anteriores são as compras do aluno nesse pacote."""
    if not publicado:
        raise ForaDeVenda()
    for anterior in anteriores:
        atual = acesso(anterior, agora)
        if atual.ativo:
            raise AcessoAtivo(f"Você já tem acesso a este pacote até {atual.ate:%d/%m/%Y}.")
    return CompraNova(aluno_id, pacote_id, preco_em_centavos, agora)
