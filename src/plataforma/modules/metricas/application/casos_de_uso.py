"""Caso de uso das métricas (H36): o ADM vê a M1, a M2 e a M3 de um mês (R64 a R67).

Os dados vêm das consultas públicas do nivelamento, das turmas e do catálogo (ADR 0002): o
metricas não tem tabela própria e calcula os números na hora.
"""

from dataclasses import dataclass

from plataforma.compartilhado.relogio import Relogio
from plataforma.modules.catalogo.application.aulas_do_aluno import ConsultaDeAulasConcluidas
from plataforma.modules.identidade.domain.autorizacao import exigir_perfil
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.metricas.domain.metricas import (
    AtividadeDeEstudo,
    ContinuidadeNaTrilha,
    Nivelado,
    Subida,
    TaxaDeProgressao,
    TempoAteNivelCerto,
    continuidade_na_trilha,
    do_mes,
    nivelados,
    taxa_de_progressao,
    tempo_ate_nivel_certo,
)
from plataforma.modules.nivelamento.application.historico import HistoricoDoNivelamento
from plataforma.modules.turmas.application.consulta_de_presencas import ConsultaDePresencas


@dataclass(frozen=True)
class Metricas:
    """As três métricas do mês em que os nivelamentos foram concluídos (R64)."""

    ano: int
    mes: int
    m1: TaxaDeProgressao
    m2: ContinuidadeNaTrilha
    m3: TempoAteNivelCerto


class VerMetricas:
    """H36: o ADM vê as métricas do mês que escolher."""

    def __init__(
        self,
        historico: HistoricoDoNivelamento,
        presencas: ConsultaDePresencas,
        aulas_concluidas: ConsultaDeAulasConcluidas,
        relogio: Relogio,
    ) -> None:
        self._historico = historico
        self._presencas = presencas
        self._aulas_concluidas = aulas_concluidas
        self._relogio = relogio

    def mes_de_agora(self) -> tuple[int, int]:
        """O ano e o mês de hoje, que a tela mostra ao abrir."""
        agora = self._relogio.agora()
        return agora.year, agora.month

    def executar(self, usuario: Usuario, ano: int, mes: int) -> Metricas:
        exigir_perfil(usuario, Perfil.ADM, "ver as métricas")
        agora = self._relogio.agora()
        concluidos = [
            Nivelado(n.aluno_id, n.materia_id, n.nivel, n.concluido_em)
            for n in self._historico.nivelamentos_concluidos()
        ]
        do_periodo = do_mes(nivelados(concluidos), ano, mes)
        subidas = [
            Subida(p.aluno_id, p.promocao.materia_id, p.promocao.em)
            for p in self._historico.promocoes()
        ]
        atividades = [
            AtividadeDeEstudo(p.aluno_id, p.materia_id, p.nivel, p.data_da_aula)
            for p in self._presencas.presentes()
        ] + [
            AtividadeDeEstudo(a.aluno_id, a.materia_id, a.nivel, a.concluida_em.date())
            for a in self._aulas_concluidas.de_todos()
        ]
        return Metricas(
            ano=ano,
            mes=mes,
            m1=taxa_de_progressao(do_periodo, subidas, agora),
            m2=continuidade_na_trilha(do_periodo, atividades, agora),
            m3=tempo_ate_nivel_certo(do_periodo, atividades),
        )
