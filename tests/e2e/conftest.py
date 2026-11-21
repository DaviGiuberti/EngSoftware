"""Configuração dos testes de ponta a ponta, que abrem as janelas do app com o pytest-qt."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractButton, QLineEdit, QPlainTextEdit
from pytestqt.qtbot import QtBot

from plataforma.janela_principal import JanelaPrincipal
from plataforma.main import criar_janela

# Sem tela: a janela não aparece durante os testes, e o mesmo teste roda na CI.
# Para ver a janela, rode com a variável QT_QPA_PLATFORM=windows.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class App:
    """Abre o app numa pasta de dados temporária e age como o usuário: digita e clica."""

    def __init__(self, qtbot: QtBot, pasta_de_dados: Path) -> None:
        self._qtbot = qtbot
        self.pasta_de_dados = pasta_de_dados
        # O qtbot só guarda uma referência fraca da janela. Sem esta lista, uma janela que
        # nenhuma variável do teste segura seria apagada no meio do teste.
        self._janelas: list[JanelaPrincipal] = []

    def abrir(self) -> JanelaPrincipal:
        janela = criar_janela(self.pasta_de_dados)
        self._janelas.append(janela)
        self._qtbot.addWidget(janela)
        with self._qtbot.waitExposed(janela):
            janela.show()
        return janela

    def digitar(self, campo: QLineEdit | QPlainTextEdit, texto: str) -> None:
        """Escreve no campo como se o texto fosse colado.

        O qtbot.keyClicks derruba o processo, sem traceback, com letras acentuadas como o
        "í" de "Física" (QTest do Qt 6.12 no Windows), e o app é todo em português.
        """
        campo.setFocus()
        campo.clear()
        if isinstance(campo, QLineEdit):
            campo.insert(texto)
        else:
            campo.insertPlainText(texto)

    def clicar(self, botao: QAbstractButton) -> None:
        self._qtbot.mouseClick(botao, Qt.MouseButton.LeftButton)

    def criar_o_primeiro_adm(self, janela: JanelaPrincipal) -> None:
        tela = janela.tela_primeiro_adm
        self.digitar(tela.email, "adm@exemplo.com")
        self.digitar(tela.senha, "admin123")
        self.clicar(tela.botao_criar)

    def entrar(self, janela: JanelaPrincipal, email: str, senha: str) -> None:
        tela = janela.tela_entrar
        self.digitar(tela.email, email)
        self.digitar(tela.senha, senha)
        self.clicar(tela.botao_entrar)

    def texto_do_log(self) -> str:
        return (self.pasta_de_dados / "logs" / "plataforma.log").read_text(encoding="utf-8")


@pytest.fixture
def app(qtbot: QtBot, tmp_path: Path) -> App:
    return App(qtbot, tmp_path)
