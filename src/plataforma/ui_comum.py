"""Peças de tela usadas por mais de um módulo."""

from collections.abc import Sequence

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
)

COR_DA_RECUSA = "#b3261e"
COR_DO_SUCESSO = "#1b5e20"


def titulo(texto: str) -> QLabel:
    rotulo = QLabel(texto)
    rotulo.setStyleSheet("font-size: 18px; font-weight: bold")
    return rotulo


def mostrar_recusa(rotulo: QLabel, texto: str) -> None:
    rotulo.setStyleSheet(f"color: {COR_DA_RECUSA}")
    rotulo.setText(texto)


def mostrar_sucesso(rotulo: QLabel, texto: str) -> None:
    rotulo.setStyleSheet(f"color: {COR_DO_SUCESSO}")
    rotulo.setText(texto)


def mostrar_aviso(rotulo: QLabel, texto: str) -> None:
    rotulo.setStyleSheet("")
    rotulo.setText(texto)


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
