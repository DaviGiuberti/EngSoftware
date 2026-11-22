"""Casos de uso da prova final (H23, H24, H32): ver a prova final de uma etapa, lançar a nota de
cada aluno depois da 24ª aula (R17, R20) e corrigi-la. O professor faz isso só nas próprias
turmas, e o ADM em qualquer uma (R10). O professor corrige até 72 horas depois do lançamento, e o
ADM a qualquer momento; depois que o resultado valeu, o nível só sobe (R22, R49)."""

from dataclasses import dataclass, replace
from datetime import datetime

from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.turmas.application.casos_de_uso import obter_turma
from plataforma.modules.turmas.application.em_dia import situacoes_na_prova_final
from plataforma.modules.turmas.application.presenca import (
    CasoDasAulas,
    exigir_professor_da_turma_ou_adm,
)
from plataforma.modules.turmas.domain.etapa import Etapa, etapa_do_nivel
from plataforma.modules.turmas.domain.prova_final import (
    ProvaFinal,
    ResultadoEtapa,
    exigir_fim_da_etapa,
    exigir_nota,
    exigir_prazo_de_correcao,
    exigir_sem_nota,
    ler_nota,
    matricula_na_etapa,
)
from plataforma.modules.turmas.domain.turma import Turma


@dataclass(frozen=True)
class AlunoNaProvaFinal:
    """Um aluno da etapa como o professor e o ADM o veem na prova final: as faltas, a prova, se
    a nota já foi lançada, e o resultado (R08)."""

    aluno_id: int
    email: str
    faltas: int
    prova: ProvaFinal | None
    resultado: ResultadoEtapa


@dataclass(frozen=True)
class ProvaFinalDaEtapa:
    """A prova final de uma etapa: quando ela termina (R17) e os alunos que estavam na turma
    nesse momento (R23)."""

    nivel: int
    fim_da_etapa: datetime
    terminou: bool
    alunos: list[AlunoNaProvaFinal]


class _CasoDaProvaFinal(CasoDasAulas):
    """Passos comuns aos casos de uso da prova final."""

    def _turma_e_etapa(
        self, usuario: Usuario, turma_id: int, nivel: int, acao: str
    ) -> tuple[Turma, Etapa]:
        """R10: a turma, se ela é do professor ou o usuário é o ADM, e a etapa do nível."""
        turma = obter_turma(self._turmas, turma_id)
        exigir_professor_da_turma_ou_adm(usuario, turma, acao)
        return turma, etapa_do_nivel(self._turmas.etapas(turma.id), nivel)

    def _prova(self, turma_id: int, nivel: int, aluno_id: int) -> ProvaFinal | None:
        provas = self._turmas.provas_finais(turma_id, nivel)
        return next((prova for prova in provas if prova.aluno_id == aluno_id), None)


class VerProvaFinal(_CasoDaProvaFinal):
    """H23: o professor da turma e o ADM veem a prova final de uma etapa, com as faltas, a nota
    e o resultado de cada aluno."""

    def executar(self, usuario: Usuario, turma_id: int, nivel: int) -> ProvaFinalDaEtapa:
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
            turma, etapa = self._turma_e_etapa(
                usuario, turma_id, nivel, "ver a prova final da turma"
            )
            alunos = [
                AlunoNaProvaFinal(
                    situacao.aluno_id,
                    self._alunos.obter(situacao.aluno_id).email,
                    situacao.faltas,
                    situacao.prova,
                    situacao.resultado,
                )
                for situacao in situacoes_na_prova_final(self._turmas, turma.id, etapa)
            ]
        return ProvaFinalDaEtapa(etapa.nivel, etapa.fim, etapa.terminou(agora), alunos)


class LancarNota(_CasoDaProvaFinal):
    """H23 e H32: depois da 24ª aula, o professor da turma ou o ADM lança a nota de cada aluno
    que estava na turma no fim da etapa (R10, R17, R20, R23)."""

    def executar(
        self, usuario: Usuario, turma_id: int, nivel: int, aluno_id: int, nota: str
    ) -> ProvaFinal:
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
            turma, etapa = self._turma_e_etapa(
                usuario, turma_id, nivel, "lançar a nota da prova final"
            )
            exigir_fim_da_etapa(etapa.fim, agora)
            valor = ler_nota(nota)
            matricula_na_etapa(self._turmas.todas_as_matriculas(turma.id), aluno_id, etapa.fim)
            aluno = self._alunos.obter(aluno_id)
            exigir_sem_nota(self._prova(turma.id, etapa.nivel, aluno_id), aluno.email)
            prova = ProvaFinal(aluno_id, valor, agora)
            self._turmas.lancar_prova_final(turma.id, etapa.nivel, prova, usuario.id)
            return prova


class CorrigirNota(_CasoDaProvaFinal):
    """H24 e H32: o professor corrige a nota até 72 horas depois do lançamento; depois, só o
    ADM. Se o resultado já valeu, a correção só muda o nível para cima (R22, R49)."""

    def executar(
        self, usuario: Usuario, turma_id: int, nivel: int, aluno_id: int, nota: str
    ) -> ProvaFinal:
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
            turma, etapa = self._turma_e_etapa(
                usuario, turma_id, nivel, "corrigir a nota da prova final"
            )
            valor = ler_nota(nota)
            aluno = self._alunos.obter(aluno_id)
            prova = exigir_nota(self._prova(turma.id, etapa.nivel, aluno_id), aluno.email)
            exigir_prazo_de_correcao(
                prova.lancada_em, agora, pelo_adm=usuario.perfil == Perfil.ADM
            )
            self._turmas.corrigir_prova_final(
                turma.id, etapa.nivel, aluno_id, valor, agora, usuario.id
            )
            self._em_dia.reavaliar(turma, etapa.nivel, agora)
            return replace(prova, nota=valor)


@dataclass(frozen=True)
class CasosDeUsoDaProvaFinal:
    """Os casos de uso da prova final, montados pelo main.py e entregues às telas."""

    ver_prova_final: VerProvaFinal
    lancar_nota: LancarNota
    corrigir_nota: CorrigirNota
