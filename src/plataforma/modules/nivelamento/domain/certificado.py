"""Certificados de nível e de trilha (H12). O certificado de nível sai de cada promoção e é do
nível em que o aluno foi aprovado (R33). A aprovação no nível máximo conclui a trilha e dá o
certificado de nível desse nível e o de trilha (R36). O nivelamento não gera certificado.

Os certificados não são guardados à parte: saem das promoções e das trilhas concluídas, com a
data em que o resultado valeu (R49). Como uma correção não tira a promoção (R22), também não tira
o certificado."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from plataforma.modules.nivelamento.domain.promocao import Promocao


class TipoDeCertificado(StrEnum):
    NIVEL = "nivel"
    TRILHA = "trilha"


@dataclass(frozen=True)
class Certificado:
    """Um certificado do aluno numa matéria. O de trilha leva o nível máximo, que concluiu."""

    tipo: TipoDeCertificado
    materia_id: int
    nivel: int
    emitido_em: datetime


def certificados(
    promocoes: Iterable[Promocao],
    trilhas_concluidas: Mapping[int, datetime],
    niveis_maximos: Mapping[int, int],
) -> list[Certificado]:
    """Os certificados do aluno, na ordem em que foram emitidos.

    trilhas_concluidas leva a matéria à data em que a trilha foi concluída, e niveis_maximos, a
    matéria ao nível máximo dela.
    """
    emitidos = [
        Certificado(TipoDeCertificado.NIVEL, p.materia_id, p.nivel_anterior, p.em)
        for p in promocoes
    ]
    for materia_id, em in trilhas_concluidas.items():
        nivel_maximo = niveis_maximos[materia_id]
        emitidos.append(Certificado(TipoDeCertificado.NIVEL, materia_id, nivel_maximo, em))
        emitidos.append(Certificado(TipoDeCertificado.TRILHA, materia_id, nivel_maximo, em))
    return sorted(
        emitidos,
        key=lambda c: (c.emitido_em, c.materia_id, c.nivel, c.tipo == TipoDeCertificado.TRILHA),
    )
