"""Casos de uso do aluno nas turmas (H04, H05, H06, H07, H13, H08): ver as turmas do nível dele,
matricular-se pagando a primeira mensalidade, entrar na lista de espera, confirmar a vaga
oferecida e sair da turma. Nas turmas em que está, o aluno vê as faltas da etapa e a prova final
da última etapa que terminou."""

from dataclasses import dataclass
from datetime import date, datetime

from plataforma.compartilhado.relogio import Relogio
from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.application.casos_de_uso import ConsultaDeProfessores
from plataforma.modules.identidade.domain.autorizacao import exigir_perfil
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.materias.domain.materia import Materia
from plataforma.modules.nivelamento.application.consulta_de_niveis import ConsultaDeNiveis
from plataforma.modules.turmas.application.casos_de_uso import (
    ResumoDaTurma,
    obter_turma,
    ocupacao,
    resumir,
)
from plataforma.modules.turmas.application.em_dia import (
    SituacaoNaProvaFinal,
    TurmasEmDia,
    situacoes_na_prova_final,
)
from plataforma.modules.turmas.application.portas import RepositorioDeTurmas
from plataforma.modules.turmas.domain.lista_de_espera import (
    confirmar,
    entrar,
    exigir_lista_aberta,
    exigir_turma_cheia,
    oferecer_vaga,
    pode_oferecer_em,
    posicao,
    reservadas,
    sair,
)
from plataforma.modules.turmas.domain.matricula import (
    Matricula,
    SemMatricula,
    SituacaoNaTurma,
    aula_de_entrada,
    exigir_aluno_livre,
    exigir_matricula_aberta,
    exigir_nivel_da_turma,
    exigir_sem_turma_na_materia,
    exigir_vaga,
    situacao_na_turma,
)
from plataforma.modules.turmas.domain.mensalidade import (
    primeira_mensalidade,
    proximo_vencimento,
)
from plataforma.modules.turmas.domain.presenca import faltas_na_etapa
from plataforma.modules.turmas.domain.turma import Turma, exigir_aberta, horarios_ocupados


@dataclass(frozen=True)
class TurmaDoAluno:
    """Uma turma como o aluno a vê: a turma, a situação dele nela e o valor da mensalidade. Na
    turma em que ele está, também as faltas dele na etapa (R08) e a prova final da última etapa
    que ele terminou nela, com a nota e o resultado (R49)."""

    resumo: ResumoDaTurma
    situacao: SituacaoNaTurma
    mensalidade_em_centavos: int
    posicao_na_lista: int | None = None
    prazo_para_confirmar: datetime | None = None
    proximo_vencimento: date | None = None
    faltas: int | None = None
    prova_final: SituacaoNaProvaFinal | None = None


@dataclass(frozen=True)
class MatriculaFeita:
    """A matrícula, a aula a partir da qual as faltas contam (R08), o valor pago e o vencimento
    da próxima mensalidade (R27, R46)."""

    matricula: Matricula
    aula_de_entrada: int
    valor_pago_em_centavos: int
    proximo_vencimento: date


class _CasoDoAluno:
    """Dependências e passos comuns aos casos de uso do aluno nas turmas."""

    def __init__(
        self,
        turmas: RepositorioDeTurmas,
        materias: ConsultaDeMaterias,
        professores: ConsultaDeProfessores,
        niveis: ConsultaDeNiveis,
        relogio: Relogio,
        transacao: Transacao,
        em_dia: TurmasEmDia,
    ) -> None:
        self._turmas = turmas
        self._materias = materias
        self._professores = professores
        self._niveis = niveis
        self._relogio = relogio
        self._transacao = transacao
        self._em_dia = em_dia

    def _turma_e_materia(self, turma_id: int) -> tuple[Turma, Materia]:
        turma = obter_turma(self._turmas, turma_id)
        return turma, self._materias.obter(turma.materia_id)

    def _exigir_nivel_e_nenhuma_turma_na_materia(
        self, aluno: Usuario, turma: Turma, materia: Materia
    ) -> list[Turma]:
        """R06 e R44. Devolve as turmas em que o aluno já está, para conferir a R07."""
        nivel = self._niveis.nivel_do_aluno(aluno.id, materia.id)
        exigir_nivel_da_turma(nivel, turma.nivel, materia.nome)
        minhas = [
            obter_turma(self._turmas, matricula.turma_id)
            for matricula in self._turmas.matriculas_do_aluno(aluno.id)
        ]
        tem_turma_na_materia = any(minha.materia_id == materia.id for minha in minhas)
        exigir_sem_turma_na_materia(tem_turma_na_materia, materia.nome)
        return minhas

    def _exigir_que_pode_entrar(
        self, aluno: Usuario, turma: Turma, materia: Materia, agora: datetime
    ) -> None:
        """R09, R06, R44, R07 e R19: valem na matrícula e na confirmação da vaga (R47)."""
        exigir_aberta(turma)
        minhas = self._exigir_nivel_e_nenhuma_turma_na_materia(aluno, turma, materia)
        exigir_aluno_livre(turma.horario, horarios_ocupados(minhas))
        exigir_matricula_aberta(turma.aulas_dadas(agora))

    def _matricular(
        self, aluno: Usuario, turma: Turma, materia: Materia, agora: datetime
    ) -> MatriculaFeita:
        """R27: a matrícula começa com o pagamento da 1ª mensalidade, no valor da matéria.

        R44: matriculado, o aluno sai das listas de espera das turmas da mesma matéria.
        """
        primeira = primeira_mensalidade(materia.mensalidade_em_centavos, agora)
        matricula = self._turmas.adicionar_matricula(turma.id, aluno.id, agora, primeira)
        self._sair_das_listas_da_materia(aluno, materia, agora)
        return MatriculaFeita(
            matricula=matricula,
            aula_de_entrada=aula_de_entrada(turma.aulas_dadas(agora)),
            valor_pago_em_centavos=primeira.valor_em_centavos,
            proximo_vencimento=proximo_vencimento(agora.date(), mensalidades_pagas=1),
        )

    def _sair_das_listas_da_materia(
        self, aluno: Usuario, materia: Materia, agora: datetime
    ) -> None:
        for turma_id in self._turmas.turmas_com_o_aluno_na_lista(aluno.id):
            turma = obter_turma(self._turmas, turma_id)
            if turma.materia_id != materia.id:
                continue
            lista = ocupacao(self._turmas, turma, agora).lista
            pode_oferecer = pode_oferecer_em(turma)(agora)
            self._turmas.salvar_lista_de_espera(
                turma.id, sair(lista, aluno.id, agora, pode_oferecer)
            )


class VerTurmasDoAluno(_CasoDoAluno):
    """H04: o aluno vê as turmas do nível dele em cada matéria e as turmas em que está. A turma
    encerrada só aparece para quem ainda está nela (R09)."""

    def executar(self, aluno: Usuario) -> list[TurmaDoAluno]:
        exigir_perfil(aluno, Perfil.ALUNO, "ver as turmas do seu nível")
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
            return self._ver(aluno, agora)

    def _ver(self, aluno: Usuario, agora: datetime) -> list[TurmaDoAluno]:
        niveis = self._niveis.niveis_do_aluno(aluno.id)
        minhas = {m.turma_id: m for m in self._turmas.matriculas_do_aluno(aluno.id)}
        materias = {materia.id: materia for materia in self._materias.listar()}
        emails = {professor.id: professor.email for professor in self._professores.listar()}
        vistas = []
        for turma in self._turmas.listar():
            matricula = minhas.get(turma.id)
            do_nivel = not turma.encerrada and niveis.get(turma.materia_id) == turma.nivel
            if matricula is None and not do_nivel:
                continue
            ocupada = ocupacao(self._turmas, turma, agora)
            na_lista = next((n for n in ocupada.lista if n.aluno_id == aluno.id), None)
            materia = materias[turma.materia_id]
            vistas.append(
                TurmaDoAluno(
                    resumo=resumir(
                        turma, ocupada, materia.nome, emails[turma.professor_id], agora
                    ),
                    situacao=situacao_na_turma(
                        matriculado=matricula is not None,
                        na_lista=na_lista is not None,
                        com_oferta=na_lista is not None and na_lista.prazo is not None,
                        vagas_livres=ocupada.vagas_livres,
                    ),
                    mensalidade_em_centavos=materia.mensalidade_em_centavos,
                    posicao_na_lista=posicao(ocupada.lista, aluno.id) if na_lista else None,
                    prazo_para_confirmar=na_lista.prazo if na_lista else None,
                    proximo_vencimento=self._proximo_vencimento(matricula),
                    faltas=self._faltas(turma, matricula),
                    prova_final=self._prova_final(turma, aluno, agora) if matricula else None,
                )
            )
        return sorted(vistas, key=lambda vista: (vista.resumo.nome_da_materia, vista.resumo.id))

    def _proximo_vencimento(self, matricula: Matricula | None) -> date | None:
        """R27 e R46: o vencimento da mensalidade seguinte às que o aluno já pagou."""
        if matricula is None:
            return None
        pagas = len(self._turmas.mensalidades(matricula.id))
        return proximo_vencimento(matricula.matriculada_em.date(), pagas)

    def _faltas(self, turma: Turma, matricula: Matricula | None) -> int | None:
        """R08: as faltas do aluno na etapa, a partir da aula em que ele entrou na turma."""
        if matricula is None:
            return None
        presencas = self._turmas.presencas(turma.id, turma.nivel)
        return faltas_na_etapa(
            turma.etapa, matricula.aluno_id, matricula.matriculada_em, presencas
        )

    def _prova_final(
        self, turma: Turma, aluno: Usuario, agora: datetime
    ) -> SituacaoNaProvaFinal | None:
        """R08, R23 e R49: a prova final da última etapa que terminou com o aluno na turma."""
        for etapa in reversed(self._turmas.etapas(turma.id)):
            if not etapa.terminou(agora):
                continue
            situacoes = situacoes_na_prova_final(self._turmas, turma.id, etapa)
            situacao = next((s for s in situacoes if s.aluno_id == aluno.id), None)
            if situacao is not None:
                return situacao
        return None


class Matricular(_CasoDoAluno):
    """H04: o aluno se matricula numa turma do nível dele e paga a primeira mensalidade."""

    def executar(self, aluno: Usuario, turma_id: int) -> MatriculaFeita:
        exigir_perfil(aluno, Perfil.ALUNO, "se matricular numa turma")
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
            turma, materia = self._turma_e_materia(turma_id)
            self._exigir_que_pode_entrar(aluno, turma, materia, agora)
            ocupada = ocupacao(self._turmas, turma, agora)
            exigir_vaga(len(ocupada.matriculas), reservadas(ocupada.lista))
            self._turmas.salvar_lista_de_espera(turma.id, ocupada.lista)
            return self._matricular(aluno, turma, materia, agora)


class EntrarNaListaDeEspera(_CasoDoAluno):
    """H05: numa turma cheia do nível dele, o aluno entra no fim da lista de espera."""

    def executar(self, aluno: Usuario, turma_id: int) -> int:
        """Devolve o lugar do aluno na lista."""
        exigir_perfil(aluno, Perfil.ALUNO, "entrar na lista de espera")
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
            turma, materia = self._turma_e_materia(turma_id)
            exigir_aberta(turma)
            self._exigir_nivel_e_nenhuma_turma_na_materia(aluno, turma, materia)
            exigir_lista_aberta(turma.aulas_dadas(agora))
            ocupada = ocupacao(self._turmas, turma, agora)
            exigir_turma_cheia(ocupada.vagas_livres)
            lista = entrar(ocupada.lista, aluno.id, agora)
            self._turmas.salvar_lista_de_espera(turma.id, lista)
            return posicao(lista, aluno.id)


class ConfirmarVaga(_CasoDoAluno):
    """H06: dentro do prazo, o aluno confirma a vaga oferecida, o que é se matricular (R47)."""

    def executar(self, aluno: Usuario, turma_id: int) -> MatriculaFeita:
        exigir_perfil(aluno, Perfil.ALUNO, "confirmar a vaga")
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
            turma, materia = self._turma_e_materia(turma_id)
            lista = confirmar(
                self._turmas.lista_de_espera(turma.id), aluno.id, agora, pode_oferecer_em(turma)
            )
            self._exigir_que_pode_entrar(aluno, turma, materia, agora)
            self._turmas.salvar_lista_de_espera(turma.id, lista)
            return self._matricular(aluno, turma, materia, agora)


class SairDaTurma(_CasoDoAluno):
    """H13: o aluno sai da turma, sem reembolso da mensalidade (R29), e a vaga vai para o 1º da
    lista de espera (R05)."""

    def executar(self, aluno: Usuario, turma_id: int) -> None:
        exigir_perfil(aluno, Perfil.ALUNO, "sair da turma")
        agora = self._relogio.agora()
        with self._transacao():
            self._em_dia.aplicar(agora)
            turma = obter_turma(self._turmas, turma_id)
            matricula = next(
                (m for m in self._turmas.matriculas_da_turma(turma.id) if m.aluno_id == aluno.id),
                None,
            )
            if matricula is None:
                raise SemMatricula()
            self._turmas.encerrar_matricula(matricula.id, agora)
            lista = ocupacao(self._turmas, turma, agora).lista
            pode_oferecer = pode_oferecer_em(turma)(agora)
            self._turmas.salvar_lista_de_espera(
                turma.id, oferecer_vaga(lista, agora, pode_oferecer)
            )


@dataclass(frozen=True)
class CasosDeUsoDaMatricula:
    """Os casos de uso do aluno nas turmas, montados pelo main.py e entregues às telas."""

    ver_turmas_do_aluno: VerTurmasDoAluno
    matricular: Matricular
    entrar_na_lista: EntrarNaListaDeEspera
    confirmar_vaga: ConfirmarVaga
    sair_da_turma: SairDaTurma
