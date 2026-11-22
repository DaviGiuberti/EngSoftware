"""Turmas em dia (H09, H10, H11, H23, H07): o que o tempo decide sem ninguém agir. No fim da
etapa, a turma passa para o nível seguinte ou encerra (R04, R09), e a lista de espera é esvaziada
(R50). Quando terminam as 72 horas de correção da nota, o resultado da etapa passa a valer: o
aprovado é promovido, e o reprovado sai da turma (R21, R49). Quem não paga a mensalidade até o fim
da tolerância perde a vaga (R28, R37). A vaga de quem sai vai para a lista de espera (R05).

Não há tarefa em segundo plano, como na lista de espera (R35): todo caso de uso das turmas põe as
turmas em dia antes de agir, e cada mudança vale a partir do momento em que aconteceu. O resultado
é o mesmo, seja qual for a hora em que o sistema olha.
"""

from dataclasses import dataclass
from datetime import datetime

from plataforma.compartilhado.relogio import Relogio
from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.materias.domain.materia import Materia
from plataforma.modules.nivelamento.application.promocao import Promocoes
from plataforma.modules.turmas.application.portas import RepositorioDeTurmas
from plataforma.modules.turmas.domain.etapa import Etapa, etapa_do_nivel
from plataforma.modules.turmas.domain.lista_de_espera import (
    ListaDeEspera,
    oferecer_vaga,
    pode_oferecer_em,
    vencer_prazos,
)
from plataforma.modules.turmas.domain.matricula import Matricula, MotivoDaSaida
from plataforma.modules.turmas.domain.mensalidade import proxima_mensalidade, vence
from plataforma.modules.turmas.domain.presenca import faltas_na_etapa
from plataforma.modules.turmas.domain.prova_final import (
    ProvaFinal,
    ResultadoEtapa,
    matriculas_da_etapa,
    resultado_a_aplicar,
    resultado_da_etapa,
)
from plataforma.modules.turmas.domain.turma import (
    Encerramento,
    MudancaDaTurma,
    Turma,
    com_a_mudanca,
    mudancas_ate,
)


@dataclass(frozen=True)
class SituacaoNaProvaFinal:
    """Um aluno na prova final de uma etapa: as faltas dele na etapa (R08), a prova, se a nota
    já foi lançada, e o resultado."""

    nivel: int
    matricula: Matricula
    faltas: int
    prova: ProvaFinal | None
    resultado: ResultadoEtapa

    @property
    def aluno_id(self) -> int:
        return self.matricula.aluno_id


def situacoes_na_prova_final(
    turmas: RepositorioDeTurmas, turma_id: int, etapa: Etapa
) -> list[SituacaoNaProvaFinal]:
    """A prova final de quem estava na turma no fim da etapa (R23), na ordem das matrículas."""
    matriculas = matriculas_da_etapa(turmas.todas_as_matriculas(turma_id), etapa.fim)
    presencas = turmas.presencas(turma_id, etapa.nivel)
    provas = {prova.aluno_id: prova for prova in turmas.provas_finais(turma_id, etapa.nivel)}
    situacoes = []
    for matricula in matriculas:
        faltas = faltas_na_etapa(etapa, matricula.aluno_id, matricula.matriculada_em, presencas)
        prova = provas.get(matricula.aluno_id)
        resultado = resultado_da_etapa(faltas, None if prova is None else prova.nota)
        situacoes.append(SituacaoNaProvaFinal(etapa.nivel, matricula, faltas, prova, resultado))
    return situacoes


@dataclass(frozen=True)
class _ResultadoQueVale:
    """R49: o resultado de um aluno na etapa, que passa a valer no fim do prazo de correção."""

    em: datetime
    nivel: int
    aluno_id: int
    resultado: ResultadoEtapa


@dataclass(frozen=True)
class _PerdaDaVaga:
    """R28 e R37: o aluno que não pagou a mensalidade perde a vaga na virada para o 8º dia."""

    em: datetime
    aluno_id: int


type _Evento = MudancaDaTurma | _ResultadoQueVale | _PerdaDaVaga


class TurmasEmDia:
    """Aplica a todas as turmas o que o tempo decidiu até agora, na ordem em que aconteceu."""

    def __init__(
        self, turmas: RepositorioDeTurmas, materias: ConsultaDeMaterias, promocoes: Promocoes
    ) -> None:
        self._turmas = turmas
        self._materias = materias
        self._promocoes = promocoes

    def aplicar(self, agora: datetime) -> None:
        """Roda na transação de quem chama, que grava tudo ou nada (RNF05)."""
        for turma in self._turmas.listar():
            self._por_em_dia(turma, agora)

    def reavaliar(self, turma: Turma, nivel: int, agora: datetime) -> None:
        """R22: depois de corrigir uma presença ou nota da etapa, o resultado que já valeu só muda
        para cima. O reprovado que passa a aprovado sobe agora, sem voltar para a turma (R52), e o
        aprovado que passa a reprovado continua no nível. Roda na transação de quem chama."""
        etapa = etapa_do_nivel(self._turmas.etapas(turma.id), nivel)
        for situacao in situacoes_na_prova_final(self._turmas, turma.id, etapa):
            prova = situacao.prova
            if prova is None:
                continue
            a_aplicar = resultado_a_aplicar(prova.resultado_aplicado, situacao.resultado)
            if a_aplicar == ResultadoEtapa.APROVADO:
                self._promocoes.aprovar_na_etapa(
                    situacao.aluno_id, turma.materia_id, nivel, agora
                )
                self._turmas.aplicar_resultado(turma.id, nivel, situacao.aluno_id, a_aplicar)

    def _por_em_dia(self, turma: Turma, agora: datetime) -> None:
        materia = self._materias.obter(turma.materia_id)
        mudancas = mudancas_ate(turma, materia.nivel_maximo, agora)
        resultados = self._resultados_que_passam_a_valer(turma, agora)
        perdas = self._perdas_de_vaga(turma, mudancas, agora)
        if not mudancas and not resultados and not perdas:
            return
        # No mesmo momento, a mudança da turma vem antes do que acontece com um aluno.
        eventos: list[tuple[datetime, int, _Evento]] = [
            *((mudanca.em, 0, mudanca) for mudanca in mudancas),
            *((resultado.em, 1, resultado) for resultado in resultados),
            *((perda.em, 1, perda) for perda in perdas),
        ]
        lista = self._turmas.lista_de_espera(turma.id)
        for _, _, evento in sorted(eventos, key=lambda evento: (evento[0], evento[1])):
            if isinstance(evento, _ResultadoQueVale):
                lista = self._aplicar_resultado(turma, materia, evento, lista)
            elif isinstance(evento, _PerdaDaVaga):
                if self._sair_da_turma(turma, evento.aluno_id, evento.em, MotivoDaSaida.ATRASO):
                    lista = self._oferecer_a_vaga(turma, lista, evento.em)
            else:
                self._turmas.aplicar_mudanca(turma.id, evento)
                turma = com_a_mudanca(turma, evento)
                # R50: a lista de espera da etapa que terminou é esvaziada.
                lista = ()
        self._turmas.salvar_lista_de_espera(turma.id, lista)

    def _resultados_que_passam_a_valer(
        self, turma: Turma, agora: datetime
    ) -> list[_ResultadoQueVale]:
        """R49: as notas cujo prazo de correção terminou e cujo resultado ainda não valeu."""
        resultados = []
        for etapa in self._turmas.etapas(turma.id):
            a_valer = [
                prova
                for prova in self._turmas.provas_finais(turma.id, etapa.nivel)
                if prova.resultado_aplicado is None and prova.vale_em <= agora
            ]
            if not a_valer:
                continue
            situacoes = {
                situacao.aluno_id: situacao
                for situacao in situacoes_na_prova_final(self._turmas, turma.id, etapa)
            }
            for prova in a_valer:
                resultado = situacoes[prova.aluno_id].resultado
                resultados.append(
                    _ResultadoQueVale(prova.vale_em, etapa.nivel, prova.aluno_id, resultado)
                )
        return resultados

    def _perdas_de_vaga(
        self, turma: Turma, mudancas: list[MudancaDaTurma], agora: datetime
    ) -> list[_PerdaDaVaga]:
        """R28 e R37: quem não pagou a mensalidade seguinte até o fim da tolerância perde a vaga.
        Depois que a turma encerra, nenhuma mensalidade vence (R54)."""
        encerrada_em = turma.encerrada_em
        for mudanca in mudancas:
            if isinstance(mudanca, Encerramento):
                encerrada_em = mudanca.em
        perdas = []
        for matricula in self._turmas.matriculas_da_turma(turma.id):
            pagas = len(self._turmas.mensalidades(matricula.id))
            devida = proxima_mensalidade(matricula.matriculada_em.date(), pagas)
            if vence(devida, encerrada_em) and devida.perde_a_vaga_em <= agora:
                perdas.append(_PerdaDaVaga(devida.perde_a_vaga_em, matricula.aluno_id))
        return perdas

    def _aplicar_resultado(
        self,
        turma: Turma,
        materia: Materia,
        evento: _ResultadoQueVale,
        lista: ListaDeEspera,
    ) -> ListaDeEspera:
        if evento.resultado == ResultadoEtapa.APROVADO:
            # R08 e R09: o aprovado sobe um nível ou, no nível máximo, conclui a trilha.
            self._promocoes.aprovar_na_etapa(evento.aluno_id, materia.id, evento.nivel, evento.em)
            # R09: a turma encerrou com a etapa, e quem foi aprovado nela sai.
            if turma.encerrada and evento.nivel == turma.nivel:
                self._sair_da_turma(turma, evento.aluno_id, evento.em, MotivoDaSaida.CONCLUSAO)
        elif self._sair_da_turma(turma, evento.aluno_id, evento.em, MotivoDaSaida.REPROVACAO):
            # R21: o reprovado sai da turma.
            lista = self._oferecer_a_vaga(turma, lista, evento.em)
        self._turmas.aplicar_resultado(turma.id, evento.nivel, evento.aluno_id, evento.resultado)
        return lista

    @staticmethod
    def _oferecer_a_vaga(turma: Turma, lista: ListaDeEspera, em: datetime) -> ListaDeEspera:
        """R05 e R45: a vaga de quem saiu vai para o 1º da lista ainda sem oferta, se a etapa
        ainda não chegou à 13ª aula. Os prazos que venceram antes valem primeiro (R35)."""
        pode_oferecer = pode_oferecer_em(turma)
        lista = vencer_prazos(lista, em, pode_oferecer)
        return oferecer_vaga(lista, em, pode_oferecer(em))

    def _sair_da_turma(
        self, turma: Turma, aluno_id: int, em: datetime, motivo: MotivoDaSaida
    ) -> bool:
        """Encerra a matrícula do aluno na turma, se ele ainda está nela."""
        matricula = next(
            (m for m in self._turmas.matriculas_da_turma(turma.id) if m.aluno_id == aluno_id),
            None,
        )
        if matricula is None:
            return False
        self._turmas.encerrar_matricula(matricula.id, em, motivo)
        return True


class AtualizarTurmas:
    """Põe as turmas em dia antes de o app mostrar o que depende delas e não passa por um caso de
    uso das turmas, como o nível do aluno em "Meus níveis"."""

    def __init__(self, em_dia: TurmasEmDia, relogio: Relogio, transacao: Transacao) -> None:
        self._em_dia = em_dia
        self._relogio = relogio
        self._transacao = transacao

    def executar(self) -> None:
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
