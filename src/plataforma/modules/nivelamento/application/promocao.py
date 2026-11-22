"""Função pública da promoção do aluno, que as turmas chamam no fim da etapa (ADR 0002)."""

from dataclasses import replace
from datetime import datetime

from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.nivelamento.application.portas import RepositorioDeNivelamentos
from plataforma.modules.nivelamento.domain.nivelamento import NivelDoAluno
from plataforma.modules.nivelamento.domain.promocao import (
    Promocao,
    conclui_a_trilha,
    promover,
)


class Promocoes:
    """O nível do aluno é do nivelamento, então é ele que promove. As turmas pedem a promoção
    quando o resultado da etapa passa a valer (R49) ou quando a correção do ADM aprova o aluno
    depois disso (R22), sem ler as tabelas do nivelamento."""

    def __init__(
        self, nivelamentos: RepositorioDeNivelamentos, materias: ConsultaDeMaterias
    ) -> None:
        self._nivelamentos = nivelamentos
        self._materias = materias

    def aprovar_na_etapa(
        self, aluno_id: int, materia_id: int, nivel_da_etapa: int, em: datetime
    ) -> None:
        """R08 e R09: o aprovado sobe um nível, sem pular, e no nível máximo conclui a trilha.

        Roda na transação de quem chama. Aprovar de novo na mesma etapa não muda nada.
        """
        materia = self._materias.obter(materia_id)
        atual = self._nivelamentos.nivel_do_aluno(aluno_id, materia.id)
        nivel_atual = nivel_da_etapa if atual is None else atual.nivel
        promocao = promover(materia.id, nivel_atual, nivel_da_etapa, materia.nivel_maximo, em)
        if promocao is not None:
            novo = (
                NivelDoAluno(materia.id, promocao.nivel_novo)
                if atual is None
                else replace(atual, nivel=promocao.nivel_novo)
            )
            self._nivelamentos.salvar_nivel(aluno_id, novo)
            self._nivelamentos.adicionar_promocao(aluno_id, promocao)
        if conclui_a_trilha(nivel_da_etapa, materia.nivel_maximo):
            self._nivelamentos.concluir_trilha(aluno_id, materia.id, em)

    def promocoes(self, aluno_id: int) -> list[Promocao]:
        """As promoções do aluno com a data, da mais antiga à mais nova."""
        return self._nivelamentos.promocoes(aluno_id)
