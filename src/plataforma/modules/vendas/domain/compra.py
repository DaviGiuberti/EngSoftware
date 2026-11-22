"""Compra e reembolso de pacote (H15, H17): só o pacote publicado é vendido, pelo preço do
momento (R15, R59). A compra libera o acesso por 12 meses, até as 23h59 do dia, ou do último dia do
mês que não tem o dia da compra (R12, R60). Com acesso ativo, o aluno não compra o mesmo pacote de
novo (R12).

O reembolso é pedido até as 23h59 do 7º dia depois da compra, sem condição sobre o quanto foi
assistido, e encerra o acesso na hora (R13, R63). A compra feita depois de um reembolso do mesmo
pacote não tem direito a reembolso (R13).

O pagamento e o reembolso são simulados e contam na hora (ADR 0003).
"""

import calendar
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.catalogo.domain.aulas_do_aluno import AcessoAoPacote

MESES_DE_ACESSO = 12
# R13: o reembolso é pedido até as 23h59 do 7º dia depois da compra.
DIAS_PARA_O_REEMBOLSO = 7


class ForaDeVenda(Recusa):
    mensagem = "Este pacote não está à venda."


class AcessoAtivo(Recusa):
    """R12: a mensagem diz até quando vai o acesso que o aluno já tem."""


class PrazoDoReembolso(Recusa):
    """R13: a mensagem diz até quando o reembolso podia ser pedido."""


class SemDireitoAReembolso(Recusa):
    mensagem = (
        "Esta compra foi feita depois de um reembolso do mesmo pacote e não dá direito a "
        "reembolso."
    )


class SemCompra(Recusa):
    mensagem = "Você não comprou este pacote."


class JaReembolsada(Recusa):
    """A mensagem diz quando a compra foi reembolsada."""


@dataclass(frozen=True)
class CompraNova:
    """Compra conferida e pronta para gravar. Depois de um reembolso do mesmo pacote, a compra não
    tem direito a reembolso (R13)."""

    aluno_id: int
    pacote_id: int
    valor_em_centavos: int
    comprada_em: datetime
    com_direito_a_reembolso: bool = True


@dataclass(frozen=True)
class Compra:
    """reembolsada_em fica vazio até o reembolso ser aceito (R13)."""

    id: int
    aluno_id: int
    pacote_id: int
    valor_em_centavos: int
    comprada_em: datetime
    com_direito_a_reembolso: bool = True
    reembolsada_em: datetime | None = None


def acesso_ate(comprada_em: datetime) -> date:
    """R12 e R60: o último dia do acesso, 12 meses depois da compra. No mês que não tem o dia da
    compra, é o último dia dele."""
    dia = comprada_em.date()
    meses_desde_janeiro = dia.month - 1 + MESES_DE_ACESSO
    ano = dia.year + meses_desde_janeiro // 12
    mes = meses_desde_janeiro % 12 + 1
    return date(ano, mes, min(dia.day, calendar.monthrange(ano, mes)[1]))


def acesso(compra: Compra, agora: datetime) -> AcessoAoPacote | None:
    """R60: o acesso vale até as 23h59 do último dia e vence na virada para o dia seguinte. R63: a
    compra reembolsada não dá acesso nenhum."""
    if compra.reembolsada_em is not None:
        return None
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
    mesmo pacote, a compra é recusada. R13: depois de um reembolso do mesmo pacote, a compra não tem
    direito a reembolso. anteriores são as compras do aluno nesse pacote."""
    if not publicado:
        raise ForaDeVenda()
    anteriores = list(anteriores)
    for anterior in anteriores:
        atual = acesso(anterior, agora)
        if atual is not None and atual.ativo:
            raise AcessoAtivo(f"Você já tem acesso a este pacote até {atual.ate:%d/%m/%Y}.")
    ja_reembolsado = any(anterior.reembolsada_em is not None for anterior in anteriores)
    return CompraNova(aluno_id, pacote_id, preco_em_centavos, agora, not ja_reembolsado)


def prazo_do_reembolso(compra: Compra) -> datetime:
    """R13: o reembolso pode ser pedido até as 23h59 do 7º dia depois da compra, ou seja, até antes
    da 0h do 8º dia."""
    oitavo_dia = compra.comprada_em.date() + timedelta(days=DIAS_PARA_O_REEMBOLSO + 1)
    return datetime.combine(oitavo_dia, time(0), compra.comprada_em.tzinfo)


def reembolsar(compra: Compra, agora: datetime) -> Compra:
    """R13: dentro do prazo, a compra com direito a reembolso é reembolsada agora, sem condição
    sobre o quanto foi assistido. O acesso acaba na hora (R63)."""
    if compra.reembolsada_em is not None:
        raise JaReembolsada(
            f"Esta compra já foi reembolsada em {compra.reembolsada_em:%d/%m/%Y}."
        )
    if not compra.com_direito_a_reembolso:
        raise SemDireitoAReembolso()
    prazo = prazo_do_reembolso(compra)
    if agora >= prazo:
        ultimo_dia = prazo.date() - timedelta(days=1)
        raise PrazoDoReembolso(
            f"O reembolso só pode ser pedido até as 23h59 de {ultimo_dia:%d/%m/%Y}, o 7º dia "
            "depois da compra."
        )
    return replace(compra, reembolsada_em=agora)
