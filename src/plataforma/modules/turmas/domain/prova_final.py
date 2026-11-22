"""Prova final (H23, H24, H09, H11, H32). A nota vai de 0 a 10, com uma casa decimal (R51), e é
lançada no fim da etapa, depois da 24ª aula (R17, R20), para quem estava na turma nesse momento.
O professor corrige até 72 horas depois do lançamento; depois, só o ADM (R22). O resultado da
etapa (R08) passa a valer quando esse prazo termina (R49), e uma correção feita depois disso só
muda o nível para cima (R22)."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.turmas.domain.horario import formatar_data_e_hora
from plataforma.modules.turmas.domain.matricula import Matricula
from plataforma.modules.turmas.domain.presenca import passou_do_limite

PRAZO_DE_CORRECAO = timedelta(hours=72)

# De 0 a 10, com no máximo uma casa decimal, depois de vírgula ou ponto: "6,5", "6.5", "7".
_NOTA = re.compile(r"([0-9]{1,2})(?:[,.]([0-9]))?")


class NotaInvalida(Recusa):
    mensagem = "A nota vai de 0 a 10, com uma casa decimal, como 6,5."


class EtapaNaoTerminou(Recusa):
    """R17 e R20: a mensagem diz quando a etapa termina."""


class NotaJaLancada(Recusa):
    """A mensagem diz de quem é a nota. Mudar a nota é a correção (R22)."""


class SemNota(Recusa):
    """R22: a mensagem diz de quem é a nota que ainda não foi lançada."""


class PrazoDeCorrecaoVencido(Recusa):
    """R22: a mensagem diz quando o prazo terminou e que só o ADM pode corrigir."""


class AlunoForaDaEtapa(Recusa):
    mensagem = "Este aluno não estava na turma no fim da etapa."


@dataclass(frozen=True, order=True)
class Nota:
    """Nota da prova final, guardada em décimos: 6,5 é Nota(65) (R51)."""

    decimos: int

    def __str__(self) -> str:
        inteiro, decimo = divmod(self.decimos, 10)
        return f"{inteiro}" if decimo == 0 else f"{inteiro},{decimo}"


NOTA_MAXIMA = Nota(100)
# R08: o aluno é aprovado com nota ≥ 7.
NOTA_PARA_APROVAR = Nota(70)


def ler_nota(texto: str) -> Nota:
    """R51: "6,5", "6.5", "7" e "10" são notas. "6,75", "-1", "10,5" e "" não são."""
    lida = _NOTA.fullmatch(texto.strip())
    if lida is None:
        raise NotaInvalida()
    inteiro, decimo = lida.groups()
    nota = Nota(int(inteiro) * 10 + int(decimo or "0"))
    if nota > NOTA_MAXIMA:
        raise NotaInvalida()
    return nota


class ResultadoEtapa(StrEnum):
    APROVADO = "aprovado"
    REPROVADO = "reprovado"
    PENDENTE = "pendente"


@dataclass(frozen=True)
class ProvaFinal:
    """A nota de um aluno na prova final de uma etapa e quando ela foi lançada (R20).

    resultado_aplicado é o resultado que já passou a valer (R49), com a promoção ou a saída da
    turma feitas. Antes do fim do prazo de correção, é None.
    """

    aluno_id: int
    nota: Nota
    lancada_em: datetime
    resultado_aplicado: ResultadoEtapa | None = None

    @property
    def vale_em(self) -> datetime:
        """R49: o resultado passa a valer quando termina o prazo de correção da nota."""
        return fim_do_prazo_de_correcao(self.lancada_em)


def resultado_da_etapa(faltas: int, nota: Nota | None) -> ResultadoEtapa:
    """R08: aprovado com no máximo 6 faltas e nota ≥ 7, e reprovado se não. Sem a nota, o
    resultado fica pendente (R23)."""
    if nota is None:
        return ResultadoEtapa.PENDENTE
    if not passou_do_limite(faltas) and nota >= NOTA_PARA_APROVAR:
        return ResultadoEtapa.APROVADO
    return ResultadoEtapa.REPROVADO


def fim_do_prazo_de_correcao(lancada_em: datetime) -> datetime:
    """R22: o prazo vai até 72 horas depois do lançamento. Uma correção não o recomeça."""
    return lancada_em + PRAZO_DE_CORRECAO


def exigir_fim_da_etapa(fim_da_etapa: datetime, agora: datetime) -> None:
    """R17 e R20: a nota da prova final só é lançada no fim da etapa, depois da 24ª aula."""
    if agora < fim_da_etapa:
        raise EtapaNaoTerminou(
            "A nota da prova final só é lançada no fim da etapa, depois da 24ª aula: em "
            f"{formatar_data_e_hora(fim_da_etapa)}."
        )


def exigir_prazo_de_correcao(lancada_em: datetime, agora: datetime, pelo_adm: bool) -> None:
    """R22: o professor corrige uma presença ou nota até 72 horas depois de lançá-la. Depois,
    só o ADM, que corrige a qualquer momento (R10)."""
    fim = fim_do_prazo_de_correcao(lancada_em)
    if pelo_adm or agora < fim:
        return
    raise PrazoDeCorrecaoVencido(
        f"O prazo de correção terminou em {formatar_data_e_hora(fim)}, 72 horas depois do "
        "lançamento: agora só o ADM pode corrigir."
    )


def exigir_sem_nota(prova: ProvaFinal | None, email_do_aluno: str) -> None:
    """A nota de cada aluno na etapa é lançada uma vez. Depois, ela é corrigida (R22)."""
    if prova is not None:
        raise NotaJaLancada(
            f"A nota de {email_do_aluno} já foi lançada. Para mudar, corrija a nota."
        )


def exigir_nota(prova: ProvaFinal | None, email_do_aluno: str) -> ProvaFinal:
    """R22: só a nota já lançada é corrigida."""
    if prova is None:
        raise SemNota(f"A nota de {email_do_aluno} ainda não foi lançada.")
    return prova


def matriculas_da_etapa(
    matriculas: Iterable[Matricula], fim_da_etapa: datetime
) -> list[Matricula]:
    """R08 e R23: a prova final é de quem estava na turma no fim da etapa, mesmo que tenha saído
    depois, como o reprovado quando o resultado vale (R21, R49)."""
    return [
        matricula
        for matricula in matriculas
        if matricula.matriculada_em < fim_da_etapa
        and (matricula.saiu_em is None or matricula.saiu_em >= fim_da_etapa)
    ]


def matricula_na_etapa(
    matriculas: Iterable[Matricula], aluno_id: int, fim_da_etapa: datetime
) -> Matricula:
    """A matrícula com que o aluno estava na turma no fim da etapa."""
    da_etapa = matriculas_da_etapa(matriculas, fim_da_etapa)
    matricula = next((m for m in da_etapa if m.aluno_id == aluno_id), None)
    if matricula is None:
        raise AlunoForaDaEtapa()
    return matricula


def resultado_a_aplicar(
    aplicado: ResultadoEtapa | None, novo: ResultadoEtapa
) -> ResultadoEtapa | None:
    """R22: depois que o resultado valeu (R49), uma correção só muda o nível para cima. O
    reprovado que passa a aprovado é promovido, e o aprovado que passa a reprovado continua no
    nível. Devolve o resultado que passa a valer agora, ou None se nada muda."""
    if aplicado == ResultadoEtapa.REPROVADO and novo == ResultadoEtapa.APROVADO:
        return ResultadoEtapa.APROVADO
    return None
