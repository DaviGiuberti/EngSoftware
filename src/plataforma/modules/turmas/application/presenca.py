"""Casos de uso das aulas da turma (H21, H22, H08, H24, H32): ver as aulas de uma etapa, a atual
ou uma que terminou, lançar e corrigir a presença e marcar uma aula como não realizada.

A prova final, que também é do professor da turma e do ADM, fica em prova_final.py e usa daqui o
CasoDasAulas e a exigir_professor_da_turma_ou_adm.
"""

from collections import defaultdict
from collections.abc import Collection
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from plataforma.compartilhado.relogio import Relogio
from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.application.casos_de_uso import (
    ConsultaDeAlunos,
    ConsultaDeProfessores,
)
from plataforma.modules.identidade.domain.autorizacao import (
    AcessoNegado,
    exigir_dono,
    exigir_perfil,
)
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.turmas.application.casos_de_uso import (
    ResumoDaTurma,
    obter_turma,
    ocupacao,
    resumir,
)
from plataforma.modules.turmas.application.em_dia import TurmasEmDia
from plataforma.modules.turmas.application.portas import RepositorioDeTurmas
from plataforma.modules.turmas.domain.etapa import (
    Etapa,
    aula_nas_etapas,
    etapa_do_nivel,
    exigir_etapa_em_andamento,
    marcar_nao_realizada,
)
from plataforma.modules.turmas.domain.matricula import aula_de_entrada
from plataforma.modules.turmas.domain.presenca import (
    Presenca,
    alunos_da_aula,
    exigir_aula_para_correcao,
    exigir_aula_para_presenca,
    lancar,
)
from plataforma.modules.turmas.domain.prova_final import exigir_prazo_de_correcao
from plataforma.modules.turmas.domain.turma import Turma

OUTRO_PROFESSOR = "Esta turma é de outro professor."


class SituacaoDaAula(StrEnum):
    NAO_REALIZADA = "nao_realizada"
    FUTURA = "futura"
    SEM_PRESENCA = "sem_presenca"
    COM_PRESENCA = "com_presenca"


@dataclass(frozen=True)
class AlunoNaAula:
    """Um aluno que recebe presença na aula. presente é None até a presença ser lançada."""

    aluno_id: int
    email: str
    presente: bool | None


@dataclass(frozen=True)
class AulaDaTurma:
    """Uma aula da etapa como o professor a vê, com os alunos dela (R08)."""

    inicio: datetime
    numero: int | None
    situacao: SituacaoDaAula
    alunos: tuple[AlunoNaAula, ...] = ()

    @property
    def data(self) -> date:
        return self.inicio.date()


@dataclass(frozen=True)
class EtapaDaTurma:
    """Uma etapa por que a turma passou: o nível, do início da 1ª aula ao fim da 24ª (R17), se é
    a atual e se já terminou."""

    nivel: int
    inicio: datetime
    fim: datetime
    atual: bool
    terminou: bool


@dataclass(frozen=True)
class AulasDaTurma:
    """As aulas da etapa do nivel e as etapas da turma, para escolher outra. em_andamento diz se
    é a etapa atual e ainda não terminou: só nela uma aula vira não realizada (R48)."""

    resumo: ResumoDaTurma
    etapas: tuple[EtapaDaTurma, ...]
    nivel: int
    em_andamento: bool
    aulas: list[AulaDaTurma]


def exigir_professor_da_turma_ou_adm(usuario: Usuario, turma: Turma, acao: str) -> None:
    """R10: o professor só na própria turma; o ADM em qualquer turma."""
    if usuario.perfil == Perfil.ADM:
        return
    if usuario.perfil != Perfil.PROFESSOR:
        raise AcessoNegado(f"Só o professor da turma ou o ADM pode {acao}.")
    exigir_dono(usuario, turma.professor_id, OUTRO_PROFESSOR)


class CasoDasAulas:
    """Dependências e passos comuns aos casos de uso das aulas e da prova final da turma."""

    def __init__(
        self,
        turmas: RepositorioDeTurmas,
        materias: ConsultaDeMaterias,
        professores: ConsultaDeProfessores,
        alunos: ConsultaDeAlunos,
        relogio: Relogio,
        transacao: Transacao,
        em_dia: TurmasEmDia,
    ) -> None:
        self._turmas = turmas
        self._materias = materias
        self._professores = professores
        self._alunos = alunos
        self._relogio = relogio
        self._transacao = transacao
        self._em_dia = em_dia

    def _entradas(self, turma: Turma, etapa: Etapa) -> dict[int, int]:
        """R08: a aula de entrada de cada aluno matriculado na etapa, a partir da qual as faltas
        contam. Quem entrou depois do fim da etapa não tem aula nela."""
        return {
            matricula.aluno_id: aula_de_entrada(etapa.aulas_dadas(matricula.matriculada_em))
            for matricula in self._turmas.matriculas_da_turma(turma.id)
        }


class VerAulasDaTurma(CasoDasAulas):
    """H21 e H22: o professor vê as aulas de uma etapa da turma, as presenças lançadas e o que
    falta lançar. Sem o nível, a etapa é a atual."""

    def executar(
        self, usuario: Usuario, turma_id: int, nivel: int | None = None
    ) -> AulasDaTurma:
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
            turma = obter_turma(self._turmas, turma_id)
            exigir_professor_da_turma_ou_adm(usuario, turma, "ver as aulas da turma")
            etapas = self._turmas.etapas(turma.id)
            etapa = turma.etapa if nivel is None else etapa_do_nivel(etapas, nivel)
            aulas = self._aulas(turma, etapa, agora)
            materia = self._materias.obter(turma.materia_id)
            professor = self._professores.obter(turma.professor_id)
            resumo = resumir(
                turma, ocupacao(self._turmas, turma, agora), materia.nome, professor.email, agora
            )
        return AulasDaTurma(
            resumo=resumo,
            etapas=tuple(
                EtapaDaTurma(e.nivel, e.inicio, e.fim, e.nivel == turma.nivel, e.terminou(agora))
                for e in etapas
            ),
            nivel=etapa.nivel,
            em_andamento=etapa.nivel == turma.nivel and not etapa.terminou(agora),
            aulas=aulas,
        )

    def _aulas(self, turma: Turma, etapa: Etapa, agora: datetime) -> list[AulaDaTurma]:
        entradas = self._entradas(turma, etapa)
        lancadas = self._turmas.datas_com_presenca(turma.id, etapa.nivel)
        por_data: defaultdict[date, list[Presenca]] = defaultdict(list)
        for presenca in self._turmas.presencas(turma.id, etapa.nivel):
            por_data[presenca.data_da_aula].append(presenca)
        emails: dict[int, str] = {}

        def aluno(aluno_id: int, presente: bool | None) -> AlunoNaAula:
            if aluno_id not in emails:
                emails[aluno_id] = self._alunos.obter(aluno_id).email
            return AlunoNaAula(aluno_id, emails[aluno_id], presente)

        aulas = []
        for aula in etapa.calendario():
            if aula.numero is None:
                aulas.append(AulaDaTurma(aula.inicio, None, SituacaoDaAula.NAO_REALIZADA))
            elif aula.data in lancadas:
                lancados = tuple(aluno(p.aluno_id, p.presente) for p in por_data[aula.data])
                aulas.append(
                    AulaDaTurma(aula.inicio, aula.numero, SituacaoDaAula.COM_PRESENCA, lancados)
                )
            elif aula.inicio <= agora:
                da_aula = tuple(aluno(a, None) for a in alunos_da_aula(entradas, aula.numero))
                aulas.append(
                    AulaDaTurma(aula.inicio, aula.numero, SituacaoDaAula.SEM_PRESENCA, da_aula)
                )
            else:
                aulas.append(AulaDaTurma(aula.inicio, aula.numero, SituacaoDaAula.FUTURA))
        return aulas


class LancarPresenca(CasoDasAulas):
    """H21: o professor lança a presença de uma aula da própria turma, e o ADM, de qualquer
    turma (R10). Os alunos da aula que não estão entre os ausentes ficam com presença. A aula
    pode ser de uma etapa que já terminou, como a 24ª depois que a turma passou de nível."""

    def executar(
        self, usuario: Usuario, turma_id: int, data_da_aula: date, ausentes: Collection[int]
    ) -> list[Presenca]:
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
            turma = obter_turma(self._turmas, turma_id)
            exigir_professor_da_turma_ou_adm(usuario, turma, "lançar presença")
            etapa, aula = aula_nas_etapas(self._turmas.etapas(turma.id), data_da_aula)
            ja_lancada = data_da_aula in self._turmas.datas_com_presenca(turma.id, etapa.nivel)
            numero = exigir_aula_para_presenca(aula, agora, ja_lancada)
            alunos = alunos_da_aula(self._entradas(turma, etapa), numero)
            presencas = lancar(data_da_aula, alunos, ausentes)
            self._turmas.lancar_presenca(
                turma.id, etapa.nivel, data_da_aula, presencas, agora, usuario.id
            )
            return presencas


class CorrigirPresenca(CasoDasAulas):
    """H24 e H32: o professor corrige a presença de uma aula da própria turma até 72 horas depois
    de lançá-la; depois, só o ADM, em qualquer turma (R10, R22). Os alunos da aula continuam os
    mesmos, e os que não estão entre os ausentes ficam com presença."""

    def executar(
        self, usuario: Usuario, turma_id: int, data_da_aula: date, ausentes: Collection[int]
    ) -> list[Presenca]:
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
            turma = obter_turma(self._turmas, turma_id)
            exigir_professor_da_turma_ou_adm(usuario, turma, "corrigir presença")
            etapa, aula = aula_nas_etapas(self._turmas.etapas(turma.id), data_da_aula)
            lancamentos = self._turmas.lancamentos_de_presenca(turma.id, etapa.nivel)
            lancada_em = exigir_aula_para_correcao(aula, lancamentos.get(data_da_aula))
            exigir_prazo_de_correcao(lancada_em, agora, pelo_adm=usuario.perfil == Perfil.ADM)
            da_aula = [
                presenca.aluno_id
                for presenca in self._turmas.presencas(turma.id, etapa.nivel)
                if presenca.data_da_aula == data_da_aula
            ]
            presencas = lancar(data_da_aula, da_aula, ausentes)
            self._turmas.corrigir_presenca(
                turma.id, etapa.nivel, data_da_aula, presencas, agora, usuario.id
            )
            self._em_dia.reavaliar(turma, etapa.nivel, agora)
            return presencas


class MarcarAulaNaoRealizada(CasoDasAulas):
    """H22: o professor marca uma aula da própria turma, ainda sem presença, como não realizada.
    Ela sai das 24 e é reposta no fim da etapa (R18, R48). A etapa que terminou não muda mais."""

    def executar(self, usuario: Usuario, turma_id: int, data: date) -> None:
        exigir_perfil(usuario, Perfil.PROFESSOR, "marcar aula como não realizada")
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
            turma = obter_turma(self._turmas, turma_id)
            exigir_dono(usuario, turma.professor_id, OUTRO_PROFESSOR)
            exigir_etapa_em_andamento(turma.etapa, agora)
            com_presenca = self._turmas.datas_com_presenca(turma.id, turma.nivel)
            marcar_nao_realizada(turma.calendario(), turma.nao_realizadas, data, com_presenca)
            self._turmas.marcar_nao_realizada(turma.id, turma.nivel, data, agora)


@dataclass(frozen=True)
class CasosDeUsoDasAulas:
    """Os casos de uso das aulas da turma, montados pelo main.py e entregues às telas."""

    ver_aulas: VerAulasDaTurma
    lancar_presenca: LancarPresenca
    corrigir_presenca: CorrigirPresenca
    marcar_nao_realizada: MarcarAulaNaoRealizada
