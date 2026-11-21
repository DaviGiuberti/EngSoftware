"""Entrar com e-mail e senha (H38). A recusa não diz se o erro foi no e-mail ou na senha."""

import pytest

from plataforma.modules.identidade.domain.login import Credencial, LoginInvalido, autenticar
from plataforma.modules.identidade.domain.senha import gerar_hash
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario

ANA = Usuario(id=1, email="ana@exemplo.com", perfil=Perfil.ALUNO)
CREDENCIAL_DA_ANA = Credencial(usuario=ANA, hash_da_senha=gerar_hash("abcd1234", bytes(16)))


def test_com_a_senha_certa_entra_com_o_perfil_do_usuario() -> None:
    assert autenticar(CREDENCIAL_DA_ANA, "abcd1234") == ANA


def test_com_a_senha_errada_e_recusado() -> None:
    with pytest.raises(LoginInvalido, match="E-mail ou senha incorretos."):
        autenticar(CREDENCIAL_DA_ANA, "abcd9999")


def test_email_sem_cadastro_e_recusado_com_a_mesma_mensagem() -> None:
    with pytest.raises(LoginInvalido, match="E-mail ou senha incorretos."):
        autenticar(None, "abcd1234")
