"""Presença e faltas (H21, H22, H08, H24). A presença é lançada por aula, só em aula que já
começou (R43) e que foi realizada (R18), para os alunos que estão na turma desde aquela aula. As
faltas contam a partir da entrada do aluno, e o limite é de 6 por etapa (R08). Só a presença já
lançada é corrigida (R22)."""

from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.turmas.domain.etapa import AulaDaEtapa, Etapa
from plataforma.modules.turmas.domain.horario import formatar_data_e_hora
from plataforma.modules.turmas.domain.matricula import aula_de_entrada

# R08: 25% das 24 aulas da etapa.
LIMITE_DE_FALTAS = 6


class PresencaEmAulaNaoRealizada(Recusa):
    """R18: a mensagem diz a data da aula."""


class AulaAindaNaoComecou(Recusa):
    """R43: a mensagem diz quando a aula começa."""


class PresencaJaLancada(Recusa):
    """A mensagem diz qual aula. Corrigir a presença é a R22."""


class FaltaDeQuemNaoEstaNaAula(Recusa):
    mensagem = "Só quem está na turma desde esta aula recebe falta nela."


class PresencaNaoLancada(Recusa):
    """R22: a mensagem diz qual aula ainda não tem presença para corrigir."""


@dataclass(frozen=True)
class Presenca:
    """Se o aluno esteve na aula de data_da_aula. A falta é a presença com presente falso."""

    aluno_id: int
    data_da_aula: date
    presente: bool


@dataclass(frozen=True)
class PresencaNaMateria:
    """Uma presença (não uma falta) do aluno numa aula de turma, com a matéria e o nível da etapa.
    É uma atividade de estudo para as métricas (R64)."""

    aluno_id: int
    materia_id: int
    nivel: int
    data_da_aula: date


def _numero_da_aula_realizada(aula: AulaDaEtapa) -> int:
    """R18: a aula não realizada não tem número e não recebe presença."""
    if aula.numero is None:
        raise PresencaEmAulaNaoRealizada(
            f"A aula de {aula.data:%d/%m/%Y} não foi realizada: ela não recebe presença."
        )
    return aula.numero


def exigir_aula_para_presenca(aula: AulaDaEtapa, agora: datetime, ja_lancada: bool) -> int:
    """R18 e R43: só a aula realizada que já começou recebe presença, uma vez. Devolve o número."""
    numero = _numero_da_aula_realizada(aula)
    if aula.inicio > agora:
        raise AulaAindaNaoComecou(
            f"A {numero}ª aula começa em {formatar_data_e_hora(aula.inicio)}: a presença só é "
            "lançada depois que ela começa."
        )
    if ja_lancada:
        raise PresencaJaLancada(f"A presença da {numero}ª aula já foi lançada.")
    return numero


def exigir_aula_para_correcao(aula: AulaDaEtapa, lancada_em: datetime | None) -> datetime:
    """R22: só a presença já lançada é corrigida. Devolve quando ela foi lançada, que é de onde
    contam as 72 horas da correção."""
    numero = _numero_da_aula_realizada(aula)
    if lancada_em is None:
        raise PresencaNaoLancada(f"A presença da {numero}ª aula ainda não foi lançada.")
    return lancada_em


def alunos_da_aula(entradas: Mapping[int, int], numero_da_aula: int) -> list[int]:
    """R08: a aula tem os alunos que entraram na turma até ela. entradas leva o aluno à aula de
    entrada dele."""
    return [aluno for aluno, entrada in entradas.items() if entrada <= numero_da_aula]


def lancar(
    data_da_aula: date, alunos: Sequence[int], ausentes: Collection[int]
) -> list[Presenca]:
    """R10: o professor diz quem faltou, e os outros alunos da aula ficam com presença."""
    if not set(ausentes) <= set(alunos):
        raise FaltaDeQuemNaoEstaNaAula()
    return [Presenca(aluno, data_da_aula, aluno not in ausentes) for aluno in alunos]


def faltas(
    presencas: Iterable[Presenca], aulas: Sequence[AulaDaEtapa], aula_de_entrada: int
) -> int:
    """R08: as faltas do aluno nas aulas realizadas da etapa, a partir da aula de entrada.

    As aulas anteriores à entrada contam como presença.
    """
    numeros = {aula.data: aula.numero for aula in aulas if aula.numero is not None}
    return sum(
        1
        for presenca in presencas
        if not presenca.presente and numeros.get(presenca.data_da_aula, 0) >= aula_de_entrada
    )


def faltas_na_etapa(
    etapa: Etapa, aluno_id: int, matriculada_em: datetime, presencas: Iterable[Presenca]
) -> int:
    """R08: as faltas do aluno numa etapa, a atual ou uma que já terminou, a partir da aula em
    que ele entrou na turma. Quem já estava na turma antes de a etapa começar conta desde a 1ª."""
    entrada = aula_de_entrada(etapa.aulas_dadas(matriculada_em))
    do_aluno = [presenca for presenca in presencas if presenca.aluno_id == aluno_id]
    return faltas(do_aluno, etapa.calendario(), entrada)


def passou_do_limite(faltas: int) -> bool:
    """R08: com mais de 6 faltas, o aluno não é promovido nesta etapa."""
    return faltas > LIMITE_DE_FALTAS
