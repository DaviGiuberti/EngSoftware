"""Cadastro (H38): R39, uma conta por e-mail sem diferenciar maiúsculas, e o primeiro ADM."""

import pytest

from plataforma.modules.identidade.domain.cadastro import (
    EmailInvalido,
    EmailJaCadastrado,
    PrimeiroAdmJaCriado,
    exigir_email_livre,
    exigir_que_nao_haja_adm,
    normalizar_email,
    validar_email,
)


def test_r39_email_e_guardado_sem_espacos_nas_pontas_e_em_minusculas() -> None:
    assert normalizar_email("  Ana@Exemplo.com ") == "ana@exemplo.com"


def test_r39_email_com_maiusculas_e_o_mesmo_email() -> None:
    assert normalizar_email("Ana@Exemplo.com") == normalizar_email("ana@exemplo.com")


def test_r39_email_ja_cadastrado_e_recusado() -> None:
    with pytest.raises(EmailJaCadastrado, match="Este e-mail já está cadastrado."):
        exigir_email_livre(email_ja_cadastrado=True)


def test_r39_email_livre_e_aceito() -> None:
    exigir_email_livre(email_ja_cadastrado=False)


@pytest.mark.parametrize(
    "email",
    ["", "anaexemplo.com", "ana@", "@exemplo.com", "ana@@exemplo.com", "ana silva@exemplo.com"],
)
def test_email_fora_do_formato_nome_arroba_dominio_e_recusado(email: str) -> None:
    with pytest.raises(EmailInvalido, match="Informe um e-mail válido"):
        validar_email(email)


def test_email_no_formato_nome_arroba_dominio_e_aceito() -> None:
    validar_email("ana@exemplo.com")


def test_primeiro_adm_e_recusado_quando_ja_existe_um_adm() -> None:
    with pytest.raises(PrimeiroAdmJaCriado, match="O primeiro ADM já foi criado."):
        exigir_que_nao_haja_adm(ja_existe_adm=True)


def test_primeiro_adm_e_aceito_quando_nao_existe_nenhum_adm() -> None:
    exigir_que_nao_haja_adm(ja_existe_adm=False)
