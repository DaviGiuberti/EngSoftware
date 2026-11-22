"""Presença e faltas (H21, H22, H08). A presença é lançada por aula, só em aula que já começou
(R43) e que foi realizada (R18), para os alunos que estão na turma desde aquela aula. As faltas
contam a partir da entrada do aluno, e o limite é de 6 por etapa (R08)."""

from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.turmas.domain.etapa import AulaDaEtapa
from plataforma.modules.turmas.domain.horario import formatar_data_e_hora

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


@dataclass(frozen=True)
class Presenca:
    """Se o aluno esteve na aula de data_da_aula. A falta é a presença com presente falso."""

    aluno_id: int
    data_da_aula: date
    presente: bool


def exigir_aula_para_presenca(aula: AulaDaEtapa, agora: datetime, ja_lancada: bool) -> int:
    """R18 e R43: só a aula realizada que já começou recebe presença, uma vez. Devolve o número."""
    if aula.numero is None:
        raise PresencaEmAulaNaoRealizada(
            f"A aula de {aula.data:%d/%m/%Y} não foi realizada: ela não recebe presença."
        )
    if aula.inicio > agora:
        raise AulaAindaNaoComecou(
            f"A {aula.numero}ª aula começa em {formatar_data_e_hora(aula.inicio)}: a presença só "
            "é lançada depois que ela começa."
        )
    if ja_lancada:
        raise PresencaJaLancada(f"A presença da {aula.numero}ª aula já foi lançada.")
    return aula.numero


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


def passou_do_limite(faltas: int) -> bool:
    """R08: com mais de 6 faltas, o aluno não é promovido nesta etapa."""
    return faltas > LIMITE_DE_FALTAS
