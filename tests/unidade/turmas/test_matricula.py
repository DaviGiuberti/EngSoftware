"""Matrícula (H04, H05, H06, H07): só na turma do nível do aluno (R06), sem conflito de horário
(R07), até antes da 13ª aula da etapa (R19), uma turma por matéria (R44) e com vaga livre (R04,
R05). Quem perde a vaga por atraso da mensalidade vê um aviso até entrar em outra turma da
matéria (R55)."""

from datetime import datetime, time

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.turmas.domain.horario import DiaDaSemana, novo_horario
from plataforma.modules.turmas.domain.matricula import (
    JaTemTurmaNaMateria,
    Matricula,
    MatriculaFechada,
    MotivoDaSaida,
    NivelDiferenteDaTurma,
    SemNivelNaMateria,
    SituacaoNaTurma,
    TurmaCheia,
    aula_de_entrada,
    exigir_aluno_livre,
    exigir_matricula_aberta,
    exigir_nivel_da_turma,
    exigir_sem_turma_na_materia,
    exigir_vaga,
    situacao_na_turma,
    vagas_livres,
    vagas_perdidas,
)
from plataforma.modules.turmas.domain.turma import ConflitoDeHorario

TER, QUI = DiaDaSemana.TERCA, DiaDaSemana.QUINTA
MATEMATICA_TER_19H = novo_horario([TER], time(19), time(20, 30))
FISICA_TER_E_QUI_20H = novo_horario([TER, QUI], time(20), time(21, 30))


def test_r06_aluno_no_n2_entra_na_turma_do_n2() -> None:
    exigir_nivel_da_turma(nivel_do_aluno=2, nivel_da_turma=2, nome_da_materia="Física")


def test_r06_aluno_no_n2_nao_entra_na_turma_do_n3() -> None:
    with pytest.raises(
        NivelDiferenteDaTurma, match="Esta turma é do N3 de Física, e você está no N2."
    ):
        exigir_nivel_da_turma(nivel_do_aluno=2, nivel_da_turma=3, nome_da_materia="Física")


def test_r06_aluno_sem_nivel_na_materia_precisa_fazer_o_nivelamento() -> None:
    with pytest.raises(
        SemNivelNaMateria, match="Faça o nivelamento de Física antes de entrar numa turma dela."
    ):
        exigir_nivel_da_turma(nivel_do_aluno=None, nivel_da_turma=2, nome_da_materia="Física")


def test_r44_aluno_com_turma_de_fisica_nao_entra_em_outra_de_fisica() -> None:
    with pytest.raises(JaTemTurmaNaMateria, match="Você já está numa turma de Física."):
        exigir_sem_turma_na_materia(tem_turma_na_materia=True, nome_da_materia="Física")


def test_r44_aluno_sem_turma_na_materia_pode_entrar() -> None:
    exigir_sem_turma_na_materia(tem_turma_na_materia=False, nome_da_materia="Física")


def test_r07_aluno_em_matematica_as_tercas_19h_nao_entra_em_fisica_as_tercas_20h() -> None:
    with pytest.raises(
        ConflitoDeHorario,
        match="Conflito de horário: você já tem uma turma às terças, das 19h às 20h30.",
    ):
        exigir_aluno_livre(FISICA_TER_E_QUI_20H, [MATEMATICA_TER_19H])


def test_r07_aluno_sem_turma_que_se_sobreponha_esta_livre() -> None:
    exigir_aluno_livre(FISICA_TER_E_QUI_20H, [])


def test_r19_com_12_aulas_dadas_a_matricula_e_aceita_e_o_aluno_entra_na_13a() -> None:
    exigir_matricula_aberta(aulas_dadas=12)

    assert aula_de_entrada(aulas_dadas=12) == 13


def test_r19_com_13_aulas_dadas_a_matricula_e_recusada() -> None:
    with pytest.raises(
        MatriculaFechada,
        match="A matrícula nesta turma fechou: só dá para entrar até antes da 13ª aula da etapa.",
    ):
        exigir_matricula_aberta(aulas_dadas=13)


def test_r08_antes_da_1a_aula_o_aluno_entra_na_1a() -> None:
    assert aula_de_entrada(aulas_dadas=0) == 1


def test_r04_turma_com_12_alunos_recusa_e_oferece_a_lista_de_espera() -> None:
    with pytest.raises(TurmaCheia, match="Turma cheia: você pode entrar na lista de espera."):
        exigir_vaga(matriculados=12, reservadas=0)


def test_r05_a_vaga_reservada_para_a_lista_de_espera_nao_e_de_quem_chega() -> None:
    with pytest.raises(
        TurmaCheia,
        match="A vaga desta turma está reservada para a lista de espera. "
        "Você pode entrar na lista.",
    ):
        exigir_vaga(matriculados=11, reservadas=1)


def test_r04_turma_com_11_alunos_tem_1_vaga_livre() -> None:
    exigir_vaga(matriculados=11, reservadas=0)

    assert vagas_livres(matriculados=11, reservadas=0) == 1


@pytest.mark.parametrize(
    ("matriculado", "na_lista", "com_oferta", "livres", "situacao"),
    [
        (True, False, False, 0, SituacaoNaTurma.MATRICULADO),
        (False, True, True, 0, SituacaoNaTurma.VAGA_OFERECIDA),
        (False, True, False, 0, SituacaoNaTurma.NA_LISTA),
        (False, False, False, 3, SituacaoNaTurma.COM_VAGA),
        (False, False, False, 0, SituacaoNaTurma.CHEIA),
    ],
)
def test_a_situacao_do_aluno_na_turma_decide_o_que_ele_pode_fazer(
    matriculado: bool, na_lista: bool, com_oferta: bool, livres: int, situacao: SituacaoNaTurma
) -> None:
    assert situacao_na_turma(matriculado, na_lista, com_oferta, livres) == situacao


ANA, FISICA, MATEMATICA = 1, 10, 20
TURMA_DE_FISICA, OUTRA_DE_FISICA, TURMA_DE_MATEMATICA = 100, 101, 200
MATERIA_DA_TURMA = {
    TURMA_DE_FISICA: FISICA,
    OUTRA_DE_FISICA: FISICA,
    TURMA_DE_MATEMATICA: MATEMATICA,
}
MATRICULOU_EM_10_03 = datetime(2027, 3, 10, 10, 0, tzinfo=BRASILIA)
PERDEU_A_VAGA_EM_18_04 = datetime(2027, 4, 18, 0, 0, tzinfo=BRASILIA)
PERDIDA = Matricula(
    1, TURMA_DE_FISICA, ANA, MATRICULOU_EM_10_03, PERDEU_A_VAGA_EM_18_04, MotivoDaSaida.ATRASO
)


def test_r55_quem_perdeu_a_vaga_por_atraso_ve_o_aviso() -> None:
    assert vagas_perdidas([PERDIDA], MATERIA_DA_TURMA) == [PERDIDA]


def test_r55_o_aviso_some_quando_o_aluno_entra_em_outra_turma_da_materia() -> None:
    outra = Matricula(
        2, OUTRA_DE_FISICA, ANA, datetime(2027, 4, 20, 10, 0, tzinfo=BRASILIA)
    )

    assert vagas_perdidas([PERDIDA, outra], MATERIA_DA_TURMA) == []


def test_r55_turma_de_outra_materia_nao_tira_o_aviso() -> None:
    matematica = Matricula(
        2, TURMA_DE_MATEMATICA, ANA, datetime(2027, 4, 20, 10, 0, tzinfo=BRASILIA)
    )

    assert vagas_perdidas([PERDIDA, matematica], MATERIA_DA_TURMA) == [PERDIDA]


def test_r55_quem_saiu_por_outro_motivo_nao_ve_o_aviso() -> None:
    saiu = Matricula(
        1, TURMA_DE_FISICA, ANA, MATRICULOU_EM_10_03, PERDEU_A_VAGA_EM_18_04, MotivoDaSaida.VONTADE
    )

    assert vagas_perdidas([saiu], MATERIA_DA_TURMA) == []
