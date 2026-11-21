"""Verificação do banco: com as migrações do app aplicadas, ele responde ao SELECT 1."""

from pathlib import Path

from plataforma.banco import PASTA_MIGRACOES, aplicar_migracoes, verificar_banco


def test_banco_com_as_migracoes_do_app_responde_ao_select_1(tmp_path: Path) -> None:
    caminho_banco = tmp_path / "plataforma.db"
    aplicar_migracoes(caminho_banco, PASTA_MIGRACOES, tmp_path / "copias")

    assert verificar_banco(caminho_banco)
