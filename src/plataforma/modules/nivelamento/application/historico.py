"""Consulta pública do histórico do nivelamento, para as métricas (ADR 0002): os nivelamentos
concluídos e as promoções de todos os alunos, com as datas (R64, R65)."""

from plataforma.modules.nivelamento.application.portas import RepositorioDeNivelamentos
from plataforma.modules.nivelamento.domain.nivelamento import NivelamentoNoHistorico
from plataforma.modules.nivelamento.domain.promocao import PromocaoDoAluno


class HistoricoDoNivelamento:
    """As métricas leem o histórico sem ler as tabelas do nivelamento."""

    def __init__(self, nivelamentos: RepositorioDeNivelamentos) -> None:
        self._nivelamentos = nivelamentos

    def nivelamentos_concluidos(self) -> list[NivelamentoNoHistorico]:
        """Todos os nivelamentos concluídos, também os refeitos (R42), em ordem de data."""
        return self._nivelamentos.concluidos_de_todos()

    def promocoes(self) -> list[PromocaoDoAluno]:
        """Todas as promoções, em ordem de data (R49)."""
        return self._nivelamentos.promocoes_de_todos()
