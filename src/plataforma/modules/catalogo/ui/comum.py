"""Peças das telas de pacotes que o professor e o ADM usam."""

from collections.abc import Sequence

from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from plataforma.compartilhado.dinheiro import formatar_reais
from plataforma.modules.catalogo.application.casos_de_uso import ResumoDoPacote
from plataforma.modules.catalogo.domain.pacote import NOME_DO_ESTADO, AulaGravada, Pacote


def tabela_de_escolha(colunas: list[str]) -> QTableWidget:
    """Tabela só de leitura, em que se escolhe uma linha inteira por vez."""
    tabela = QTableWidget(0, len(colunas))
    tabela.setHorizontalHeaderLabels(colunas)
    tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    tabela.verticalHeader().setVisible(False)
    cabecalho = tabela.horizontalHeader()
    cabecalho.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    cabecalho.setStretchLastSection(True)
    return tabela


def preencher(tabela: QTableWidget, linhas: Sequence[Sequence[str]]) -> None:
    """Põe as linhas na tabela sem avisar a troca de seleção."""
    tabela.blockSignals(True)
    tabela.clearSelection()
    tabela.setRowCount(len(linhas))
    for linha, valores in enumerate(linhas):
        for coluna, valor in enumerate(valores):
            tabela.setItem(linha, coluna, QTableWidgetItem(valor))
    tabela.blockSignals(False)


def linha_escolhida(tabela: QTableWidget) -> int | None:
    selecionadas = tabela.selectionModel().selectedRows()
    return selecionadas[0].row() if selecionadas else None


def descrever_preco(pacote: Pacote) -> str:
    """O preço só existe depois que o ADM publica o pacote (R59)."""
    if pacote.preco_em_centavos is None:
        return "—"
    return formatar_reais(pacote.preco_em_centavos)


def descrever_estado(pacote: Pacote) -> str:
    return NOME_DO_ESTADO[pacote.estado]


def linhas_das_aulas(aulas: Sequence[AulaGravada]) -> list[list[str]]:
    return [[str(aula.numero), aula.titulo, aula.link] for aula in aulas]


def reescolher(
    tabela: QTableWidget, resumos: Sequence[ResumoDoPacote], pacote_id: int | None
) -> None:
    """Escolhe de novo o pacote que estava escolhido, se ele ainda está na tabela."""
    ids = [resumo.pacote.id for resumo in resumos]
    if pacote_id in ids:
        tabela.selectRow(ids.index(pacote_id))
