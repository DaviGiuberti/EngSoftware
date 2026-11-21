"""Telas de cadastro e login (H38), com o log das ações (RNF14) e o erro inesperado (RNF10)."""

import json

import pytest

from plataforma.acoes import MENSAGEM_DE_ERRO_INESPERADO
from plataforma.modules.identidade.application.casos_de_uso import Entrar
from tests.e2e.conftest import App


def test_o_app_abre_no_primeiro_adm_e_depois_na_tela_de_entrar(app: App) -> None:
    janela = app.abrir()
    assert janela.telas.currentWidget() is janela.tela_primeiro_adm

    app.criar_o_primeiro_adm(janela)

    assert janela.telas.currentWidget() is janela.tela_inicio
    assert janela.tela_inicio.boas_vindas.text() == "Você entrou como adm@exemplo.com (ADM)."
    janela.close()
    de_novo = app.abrir()
    assert de_novo.telas.currentWidget() is de_novo.tela_entrar


def test_rnf06_senha_curta_e_recusada_na_tela_e_com_8_caracteres_o_aluno_entra(
    app: App,
) -> None:
    janela = app.abrir()
    app.criar_o_primeiro_adm(janela)
    app.clicar(janela.tela_inicio.botao_sair)
    app.clicar(janela.tela_entrar.botao_cadastro)
    tela = janela.tela_cadastro
    app.digitar(tela.email, "ana@exemplo.com")
    app.digitar(tela.senha, "abc1234")

    app.clicar(tela.botao_cadastrar)

    assert janela.telas.currentWidget() is tela
    assert tela.mensagem.text() == "A senha precisa ter pelo menos 8 caracteres."

    app.digitar(tela.senha, "abcd1234")
    app.clicar(tela.botao_cadastrar)

    assert janela.telas.currentWidget() is janela.tela_inicio
    assert janela.tela_inicio.boas_vindas.text() == "Você entrou como ana@exemplo.com (aluno)."


def test_senha_errada_mostra_a_recusa_e_sair_volta_para_a_tela_de_entrar_vazia(
    app: App,
) -> None:
    janela = app.abrir()
    app.criar_o_primeiro_adm(janela)
    app.clicar(janela.tela_inicio.botao_sair)

    app.entrar(janela, "adm@exemplo.com", "senha-errada")

    assert janela.tela_entrar.mensagem.text() == "E-mail ou senha incorretos."

    app.entrar(janela, "adm@exemplo.com", "admin123")
    assert janela.telas.currentWidget() is janela.tela_inicio

    app.clicar(janela.tela_inicio.botao_sair)

    assert janela.telas.currentWidget() is janela.tela_entrar
    assert janela.tela_entrar.senha.text() == ""
    assert janela.tela_entrar.mensagem.text() == ""


def test_rnf14_as_acoes_vao_para_o_log_sem_a_senha(app: App) -> None:
    janela = app.abrir()
    app.criar_o_primeiro_adm(janela)
    app.clicar(janela.tela_inicio.botao_sair)

    app.entrar(janela, "adm@exemplo.com", "admin123")

    log = app.texto_do_log()
    acoes = {(linha["acao"], linha["resultado"]) for linha in map(json.loads, log.splitlines())}
    assert {("criar primeiro ADM", "ok"), ("entrar", "ok")} <= acoes
    assert "admin123" not in log


def test_rnf10_erro_inesperado_ao_entrar_mostra_mensagem_curta_e_vai_para_o_log(
    app: App, monkeypatch: pytest.MonkeyPatch
) -> None:
    def quebrar(self: Entrar, email: str, senha: str) -> None:
        raise RuntimeError("falha forçada no teste")

    janela = app.abrir()
    app.criar_o_primeiro_adm(janela)
    app.clicar(janela.tela_inicio.botao_sair)
    monkeypatch.setattr(Entrar, "executar", quebrar)

    app.entrar(janela, "adm@exemplo.com", "admin123")

    assert janela.telas.currentWidget() is janela.tela_entrar
    assert janela.tela_entrar.mensagem.text() == MENSAGEM_DE_ERRO_INESPERADO
    assert "RuntimeError: falha forçada no teste" in app.texto_do_log()
