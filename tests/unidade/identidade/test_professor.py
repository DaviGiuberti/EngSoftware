"""Professor e habilitação por matéria (H29): habilitado numa matéria, o professor dá aula em
todos os níveis dela (R11)."""

import pytest

from plataforma.modules.identidade.domain.professor import (
    HabilitacaoRepetida,
    Professor,
    SemHabilitacao,
    exigir_habilitacao,
    habilitar,
)
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario

FISICA = 1
MATEMATICA = 2


def professor(email: str, *materias: int) -> Professor:
    return Professor(Usuario(10, email, Perfil.PROFESSOR), frozenset(materias))


CARLOS = professor("carlos@exemplo.com", FISICA)
DORA = professor("dora@exemplo.com", FISICA, MATEMATICA)


def test_r11_carlos_habilitado_em_fisica_da_aula_de_fisica() -> None:
    exigir_habilitacao(CARLOS, FISICA, "Física")


def test_r11_professor_sem_habilitacao_na_materia_nao_entra_na_turma() -> None:
    with pytest.raises(
        SemHabilitacao, match="carlos@exemplo.com não tem habilitação em Matemática."
    ):
        exigir_habilitacao(CARLOS, MATEMATICA, "Matemática")


def test_r11_dora_habilitada_em_fisica_e_matematica_da_aula_das_duas() -> None:
    exigir_habilitacao(DORA, FISICA, "Física")
    exigir_habilitacao(DORA, MATEMATICA, "Matemática")


def test_r11_professor_recem_cadastrado_ainda_nao_da_aula_de_nenhuma_materia() -> None:
    eva = professor("eva@exemplo.com")

    with pytest.raises(SemHabilitacao):
        exigir_habilitacao(eva, FISICA, "Física")


def test_r11_habilitar_acrescenta_a_materia_sem_tirar_as_outras() -> None:
    habilitado = habilitar(CARLOS, MATEMATICA, "Matemática")

    assert habilitado.materias_habilitadas == {FISICA, MATEMATICA}
    exigir_habilitacao(habilitado, MATEMATICA, "Matemática")


def test_r11_habilitar_de_novo_na_mesma_materia_e_recusado() -> None:
    with pytest.raises(
        HabilitacaoRepetida, match="carlos@exemplo.com já tem habilitação em Física."
    ):
        habilitar(CARLOS, FISICA, "Física")


def test_usuario_sem_o_perfil_de_professor_nao_vira_professor() -> None:
    ana = Usuario(1, "ana@exemplo.com", Perfil.ALUNO)

    with pytest.raises(ValueError, match="ana@exemplo.com"):
        Professor(ana, frozenset({FISICA}))
