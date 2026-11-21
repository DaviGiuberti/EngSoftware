"""Janela principal do app."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow


class JanelaPrincipal(QMainWindow):
    """Janela do esqueleto: por enquanto, só mostra se o banco respondeu."""

    def __init__(self, banco_ok: bool) -> None:
        super().__init__()
        self.setWindowTitle("Plataforma de Ensino")
        self.resize(480, 240)
        self.rotulo_banco = QLabel("Banco: ok" if banco_ok else "Banco: erro")
        self.rotulo_banco.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.rotulo_banco)
