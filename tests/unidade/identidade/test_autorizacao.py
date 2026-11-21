"""RNF07: todo caso de uso confere o perfil de quem chama, e não só a tela (H38)."""

import pytest

from plataforma.modules.identidade.domain.autorizacao import (
    AcessoNegado,
    exigir_dono,
    exigir_perfil,
)
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario

ANA = Usuario(id=1, email="ana@exemplo.com", perfil=Perfil.ALUNO)
CARLOS = Usuario(id=2, email="carlos@exemplo.com", perfil=Perfil.PROFESSOR)
ADM = Usuario(id=3, email="adm@exemplo.com", perfil=Perfil.ADM)


def test_rnf07_aluno_chamando_acao_do_adm_e_recusado() -> None:
    with pytest.raises(AcessoNegado, match="Só o ADM pode cadastrar matéria."):
        exigir_perfil(ANA, Perfil.ADM, "cadastrar matéria")


def test_rnf07_professor_chamando_acao_do_adm_e_recusado() -> None:
    with pytest.raises(AcessoNegado, match="Só o ADM pode cadastrar matéria."):
        exigir_perfil(CARLOS, Perfil.ADM, "cadastrar matéria")


def test_rnf07_adm_chamando_acao_do_adm_e_aceito() -> None:
    exigir_perfil(ADM, Perfil.ADM, "cadastrar matéria")


def test_rnf07_adm_chamando_acao_do_aluno_e_recusado() -> None:
    with pytest.raises(AcessoNegado, match="Só o aluno pode fazer o nivelamento."):
        exigir_perfil(ADM, Perfil.ALUNO, "fazer o nivelamento")


def test_rnf07_quem_nao_e_dono_do_recurso_e_recusado() -> None:
    with pytest.raises(AcessoNegado, match="Este nivelamento é de outro aluno."):
        exigir_dono(ANA, dono_id=CARLOS.id, mensagem="Este nivelamento é de outro aluno.")


def test_rnf07_o_dono_do_recurso_e_aceito() -> None:
    exigir_dono(ANA, dono_id=ANA.id, mensagem="Este nivelamento é de outro aluno.")
