"""Promoção (H09, H32): aprovado na etapa, o aluno sobe exatamente um nível, sem pular (R08, R09).
No nível máximo, ele continua nele e conclui a trilha (R09). O nível nunca desce (R22)."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Promocao:
    """A subida de um nível do aluno numa matéria e quando ela aconteceu (R49). A data serve à
    M1 e aos certificados de nível (R33)."""

    materia_id: int
    nivel_anterior: int
    nivel_novo: int
    em: datetime


def promover(
    materia_id: int, nivel_atual: int, nivel_da_etapa: int, nivel_maximo: int, em: datetime
) -> Promocao | None:
    """R08 e R09: o aprovado sobe um nível a partir do da etapa, nunca dois, e não passa do nível
    máximo. O nível nunca desce (R22). Devolve None quando o nível não muda."""
    novo = max(nivel_atual, min(nivel_da_etapa + 1, nivel_atual + 1, nivel_maximo))
    if novo == nivel_atual:
        return None
    return Promocao(materia_id, nivel_atual, novo, em)


def conclui_a_trilha(nivel_da_etapa: int, nivel_maximo: int) -> bool:
    """R09: a aprovação na etapa do nível máximo conclui a trilha da matéria."""
    return nivel_da_etapa >= nivel_maximo
