"""Nivelamento (H01, H02, H03, H33): uma vez por matéria (R03), 60 minutos que só correm com o
teste aberto (R30) e o resultado do nivelamento refeito (R42)."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum

from plataforma.compartilhado.recusa import Recusa

DURACAO_DO_NIVELAMENTO = timedelta(minutes=60)


class NivelamentoJaFeito(Recusa):
    """R03: a mensagem diz qual é a matéria."""


class NadaParaRefazer(Recusa):
    """O aluno ainda não tem nível na matéria, então não há o que refazer."""


class NivelamentoEmAndamento(Recusa):
    """O aluno está fazendo o nivelamento da matéria agora."""


class SemNivelamentoEmAndamento(Recusa):
    """O aluno não está fazendo o nivelamento da matéria."""


class TempoExtraInvalido(Recusa):
    mensagem = "Informe quantos minutos a mais, de 1 em diante."


@dataclass(frozen=True)
class TempoDoNivelamento:
    """R30: o tempo usado só cresce com o teste aberto.

    aberto_desde guarda desde quando o tempo está correndo: desde a abertura ou desde o último
    registro. Com o teste fechado, é None.
    """

    usado: timedelta
    extra: timedelta = timedelta(0)
    aberto_desde: datetime | None = None


def abrir(tempo: TempoDoNivelamento, agora: datetime) -> TempoDoNivelamento:
    """O tempo volta a correr a partir de agora.

    Se o app caiu com o teste aberto, o intervalo entre o último registro e agora não conta:
    o tempo só corre com o teste aberto, e o app registra o tempo a cada poucos segundos.
    """
    return replace(tempo, aberto_desde=agora)


def registrar(tempo: TempoDoNivelamento, agora: datetime) -> TempoDoNivelamento:
    """Soma ao tempo usado o que correu até agora. O teste continua aberto."""
    return replace(tempo, usado=_usado_ate(tempo, agora), aberto_desde=agora)


def fechar(tempo: TempoDoNivelamento, agora: datetime) -> TempoDoNivelamento:
    """Soma ao tempo usado o que correu até agora e para o tempo."""
    return replace(tempo, usado=_usado_ate(tempo, agora), aberto_desde=None)


def restante(tempo: TempoDoNivelamento, agora: datetime) -> timedelta:
    """Os 60 minutos, mais o tempo extra do ADM, menos o tempo usado. Nunca fica negativo."""
    return max(DURACAO_DO_NIVELAMENTO + tempo.extra - _usado_ate(tempo, agora), timedelta(0))


def acabou(tempo: TempoDoNivelamento, agora: datetime) -> bool:
    return restante(tempo, agora) == timedelta(0)


def com_mais_tempo(tempo: TempoDoNivelamento, minutos: int) -> TempoDoNivelamento:
    """R30: o ADM dá mais tempo a um aluno que está fazendo o nivelamento."""
    if minutos < 1:
        raise TempoExtraInvalido()
    return replace(tempo, extra=tempo.extra + timedelta(minutes=minutos))


def _usado_ate(tempo: TempoDoNivelamento, agora: datetime) -> timedelta:
    if tempo.aberto_desde is None:
        return tempo.usado
    # Um relógio que volta no tempo não devolve minutos ao aluno.
    return tempo.usado + max(agora - tempo.aberto_desde, timedelta(0))


def exigir_que_pode_iniciar(nome_da_materia: str, tem_nivel: bool, refazer_liberado: bool) -> None:
    """R03: só faz o nivelamento quem ainda não tem nível na matéria, ou quem o ADM liberou."""
    if tem_nivel and not refazer_liberado:
        raise NivelamentoJaFeito(f"O nivelamento de {nome_da_materia} já foi feito.")


def exigir_que_pode_liberar(nome_da_materia: str, tem_nivel: bool, em_andamento: bool) -> None:
    """O ADM libera refazer para quem já tem nível e não está fazendo o nivelamento agora."""
    if not tem_nivel:
        raise NadaParaRefazer(f"Este aluno ainda não fez o nivelamento de {nome_da_materia}.")
    if em_andamento:
        raise NivelamentoEmAndamento(
            f"Este aluno está fazendo o nivelamento de {nome_da_materia} agora."
        )


def exigir_em_andamento(nome_da_materia: str, em_andamento: bool) -> None:
    """R30: o ADM só dá mais tempo a quem está fazendo o nivelamento."""
    if not em_andamento:
        raise SemNivelamentoEmAndamento(
            f"Este aluno não está fazendo o nivelamento de {nome_da_materia}."
        )


def nivel_depois_do_nivelamento(nivel_atual: int | None, nivel_da_nota: int) -> int:
    """O primeiro nivelamento define o nível. O refeito só muda o nível se for maior (R42)."""
    if nivel_atual is None:
        return nivel_da_nota
    return max(nivel_atual, nivel_da_nota)


class SituacaoNaMateria(StrEnum):
    """O que o aluno vê de cada matéria no perfil (H03)."""

    SEM_NIVEL = "sem_nivel"
    INDISPONIVEL = "indisponivel"
    EM_ANDAMENTO = "em_andamento"
    COM_NIVEL = "com_nivel"
    REFAZER_LIBERADO = "refazer_liberado"


def situacao_na_materia(
    nivel: int | None, refazer_liberado: bool, em_andamento: bool, quantidade_de_questoes: int
) -> SituacaoNaMateria:
    if em_andamento:
        return SituacaoNaMateria.EM_ANDAMENTO
    if nivel is not None:
        if refazer_liberado:
            return SituacaoNaMateria.REFAZER_LIBERADO
        return SituacaoNaMateria.COM_NIVEL
    if quantidade_de_questoes == 0:
        return SituacaoNaMateria.INDISPONIVEL
    return SituacaoNaMateria.SEM_NIVEL
