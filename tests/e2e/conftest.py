"""Configuração dos testes de ponta a ponta, que abrem as janelas do app com o pytest-qt."""

import os
from contextlib import closing
from datetime import datetime
from functools import partial
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QCheckBox,
    QLineEdit,
    QPlainTextEdit,
    QRadioButton,
)
from pytestqt.qtbot import QtBot

from plataforma.banco import PASTA_MIGRACOES, aplicar_migracoes, conectar, transacao
from plataforma.compartilhado.horario import BRASILIA
from plataforma.janela_principal import JanelaPrincipal
from plataforma.main import criar_janela
from plataforma.modules.identidade.application.casos_de_uso import CriarPrimeiroAdm, Entrar
from plataforma.modules.identidade.infra.repositorio_de_usuarios import (
    RepositorioDeUsuariosSqlite,
)
from plataforma.modules.materias.application.casos_de_uso import (
    CadastrarMateria,
    ConsultaDeMaterias,
)
from plataforma.modules.materias.infra.repositorio_de_materias import (
    RepositorioDeMateriasSqlite,
)
from plataforma.modules.nivelamento.application.casos_de_uso import CadastrarQuestao
from plataforma.modules.nivelamento.infra.repositorio_de_questoes import (
    RepositorioDeQuestoesSqlite,
)

# Sem tela: a janela não aparece durante os testes, e o mesmo teste roda na CI.
# Para ver a janela, rode com a variável QT_QPA_PLATFORM=windows.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

EMAIL_DO_ADM = "adm@exemplo.com"
SENHA_DO_ADM = "admin123"


class RelogioParado:
    """Relógio falso que não anda: o tempo do nivelamento mostrado na tela fica exato."""

    def agora(self) -> datetime:
        return datetime(2026, 11, 23, 14, 0, tzinfo=BRASILIA)


class App:
    """Abre o app numa pasta de dados temporária e age como o usuário: digita e clica."""

    def __init__(self, qtbot: QtBot, pasta_de_dados: Path) -> None:
        self._qtbot = qtbot
        self.pasta_de_dados = pasta_de_dados
        # O qtbot só guarda uma referência fraca da janela. Sem esta lista, uma janela que
        # nenhuma variável do teste segura seria apagada no meio do teste.
        self._janelas: list[JanelaPrincipal] = []

    def abrir(self) -> JanelaPrincipal:
        janela = criar_janela(self.pasta_de_dados, RelogioParado())
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
        """Clica onde o usuário clicaria.

        Num botão de marcar, isso é a bolinha, à esquerda: quando ele ocupa a largura toda da
        tela, o centro cai fora da área que reage ao clique.
        """
        if isinstance(botao, QRadioButton | QCheckBox):
            na_bolinha = QPoint(8, botao.height() // 2)
            self._qtbot.mouseClick(botao, Qt.MouseButton.LeftButton, pos=na_bolinha)
        else:
            self._qtbot.mouseClick(botao, Qt.MouseButton.LeftButton)

    def criar_o_primeiro_adm(self, janela: JanelaPrincipal) -> None:
        tela = janela.tela_primeiro_adm
        self.digitar(tela.email, EMAIL_DO_ADM)
        self.digitar(tela.senha, SENHA_DO_ADM)
        self.clicar(tela.botao_criar)

    def entrar(self, janela: JanelaPrincipal, email: str, senha: str) -> None:
        tela = janela.tela_entrar
        self.digitar(tela.email, email)
        self.digitar(tela.senha, senha)
        self.clicar(tela.botao_entrar)

    def cadastrar_aluno(self, janela: JanelaPrincipal, email: str, senha: str) -> None:
        self.clicar(janela.tela_entrar.botao_cadastro)
        tela = janela.tela_cadastro
        self.digitar(tela.email, email)
        self.digitar(tela.senha, senha)
        self.clicar(tela.botao_cadastrar)

    def preparar_materia(
        self, nome: str, notas_minimas: list[int], quantidade_de_questoes: int
    ) -> None:
        """Cadastra, antes de abrir o app, o ADM e uma matéria com questões de correta na B."""
        caminho_banco = self.pasta_de_dados / "plataforma.db"
        aplicar_migracoes(caminho_banco, PASTA_MIGRACOES, self.pasta_de_dados / "copias")
        with closing(conectar(caminho_banco)) as conexao:
            em_transacao = partial(transacao, conexao)
            usuarios = RepositorioDeUsuariosSqlite(conexao)
            criar_adm = CriarPrimeiroAdm(usuarios, em_transacao)
            if criar_adm.pendente():
                criar_adm.executar(EMAIL_DO_ADM, SENHA_DO_ADM)
            adm = Entrar(usuarios).executar(EMAIL_DO_ADM, SENHA_DO_ADM)
            materias = RepositorioDeMateriasSqlite(conexao)
            materia = CadastrarMateria(materias, em_transacao).executar(
                adm, nome, len(notas_minimas) + 1, notas_minimas, 20000
            )
            cadastrar_questao = CadastrarQuestao(
                RepositorioDeQuestoesSqlite(conexao), ConsultaDeMaterias(materias), em_transacao
            )
            for numero in range(1, quantidade_de_questoes + 1):
                cadastrar_questao.executar(
                    adm, materia.id, f"{nome}: questão {numero}?", ["A", "B", "C", "D", "E"], 1
                )

    def texto_do_log(self) -> str:
        return (self.pasta_de_dados / "logs" / "plataforma.log").read_text(encoding="utf-8")


@pytest.fixture
def app(qtbot: QtBot, tmp_path: Path) -> App:
    return App(qtbot, tmp_path)
