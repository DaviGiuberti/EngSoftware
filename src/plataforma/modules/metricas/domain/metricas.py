"""Métricas M1, M2 e M3 (H36), da seção 4 da visão.

Cada aluno numa matéria conta pelo primeiro nivelamento que concluiu nela, no mês da conclusão
(R64). A M1 é a porcentagem dos promovidos na matéria em até 6 meses (R65); a M2, a dos que
estudaram a matéria na 4ª semana, do 21º ao 27º dia (R66); a M3, a mediana dos dias até a primeira
atividade de estudo na matéria e no nível recebido (R67).

Os dados chegam prontos dos outros módulos (ADR 0002): os nivelamentos, as promoções e as
atividades de estudo, que são as presenças e as aulas gravadas concluídas.
"""

import calendar
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from statistics import median

MESES_PARA_A_PROGRESSAO = 6
# R66: do 21º ao 27º dia depois do nivelamento, com o dia do nivelamento como o dia 0.
INICIO_DA_4A_SEMANA = 21
FIM_DA_4A_SEMANA = 27
DIAS_PARA_ENTRAR_NA_M2 = 28


@dataclass(frozen=True)
class Nivelado:
    """Um aluno numa matéria, com a data do nivelamento e o nível que ele deu (R64)."""

    aluno_id: int
    materia_id: int
    nivel: int
    em: datetime


@dataclass(frozen=True)
class Subida:
    """Uma promoção do aluno na matéria e quando ela aconteceu."""

    aluno_id: int
    materia_id: int
    em: datetime


@dataclass(frozen=True)
class AtividadeDeEstudo:
    """Presença numa aula de turma ou aula gravada concluída, com a matéria e o nível (R64)."""

    aluno_id: int
    materia_id: int
    nivel: int
    em: date


@dataclass(frozen=True)
class TaxaDeProgressao:
    """M1 (R65): quantos nivelados foram promovidos e quantos ainda estão dentro dos 6 meses."""

    promovidos: int
    nivelados: int
    ainda_no_prazo: int

    @property
    def porcentagem(self) -> float | None:
        return _porcentagem(self.promovidos, self.nivelados)


@dataclass(frozen=True)
class ContinuidadeNaTrilha:
    """M2 (R66): entre os nivelados há pelo menos 28 dias, quantos estudaram na 4ª semana."""

    com_atividade: int
    elegiveis: int

    @property
    def porcentagem(self) -> float | None:
        return _porcentagem(self.com_atividade, self.elegiveis)


@dataclass(frozen=True)
class TempoAteNivelCerto:
    """M3 (R67): os dias até a primeira atividade no nível recebido, do menor ao maior."""

    dias: tuple[int, ...]

    @property
    def mediana(self) -> float | None:
        """A mediana, com uma casa decimal. Com número par, é a média dos dois do meio."""
        if not self.dias:
            return None
        return round(float(median(self.dias)), 1)


def nivelados(nivelamentos: Iterable[Nivelado]) -> list[Nivelado]:
    """R64: só o primeiro nivelamento do aluno em cada matéria conta; o refeito não é novo."""
    primeiros: dict[tuple[int, int], Nivelado] = {}
    for nivelamento in sorted(nivelamentos, key=lambda n: n.em):
        primeiros.setdefault((nivelamento.aluno_id, nivelamento.materia_id), nivelamento)
    return list(primeiros.values())


def do_mes(casos: Iterable[Nivelado], ano: int, mes: int) -> list[Nivelado]:
    """R64: os nivelados cujo nivelamento foi concluído no mês."""
    return [caso for caso in casos if (caso.em.year, caso.em.month) == (ano, mes)]


def fim_do_prazo_da_progressao(caso: Nivelado) -> date:
    """R65: o mesmo dia, 6 meses depois do nivelamento, ou o último dia do mês que não o tem."""
    dia = caso.em.date()
    meses_desde_janeiro = dia.month - 1 + MESES_PARA_A_PROGRESSAO
    ano = dia.year + meses_desde_janeiro // 12
    mes = meses_desde_janeiro % 12 + 1
    return date(ano, mes, min(dia.day, calendar.monthrange(ano, mes)[1]))


def taxa_de_progressao(
    casos: Iterable[Nivelado], subidas: Iterable[Subida], agora: datetime
) -> TaxaDeProgressao:
    """R65: entram todos os nivelados do mês. Conta quem foi promovido na matéria até o fim do
    prazo e quem, sem promoção, ainda está dentro dele."""
    casos = list(casos)
    subidas = list(subidas)
    promovidos = 0
    ainda_no_prazo = 0
    for caso in casos:
        fim = fim_do_prazo_da_progressao(caso)
        subiu = any(
            subida.aluno_id == caso.aluno_id
            and subida.materia_id == caso.materia_id
            and caso.em <= subida.em
            and subida.em.date() <= fim
            for subida in subidas
        )
        if subiu:
            promovidos += 1
        elif agora.date() <= fim:
            ainda_no_prazo += 1
    return TaxaDeProgressao(promovidos, len(casos), ainda_no_prazo)


def continuidade_na_trilha(
    casos: Iterable[Nivelado], atividades: Iterable[AtividadeDeEstudo], agora: datetime
) -> ContinuidadeNaTrilha:
    """R66: entre os nivelados há pelo menos 28 dias, quantos tiveram atividade de estudo na
    matéria, em qualquer nível, do 21º ao 27º dia depois do nivelamento."""
    atividades = list(atividades)
    elegiveis = [
        caso for caso in casos if _dias_desde(caso, agora.date()) >= DIAS_PARA_ENTRAR_NA_M2
    ]
    com_atividade = sum(
        1
        for caso in elegiveis
        if any(
            INICIO_DA_4A_SEMANA <= _dias_desde(caso, atividade.em) <= FIM_DA_4A_SEMANA
            for atividade in _da_materia(caso, atividades)
        )
    )
    return ContinuidadeNaTrilha(com_atividade, len(elegiveis))


def tempo_ate_nivel_certo(
    casos: Iterable[Nivelado], atividades: Iterable[AtividadeDeEstudo]
) -> TempoAteNivelCerto:
    """R67: para cada nivelado com atividade na matéria e no nível recebido, desde o dia do
    nivelamento, os dias de calendário até a primeira delas. Quem não teve não entra."""
    atividades = list(atividades)
    dias = []
    for caso in casos:
        no_nivel = [
            _dias_desde(caso, atividade.em)
            for atividade in _da_materia(caso, atividades)
            if atividade.nivel == caso.nivel and atividade.em >= caso.em.date()
        ]
        if no_nivel:
            dias.append(min(no_nivel))
    return TempoAteNivelCerto(tuple(sorted(dias)))


def _da_materia(caso: Nivelado, atividades: list[AtividadeDeEstudo]) -> list[AtividadeDeEstudo]:
    return [
        atividade
        for atividade in atividades
        if atividade.aluno_id == caso.aluno_id and atividade.materia_id == caso.materia_id
    ]


def _dias_desde(caso: Nivelado, dia: date) -> int:
    return (dia - caso.em.date()).days


def _porcentagem(parte: int, total: int) -> float | None:
    if total == 0:
        return None
    return 100 * parte / total
