"""Textos das turmas que mais de uma tela mostra."""

from plataforma.modules.materias.domain.materia import nome_do_nivel
from plataforma.modules.turmas.application.casos_de_uso import ResumoDaTurma
from plataforma.modules.turmas.domain.etapa import AULAS_POR_ETAPA
from plataforma.modules.turmas.domain.horario import formatar_data_e_hora


def nome_da_turma(resumo: ResumoDaTurma) -> str:
    """A matéria e o nível da turma: "Física N2"."""
    return f"{resumo.nome_da_materia} {nome_do_nivel(resumo.nivel)}"


def descrever_etapa(resumo: ResumoDaTurma) -> str:
    """Antes da 1ª aula, quando ela é; depois, quantas aulas da etapa já foram dadas (R43). A
    turma que concluiu o nível máximo mostra quando encerrou (R09)."""
    if resumo.encerrada_em is not None:
        return f"encerrada em {resumo.encerrada_em:%d/%m/%Y}"
    if resumo.aulas_dadas == 0:
        return f"1ª aula em {formatar_data_e_hora(resumo.inicio_da_etapa)}"
    return f"{resumo.aulas_dadas} de {AULAS_POR_ETAPA} aulas dadas"
