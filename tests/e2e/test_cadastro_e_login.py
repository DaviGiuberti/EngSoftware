"""Telas de cadastro e login (H38), com o log das ações (RNF14) e o erro inesperado (RNF10)."""

import json
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractButton, QLineEdit
from pytestqt.qtbot import QtBot

from plataforma.acoes import MENSAGEM_DE_ERRO_INESPERADO
from plataforma.janela_principal import JanelaPrincipal
from plataforma.main import criar_janela
from plataforma.modules.identidade.application.casos_de_uso import Entrar


def abrir_app(qtbot: QtBot, pasta_de_dados: Path) -> JanelaPrincipal:
    janela = criar_janela(pasta_de_dados)
    qtbot.addWidget(janela)
    with qtbot.waitExposed(janela):
        janela.show()
    return janela


def digitar(qtbot: QtBot, campo: QLineEdit, texto: str) -> None:
    campo.clear()
    qtbot.keyClicks(campo, texto)


def clicar(qtbot: QtBot, botao: QAbstractButton) -> None:
    qtbot.mouseClick(botao, Qt.MouseButton.LeftButton)


def criar_o_primeiro_adm(qtbot: QtBot, janela: JanelaPrincipal) -> None:
    tela = janela.tela_primeiro_adm
    digitar(qtbot, tela.email, "adm@exemplo.com")
    digitar(qtbot, tela.senha, "admin123")
    clicar(qtbot, tela.botao_criar)


def entrar(qtbot: QtBot, janela: JanelaPrincipal, email: str, senha: str) -> None:
    tela = janela.tela_entrar
    digitar(qtbot, tela.email, email)
    digitar(qtbot, tela.senha, senha)
    clicar(qtbot, tela.botao_entrar)


def texto_do_log(pasta_de_dados: Path) -> str:
    return (pasta_de_dados / "logs" / "plataforma.log").read_text(encoding="utf-8")


def test_o_app_abre_no_primeiro_adm_e_depois_na_tela_de_entrar(
    qtbot: QtBot, tmp_path: Path
) -> None:
    janela = abrir_app(qtbot, tmp_path)
    assert janela.telas.currentWidget() is janela.tela_primeiro_adm

    criar_o_primeiro_adm(qtbot, janela)

    assert janela.telas.currentWidget() is janela.tela_inicio
    assert janela.tela_inicio.boas_vindas.text() == "Você entrou como adm@exemplo.com (ADM)."
    janela.close()
    de_novo = abrir_app(qtbot, tmp_path)
    assert de_novo.telas.currentWidget() is de_novo.tela_entrar


def test_rnf06_senha_curta_e_recusada_na_tela_e_com_8_caracteres_o_aluno_entra(
    qtbot: QtBot, tmp_path: Path
) -> None:
    janela = abrir_app(qtbot, tmp_path)
    criar_o_primeiro_adm(qtbot, janela)
    clicar(qtbot, janela.tela_inicio.botao_sair)
    clicar(qtbot, janela.tela_entrar.botao_cadastro)
    tela = janela.tela_cadastro
    digitar(qtbot, tela.email, "ana@exemplo.com")
    digitar(qtbot, tela.senha, "abc1234")

    clicar(qtbot, tela.botao_cadastrar)

    assert janela.telas.currentWidget() is tela
    assert tela.mensagem.text() == "A senha precisa ter pelo menos 8 caracteres."

    digitar(qtbot, tela.senha, "abcd1234")
    clicar(qtbot, tela.botao_cadastrar)

    assert janela.telas.currentWidget() is janela.tela_inicio
    assert janela.tela_inicio.boas_vindas.text() == "Você entrou como ana@exemplo.com (aluno)."


def test_senha_errada_mostra_a_recusa_e_sair_volta_para_a_tela_de_entrar_vazia(
    qtbot: QtBot, tmp_path: Path
) -> None:
    janela = abrir_app(qtbot, tmp_path)
    criar_o_primeiro_adm(qtbot, janela)
    clicar(qtbot, janela.tela_inicio.botao_sair)

    entrar(qtbot, janela, "adm@exemplo.com", "senha-errada")

    assert janela.tela_entrar.mensagem.text() == "E-mail ou senha incorretos."

    entrar(qtbot, janela, "adm@exemplo.com", "admin123")
    assert janela.telas.currentWidget() is janela.tela_inicio

    clicar(qtbot, janela.tela_inicio.botao_sair)

    assert janela.telas.currentWidget() is janela.tela_entrar
    assert janela.tela_entrar.senha.text() == ""
    assert janela.tela_entrar.mensagem.text() == ""


def test_rnf14_as_acoes_vao_para_o_log_sem_a_senha(qtbot: QtBot, tmp_path: Path) -> None:
    janela = abrir_app(qtbot, tmp_path)
    criar_o_primeiro_adm(qtbot, janela)
    clicar(qtbot, janela.tela_inicio.botao_sair)

    entrar(qtbot, janela, "adm@exemplo.com", "admin123")

    log = texto_do_log(tmp_path)
    acoes = {(linha["acao"], linha["resultado"]) for linha in map(json.loads, log.splitlines())}
    assert {("criar primeiro ADM", "ok"), ("entrar", "ok")} <= acoes
    assert "admin123" not in log


def test_rnf10_erro_inesperado_ao_entrar_mostra_mensagem_curta_e_vai_para_o_log(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def quebrar(self: Entrar, email: str, senha: str) -> None:
        raise RuntimeError("falha forçada no teste")

    janela = abrir_app(qtbot, tmp_path)
    criar_o_primeiro_adm(qtbot, janela)
    clicar(qtbot, janela.tela_inicio.botao_sair)
    monkeypatch.setattr(Entrar, "executar", quebrar)

    entrar(qtbot, janela, "adm@exemplo.com", "admin123")

    assert janela.telas.currentWidget() is janela.tela_entrar
    assert janela.tela_entrar.mensagem.text() == MENSAGEM_DE_ERRO_INESPERADO
    assert "RuntimeError: falha forçada no teste" in texto_do_log(tmp_path)
