"""Matéria (H27): níveis (R01), faixas do nivelamento (R02, R40) e mensalidade (R27)."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import pairwise

from plataforma.compartilhado.recusa import Recusa

NOTA_MAXIMA = 100


class NomeVazio(Recusa):
    mensagem = "Informe o nome da matéria."


class NomeJaCadastrado(Recusa):
    mensagem = "Já existe uma matéria com esse nome."


class SemNiveis(Recusa):
    mensagem = "A matéria precisa ter pelo menos 1 nível."


class MensalidadeInvalida(Recusa):
    mensagem = "A mensalidade precisa ser maior que zero."


class FaixasInvalidas(Recusa):
    """R40: a mensagem diz qual nota mínima está errada."""


@dataclass(frozen=True)
class Faixa:
    """R02: intervalo de nota do nivelamento que leva a um nível, como 40–69% → N2."""

    nivel: int
    nota_minima: int
    nota_maxima: int


@dataclass(frozen=True)
class MateriaNova:
    """Matéria conferida e pronta para gravar. Tem uma faixa por nível (R40)."""

    nome: str
    faixas: tuple[Faixa, ...]
    mensalidade_em_centavos: int

    @property
    def niveis(self) -> tuple[int, ...]:
        return tuple(faixa.nivel for faixa in self.faixas)


@dataclass(frozen=True)
class Materia:
    id: int
    nome: str
    faixas: tuple[Faixa, ...]
    mensalidade_em_centavos: int

    @property
    def nivel_maximo(self) -> int:
        return len(self.faixas)


def nome_do_nivel(nivel: int) -> str:
    return f"N{nivel}"


def nova_materia(
    nome: str, nivel_maximo: int, notas_minimas: Sequence[int], mensalidade_em_centavos: int
) -> MateriaNova:
    """Confere o cadastro do ADM e monta as faixas.

    notas_minimas traz a nota mínima de cada nível a partir do N2, em ordem.
    """
    nome = nome.strip()
    if not nome:
        raise NomeVazio()
    if nivel_maximo < 1:
        raise SemNiveis()
    if len(notas_minimas) != nivel_maximo - 1:
        raise FaixasInvalidas("Informe uma nota mínima para cada nível a partir do N2.")
    if mensalidade_em_centavos <= 0:
        raise MensalidadeInvalida()
    return MateriaNova(nome, montar_faixas(notas_minimas), mensalidade_em_centavos)


def montar_faixas(notas_minimas: Sequence[int]) -> tuple[Faixa, ...]:
    """R40: monta as faixas do N1 ao nível máximo, de 0% a 100%, sem buraco nem sobreposição.

    O N1 começa em 0%, e cada faixa vai até 1 ponto abaixo da nota mínima do nível seguinte.
    """
    inicios = [0, *notas_minimas]
    for nivel, (anterior, atual) in enumerate(pairwise(inicios), start=2):
        if not 1 <= atual <= NOTA_MAXIMA:
            raise FaixasInvalidas(
                f"A nota mínima do {nome_do_nivel(nivel)} precisa estar entre 1% e 100%."
            )
        if atual <= anterior:
            raise FaixasInvalidas(
                f"A nota mínima do {nome_do_nivel(nivel)} precisa ser maior que a do "
                f"{nome_do_nivel(nivel - 1)}."
            )
    fins = [inicio - 1 for inicio in inicios[1:]] + [NOTA_MAXIMA]
    return tuple(
        Faixa(nivel, inicio, fim)
        for nivel, (inicio, fim) in enumerate(zip(inicios, fins, strict=True), start=1)
    )


def nivel_da_nota(faixas: Sequence[Faixa], nota: int) -> int:
    """R02: o nível da faixa em que a nota cai. As faixas cobrem de 0 a 100 (R40)."""
    for faixa in faixas:
        if faixa.nota_minima <= nota <= faixa.nota_maxima:
            return faixa.nivel
    raise ValueError(f"Nota fora das faixas: {nota}")


def exigir_nome_livre(nome: str, nomes_cadastrados: Iterable[str]) -> None:
    """Recusa o nome de uma matéria que já existe, sem diferenciar maiúsculas."""
    if any(nome.casefold() == cadastrado.casefold() for cadastrado in nomes_cadastrados):
        raise NomeJaCadastrado()
