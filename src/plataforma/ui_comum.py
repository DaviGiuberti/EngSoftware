"""Peças de tela usadas por mais de um módulo."""

from PySide6.QtWidgets import QLabel

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
