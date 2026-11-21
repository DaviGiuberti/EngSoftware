"""Janela principal: abre, aplica as migrações e mostra se o banco respondeu."""

from pathlib import Path

from pytestqt.qtbot import QtBot

from plataforma.main import criar_janela


def test_janela_abre_e_mostra_banco_ok(qtbot: QtBot, tmp_path: Path) -> None:
    janela = criar_janela(tmp_path)
    qtbot.addWidget(janela)

    with qtbot.waitExposed(janela):
        janela.show()

    assert janela.rotulo_banco.text() == "Banco: ok"
    assert (tmp_path / "plataforma.db").exists()
