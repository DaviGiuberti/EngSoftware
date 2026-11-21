"""Log das ações (RNF14) e erro inesperado (RNF10), sem tela."""

import json
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from plataforma.acoes import MENSAGEM_DE_ERRO_INESPERADO, Falhou, Feito, executar
from plataforma.compartilhado.recusa import Recusa
from plataforma.log import configurar_log, fechar_log


@pytest.fixture
def pasta_do_log(tmp_path: Path) -> Iterator[Path]:
    pasta = tmp_path / "logs"
    configurar_log(pasta)
    yield pasta
    fechar_log()


def linhas_do_log(pasta: Path) -> list[dict[str, Any]]:
    texto = (pasta / "plataforma.log").read_text(encoding="utf-8")
    return [json.loads(linha) for linha in texto.splitlines()]


def recusar() -> None:
    raise Recusa("Motivo da recusa.")


def quebrar() -> None:
    raise RuntimeError("falha interna de exemplo")


def test_rnf14_acao_que_deu_certo_vira_uma_linha_json_com_data_usuario_acao_e_resultado(
    pasta_do_log: Path,
) -> None:
    resultado = executar("entrar", "ana@exemplo.com", lambda: 42)

    assert resultado == Feito(42)
    [linha] = linhas_do_log(pasta_do_log)
    assert linha["usuario"] == "ana@exemplo.com"
    assert linha["acao"] == "entrar"
    assert linha["resultado"] == "ok"
    assert datetime.fromisoformat(linha["data"]).utcoffset() is not None


def test_rnf02_recusa_devolve_o_motivo_para_a_tela_e_o_grava_no_log(pasta_do_log: Path) -> None:
    resultado = executar("entrar", "ana@exemplo.com", recusar)

    assert resultado == Falhou("Motivo da recusa.")
    [linha] = linhas_do_log(pasta_do_log)
    assert linha["resultado"] == "recusado"
    assert linha["motivo"] == "Motivo da recusa."


def test_rnf10_erro_inesperado_devolve_mensagem_curta_e_o_detalhe_vai_para_o_log(
    pasta_do_log: Path,
) -> None:
    resultado = executar("entrar", "ana@exemplo.com", quebrar)

    assert resultado == Falhou(MENSAGEM_DE_ERRO_INESPERADO)
    assert "Traceback" not in MENSAGEM_DE_ERRO_INESPERADO
    [linha] = linhas_do_log(pasta_do_log)
    assert linha["resultado"] == "erro"
    assert "RuntimeError: falha interna de exemplo" in linha["detalhe"]


def test_rnf14_acao_sem_usuario_conhecido_grava_usuario_vazio(pasta_do_log: Path) -> None:
    executar("abrir o app", None, lambda: None)

    [linha] = linhas_do_log(pasta_do_log)
    assert linha["usuario"] is None


def test_rnf14_o_log_guarda_no_maximo_5_arquivos(tmp_path: Path) -> None:
    pasta = tmp_path / "logs"
    configurar_log(pasta, tamanho_maximo=200)

    for _ in range(50):
        executar("entrar", "ana@exemplo.com", lambda: None)
    fechar_log()

    assert sorted(arquivo.name for arquivo in pasta.iterdir()) == [
        "plataforma.log",
        "plataforma.log.1",
        "plataforma.log.2",
        "plataforma.log.3",
        "plataforma.log.4",
    ]
