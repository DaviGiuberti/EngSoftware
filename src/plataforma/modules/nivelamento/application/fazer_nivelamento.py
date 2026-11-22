"""Casos de uso do nivelamento que o aluno faz (H01, H02, H03) e das exceções do ADM (H33)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import cast

from plataforma.compartilhado.relogio import Relogio
from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.application.casos_de_uso import ConsultaDeAlunos
from plataforma.modules.identidade.domain.autorizacao import exigir_dono, exigir_perfil
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.materias.domain.materia import Materia, nivel_da_nota
from plataforma.modules.nivelamento.application.portas import (
    RepositorioDeNivelamentos,
    RepositorioDeQuestoes,
)
from plataforma.modules.nivelamento.domain.nivelamento import (
    Nivelamento,
    NivelamentoNaoEncontrado,
    NivelDoAluno,
    SituacaoNaMateria,
    abrir,
    acabou,
    com_mais_tempo,
    concluir,
    exigir_aberto,
    exigir_em_andamento,
    exigir_que_pode_iniciar,
    exigir_que_pode_liberar,
    fechar,
    nivel_depois_do_nivelamento,
    registrar,
    responder,
    restante,
    situacao_na_materia,
)
from plataforma.modules.nivelamento.domain.nota import corrigir
from plataforma.modules.nivelamento.domain.questao import (
    Questao,
    QuestaoParaResponder,
    exigir_questoes,
    para_responder,
)


@dataclass(frozen=True)
class Resultado:
    """A nota do nivelamento e o nível do aluno na matéria depois dele (R42)."""

    nota: int
    nivel: int


@dataclass(frozen=True)
class EstadoDoNivelamento:
    """O que a tela do teste mostra. As questões vêm sem a alternativa correta."""

    nivelamento_id: int
    nome_da_materia: str
    questoes: tuple[QuestaoParaResponder, ...]
    respostas: Mapping[int, int]
    tempo_restante: timedelta
    resultado: Resultado | None = None


@dataclass(frozen=True)
class NivelNaMateria:
    """Uma linha do perfil do aluno (H03), com a trilha concluída no nível máximo (R09)."""

    materia_id: int
    nome_da_materia: str
    nivel: int | None
    situacao: SituacaoNaMateria
    trilha_concluida: bool = False


class _CasoDoNivelamento:
    """Dependências e passos comuns dos casos de uso do aluno no teste."""

    def __init__(
        self,
        nivelamentos: RepositorioDeNivelamentos,
        questoes: RepositorioDeQuestoes,
        materias: ConsultaDeMaterias,
        relogio: Relogio,
        transacao: Transacao,
    ) -> None:
        self._nivelamentos = nivelamentos
        self._questoes = questoes
        self._materias = materias
        self._relogio = relogio
        self._transacao = transacao

    def _do_aluno(self, usuario: Usuario, nivelamento_id: int) -> Nivelamento:
        """RNF07: só o aluno mexe no nivelamento, e só no próprio."""
        exigir_perfil(usuario, Perfil.ALUNO, "fazer o nivelamento")
        nivelamento = self._nivelamentos.buscar(nivelamento_id)
        if nivelamento is None:
            raise NivelamentoNaoEncontrado()
        exigir_dono(usuario, nivelamento.aluno_id, "Este nivelamento é de outro aluno.")
        return nivelamento

    def _materia_e_questoes(self, materia_id: int) -> tuple[Materia, list[Questao]]:
        return self._materias.obter(materia_id), self._questoes.listar(materia_id)

    def _contar_o_tempo(
        self,
        nivelamento: Nivelamento,
        materia: Materia,
        questoes: Sequence[Questao],
        agora: datetime,
    ) -> Nivelamento:
        """Soma o tempo que correu. Se os 60 minutos acabaram, encerra e corrige (R34)."""
        nivelamento = replace(nivelamento, tempo=registrar(nivelamento.tempo, agora))
        if acabou(nivelamento.tempo, agora):
            return self._concluir(nivelamento, materia, questoes, agora)
        return nivelamento

    def _concluir(
        self,
        nivelamento: Nivelamento,
        materia: Materia,
        questoes: Sequence[Questao],
        agora: datetime,
    ) -> Nivelamento:
        """Corrige (R34), acha o nível da nota (R02) e atualiza o nível do aluno (R42)."""
        nota = corrigir(questoes, nivelamento.respostas)
        nivel = nivel_da_nota(materia.faixas, nota)
        atual = self._nivelamentos.nivel_do_aluno(nivelamento.aluno_id, materia.id)
        novo = nivel_depois_do_nivelamento(atual.nivel if atual else None, nivel)
        self._nivelamentos.salvar_nivel(nivelamento.aluno_id, NivelDoAluno(materia.id, novo))
        return concluir(nivelamento, agora, nota, nivel)

    def _estado(
        self,
        nivelamento: Nivelamento,
        materia: Materia,
        questoes: Sequence[Questao],
        agora: datetime,
    ) -> EstadoDoNivelamento:
        resultado = None
        if nivelamento.conclusao is not None:
            atual = self._nivelamentos.nivel_do_aluno(nivelamento.aluno_id, materia.id)
            nivel = atual.nivel if atual else nivelamento.conclusao.nivel
            resultado = Resultado(nivelamento.conclusao.nota, nivel)
        return EstadoDoNivelamento(
            nivelamento_id=nivelamento.id,
            nome_da_materia=materia.nome,
            questoes=tuple(para_responder(questao) for questao in questoes),
            respostas=dict(nivelamento.respostas),
            tempo_restante=restante(nivelamento.tempo, agora),
            resultado=resultado,
        )


class IniciarNivelamento(_CasoDoNivelamento):
    """O aluno abre o nivelamento de uma matéria: começa um novo ou retoma o que deixou aberto."""

    def executar(self, usuario: Usuario, materia_id: int) -> EstadoDoNivelamento:
        exigir_perfil(usuario, Perfil.ALUNO, "fazer o nivelamento")
        materia, questoes = self._materia_e_questoes(materia_id)
        agora = self._relogio.agora()
        with self._transacao():
            nivelamento = self._nivelamentos.buscar_em_andamento(usuario.id, materia.id)
            if nivelamento is None:
                nivelamento = self._comecar(usuario, materia, questoes, agora)
            nivelamento = replace(nivelamento, tempo=abrir(nivelamento.tempo, agora))
            if acabou(nivelamento.tempo, agora):
                nivelamento = self._concluir(nivelamento, materia, questoes, agora)
            self._nivelamentos.salvar(nivelamento)
            return self._estado(nivelamento, materia, questoes, agora)

    def _comecar(
        self, usuario: Usuario, materia: Materia, questoes: Sequence[Questao], agora: datetime
    ) -> Nivelamento:
        exigir_questoes(materia.nome, len(questoes))
        nivel = self._nivelamentos.nivel_do_aluno(usuario.id, materia.id)
        exigir_que_pode_iniciar(
            materia.nome,
            tem_nivel=nivel is not None,
            refazer_liberado=nivel is not None and nivel.refazer_liberado,
        )
        if nivel is not None:
            # R03: a liberação do ADM vale para uma tentativa.
            self._nivelamentos.salvar_nivel(usuario.id, replace(nivel, refazer_liberado=False))
        return self._nivelamentos.criar(usuario.id, materia.id, agora)


class ResponderQuestao(_CasoDoNivelamento):
    def executar(
        self, usuario: Usuario, nivelamento_id: int, questao_id: int, posicao: int
    ) -> EstadoDoNivelamento:
        agora = self._relogio.agora()
        with self._transacao():
            nivelamento = self._do_aluno(usuario, nivelamento_id)
            exigir_aberto(nivelamento)
            materia, questoes = self._materia_e_questoes(nivelamento.materia_id)
            nivelamento = self._contar_o_tempo(nivelamento, materia, questoes, agora)
            # R34: a resposta que chega depois do fim do tempo não conta.
            if nivelamento.conclusao is None:
                ids_das_questoes = {questao.id for questao in questoes}
                nivelamento = responder(nivelamento, ids_das_questoes, questao_id, posicao)
            self._nivelamentos.salvar(nivelamento)
            return self._estado(nivelamento, materia, questoes, agora)


class RegistrarTempo(_CasoDoNivelamento):
    """A tela registra o tempo a cada poucos segundos. Se o app cair, perde-se só o intervalo."""

    def executar(self, usuario: Usuario, nivelamento_id: int) -> EstadoDoNivelamento:
        agora = self._relogio.agora()
        with self._transacao():
            nivelamento = self._do_aluno(usuario, nivelamento_id)
            materia, questoes = self._materia_e_questoes(nivelamento.materia_id)
            if nivelamento.conclusao is None:
                nivelamento = self._contar_o_tempo(nivelamento, materia, questoes, agora)
                self._nivelamentos.salvar(nivelamento)
            return self._estado(nivelamento, materia, questoes, agora)


class FecharNivelamento(_CasoDoNivelamento):
    """O aluno sai do teste sem entregar: o tempo para de correr (R30)."""

    def executar(self, usuario: Usuario, nivelamento_id: int) -> None:
        agora = self._relogio.agora()
        with self._transacao():
            nivelamento = self._do_aluno(usuario, nivelamento_id)
            if nivelamento.conclusao is None:
                fechado = replace(nivelamento, tempo=fechar(nivelamento.tempo, agora))
                self._nivelamentos.salvar(fechado)


class ConcluirNivelamento(_CasoDoNivelamento):
    """O aluno entrega o teste antes do fim do tempo."""

    def executar(self, usuario: Usuario, nivelamento_id: int) -> EstadoDoNivelamento:
        agora = self._relogio.agora()
        with self._transacao():
            nivelamento = self._do_aluno(usuario, nivelamento_id)
            exigir_aberto(nivelamento)
            materia, questoes = self._materia_e_questoes(nivelamento.materia_id)
            nivelamento = self._contar_o_tempo(nivelamento, materia, questoes, agora)
            if nivelamento.conclusao is None:
                nivelamento = self._concluir(nivelamento, materia, questoes, agora)
            self._nivelamentos.salvar(nivelamento)
            return self._estado(nivelamento, materia, questoes, agora)


class VerMeusNiveis:
    """O aluno vê o nível e a situação do nivelamento em cada matéria (H03)."""

    def __init__(
        self,
        nivelamentos: RepositorioDeNivelamentos,
        questoes: RepositorioDeQuestoes,
        materias: ConsultaDeMaterias,
    ) -> None:
        self._nivelamentos = nivelamentos
        self._questoes = questoes
        self._materias = materias

    def executar(self, usuario: Usuario) -> list[NivelNaMateria]:
        exigir_perfil(usuario, Perfil.ALUNO, "ver os próprios níveis")
        niveis = {n.materia_id: n for n in self._nivelamentos.niveis_do_aluno(usuario.id)}
        em_andamento = self._nivelamentos.materias_em_andamento(usuario.id)
        trilhas_concluidas = self._nivelamentos.trilhas_concluidas(usuario.id)
        questoes_por_materia = self._questoes.contar_por_materia()
        linhas = []
        for materia in self._materias.listar():
            nivel = niveis.get(materia.id)
            situacao = situacao_na_materia(
                nivel.nivel if nivel else None,
                refazer_liberado=nivel is not None and nivel.refazer_liberado,
                em_andamento=materia.id in em_andamento,
                quantidade_de_questoes=questoes_por_materia.get(materia.id, 0),
            )
            linhas.append(
                NivelNaMateria(
                    materia.id,
                    materia.nome,
                    nivel.nivel if nivel else None,
                    situacao,
                    trilha_concluida=materia.id in trilhas_concluidas,
                )
            )
        return linhas


class DarMaisTempo:
    """O ADM dá minutos a mais a um aluno que está fazendo o nivelamento (R30)."""

    def __init__(
        self,
        nivelamentos: RepositorioDeNivelamentos,
        materias: ConsultaDeMaterias,
        alunos: ConsultaDeAlunos,
        relogio: Relogio,
        transacao: Transacao,
    ) -> None:
        self._nivelamentos = nivelamentos
        self._materias = materias
        self._alunos = alunos
        self._relogio = relogio
        self._transacao = transacao

    def executar(
        self, usuario: Usuario, email_do_aluno: str, materia_id: int, minutos: int
    ) -> timedelta:
        """Devolve o tempo que o aluno passa a ter."""
        exigir_perfil(usuario, Perfil.ADM, "dar mais tempo no nivelamento")
        aluno = self._alunos.obter_por_email(email_do_aluno)
        materia = self._materias.obter(materia_id)
        agora = self._relogio.agora()
        with self._transacao():
            em_andamento = self._nivelamentos.buscar_em_andamento(aluno.id, materia.id)
            exigir_em_andamento(materia.nome, em_andamento=em_andamento is not None)
            nivelamento = cast(Nivelamento, em_andamento)
            nivelamento = replace(nivelamento, tempo=com_mais_tempo(nivelamento.tempo, minutos))
            self._nivelamentos.salvar(nivelamento)
            return restante(nivelamento.tempo, agora)


class LiberarRefazer:
    """O ADM libera que o aluno refaça o nivelamento de uma matéria uma vez (R03, R42)."""

    def __init__(
        self,
        nivelamentos: RepositorioDeNivelamentos,
        materias: ConsultaDeMaterias,
        alunos: ConsultaDeAlunos,
        transacao: Transacao,
    ) -> None:
        self._nivelamentos = nivelamentos
        self._materias = materias
        self._alunos = alunos
        self._transacao = transacao

    def executar(self, usuario: Usuario, email_do_aluno: str, materia_id: int) -> None:
        exigir_perfil(usuario, Perfil.ADM, "liberar que o aluno refaça o nivelamento")
        aluno = self._alunos.obter_por_email(email_do_aluno)
        materia = self._materias.obter(materia_id)
        with self._transacao():
            atual = self._nivelamentos.nivel_do_aluno(aluno.id, materia.id)
            em_andamento = self._nivelamentos.buscar_em_andamento(aluno.id, materia.id)
            exigir_que_pode_liberar(
                materia.nome, tem_nivel=atual is not None, em_andamento=em_andamento is not None
            )
            nivel = cast(NivelDoAluno, atual)
            self._nivelamentos.salvar_nivel(aluno.id, replace(nivel, refazer_liberado=True))
