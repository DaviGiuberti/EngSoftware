"""O lado do aluno no catálogo (H14, H16): a vitrine (R15, R31), o acesso às aulas (R12, R61) e a
aula concluída (R62).

O acesso vem da compra, que é do módulo vendas (ADR 0002). Aqui ele chega pronto, como
AcessoAoPacote: até quando vai e se ainda está ativo agora.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.catalogo.domain.pacote import (
    AulaNaoEncontrada,
    EstadoPacote,
    Pacote,
)


class SemAcesso(Recusa):
    """R12 e R61: a mensagem diz se o aluno nunca comprou o pacote ou quando o acesso venceu."""


class AulaJaConcluida(Recusa):
    """R62: a mensagem diz quando o aluno concluiu a aula."""


@dataclass(frozen=True)
class AcessoAoPacote:
    """O acesso do aluno a um pacote: o último dia (R60) e se ele está ativo agora (R12)."""

    ate: date
    ativo: bool


@dataclass(frozen=True)
class NaVitrine:
    pacote: Pacote
    destaque: bool


@dataclass(frozen=True)
class AulaConcluida:
    """R62: a aula gravada que o aluno concluiu e quando. Conta como atividade de estudo."""

    pacote_id: int
    numero: int
    concluida_em: datetime


def vitrine(pacotes: Iterable[Pacote], niveis: Mapping[int, int]) -> list[NaVitrine]:
    """R15 e R31: os pacotes publicados, de todos os níveis. Os do nível do aluno em cada matéria
    vêm primeiro, em destaque; os outros seguem na ordem em que chegaram.

    niveis traz o nível do aluno em cada matéria, pelo id da matéria. Sem nível, nada tem destaque.
    """
    publicados = [pacote for pacote in pacotes if pacote.estado == EstadoPacote.PUBLICADO]
    itens = [NaVitrine(p, niveis.get(p.materia_id) == p.nivel) for p in publicados]
    return sorted(itens, key=lambda item: not item.destaque)


def exigir_acesso(acesso: AcessoAoPacote | None) -> None:
    """R12 e R61: o aluno só assiste às aulas com o acesso ativo."""
    if acesso is None:
        raise SemAcesso("Você não tem acesso a este pacote. Compre o pacote para assistir.")
    if not acesso.ativo:
        raise SemAcesso(f"Seu acesso a este pacote venceu em {acesso.ate:%d/%m/%Y}.")


def concluir_aula(
    pacote: Pacote,
    numero: int,
    acesso: AcessoAoPacote | None,
    concluidas: Iterable[AulaConcluida],
    agora: datetime,
) -> AulaConcluida:
    """R62: com o acesso ativo, a aula vira concluída agora. A que já foi concluída não muda.

    concluidas são as aulas que o aluno já concluiu nesse pacote.
    """
    exigir_acesso(acesso)
    if not 1 <= numero <= len(pacote.aulas):
        raise AulaNaoEncontrada(f"O pacote não tem a {numero}ª aula.")
    for concluida in concluidas:
        if concluida.pacote_id == pacote.id and concluida.numero == numero:
            raise AulaJaConcluida(
                f"Você já concluiu a {numero}ª aula em {concluida.concluida_em:%d/%m/%Y}."
            )
    return AulaConcluida(pacote.id, numero, agora)


def progresso(pacote: Pacote, concluidas: Iterable[AulaConcluida]) -> tuple[int, int]:
    """Quantas aulas do pacote o aluno concluiu e quantas o pacote tem."""
    feitas = {concluida.numero for concluida in concluidas if concluida.pacote_id == pacote.id}
    return len(feitas), len(pacote.aulas)
