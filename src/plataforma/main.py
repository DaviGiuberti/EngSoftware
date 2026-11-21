"""Monta o app: banco na pasta de dados, migrações, verificação e janela principal."""

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from plataforma.banco import PASTA_MIGRACOES, aplicar_migracoes, verificar_banco
from plataforma.janela_principal import JanelaPrincipal


def pasta_de_dados_padrao() -> Path:
    """Pasta do banco e das cópias, a mesma para o código e para qualquer .exe (RNF16)."""
    return Path(os.environ["LOCALAPPDATA"]) / "Plataforma"


def criar_janela(pasta_de_dados: Path) -> JanelaPrincipal:
    """Aplica as migrações no banco da pasta de dados, verifica o banco e monta a janela."""
    caminho_banco = pasta_de_dados / "plataforma.db"
    aplicar_migracoes(caminho_banco, PASTA_MIGRACOES, pasta_de_dados / "copias")
    return JanelaPrincipal(banco_ok=verificar_banco(caminho_banco))


def main() -> int:
    """Abre o app e devolve o código de saída quando a janela fecha."""
    app = QApplication(sys.argv)
    janela = criar_janela(pasta_de_dados_padrao())
    janela.show()
    return app.exec()
