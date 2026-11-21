"""Questões do nivelamento (H28): 5 alternativas e uma só correta (R41)."""

from collections.abc import Sequence
from dataclasses import dataclass

from plataforma.compartilhado.recusa import Recusa

LETRAS_DAS_ALTERNATIVAS = "ABCDE"


class EnunciadoVazio(Recusa):
    mensagem = "Escreva o enunciado da questão."


class AlternativasIncompletas(Recusa):
    mensagem = "A questão precisa ter 5 alternativas, de A a E."


class SemAlternativaCorreta(Recusa):
    mensagem = "Marque qual alternativa é a correta."


class NivelamentoIndisponivel(Recusa):
    """A matéria ainda não tem questões. A mensagem diz qual é a matéria."""


@dataclass(frozen=True)
class Alternativa:
    texto: str
    correta: bool


@dataclass(frozen=True)
class QuestaoNova:
    """Questão conferida e pronta para gravar."""

    enunciado: str
    alternativas: tuple[Alternativa, ...]


@dataclass(frozen=True)
class Questao:
    id: int
    materia_id: int
    enunciado: str
    alternativas: tuple[Alternativa, ...]

    @property
    def letra_da_correta(self) -> str:
        indice = next(i for i, alternativa in enumerate(self.alternativas) if alternativa.correta)
        return LETRAS_DAS_ALTERNATIVAS[indice]


def nova_questao(
    enunciado: str, alternativas: Sequence[str], indice_da_correta: int | None
) -> QuestaoNova:
    """Confere a questão do ADM: enunciado, 5 alternativas preenchidas e uma correta (R41).

    A correta é dada pela posição: 0 é a A, e 4 é a E.
    """
    enunciado = enunciado.strip()
    if not enunciado:
        raise EnunciadoVazio()
    textos = [texto.strip() for texto in alternativas]
    if len(textos) != len(LETRAS_DAS_ALTERNATIVAS) or not all(textos):
        raise AlternativasIncompletas()
    if indice_da_correta is None or not 0 <= indice_da_correta < len(textos):
        raise SemAlternativaCorreta()
    return QuestaoNova(
        enunciado,
        tuple(Alternativa(texto, i == indice_da_correta) for i, texto in enumerate(textos)),
    )


def exigir_questoes(nome_da_materia: str, quantidade_de_questoes: int) -> None:
    """Matéria sem questões ainda não tem nivelamento para fazer."""
    if quantidade_de_questoes == 0:
        raise NivelamentoIndisponivel(
            f"O nivelamento de {nome_da_materia} ainda não está disponível."
        )
