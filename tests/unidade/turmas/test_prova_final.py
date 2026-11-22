"""Prova final (H23, H24, H09, H11, H32): a nota vai de 0 a 10, com uma casa decimal (R51), e só
é lançada no fim da etapa, depois da 24ª aula (R17, R20). O professor corrige até 72 horas depois
do lançamento; depois, só o ADM (R22). O resultado da etapa (R08) vale quando o prazo de correção
termina (R49), e uma correção depois disso só muda o nível para cima (R22)."""

from datetime import datetime

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.turmas.domain.matricula import Matricula
from plataforma.modules.turmas.domain.prova_final import (
    AlunoForaDaEtapa,
    EtapaNaoTerminou,
    NotaInvalida,
    NotaJaLancada,
    PrazoDeCorrecaoVencido,
    ProvaFinal,
    ResultadoEtapa,
    SemNota,
    exigir_fim_da_etapa,
    exigir_nota,
    exigir_prazo_de_correcao,
    exigir_sem_nota,
    ler_nota,
    matricula_na_etapa,
    matriculas_da_etapa,
    resultado_a_aplicar,
    resultado_da_etapa,
)

ANA, BRUNO, CARLA = 1, 2, 3
TURMA = 10


def em(dia: int, mes: int, hora: int = 10, minuto: int = 0) -> datetime:
    return datetime(2027, mes, dia, hora, minuto, tzinfo=BRASILIA)


# A 24ª aula da etapa é na terça 09/03/2027, das 19h às 20h30. Os alunos se matricularam em
# 10/12/2026, antes da 1ª aula.
FIM_DA_ETAPA = em(9, 3, 20, 30)
LANCADA_EM_10_03_AS_10H = em(10, 3)
MATRICULA_EM_10_12_2026 = datetime(2026, 12, 10, 14, 0, tzinfo=BRASILIA)


def test_r08_6_faltas_e_nota_7_aprovam() -> None:
    assert resultado_da_etapa(6, ler_nota("7")) == ResultadoEtapa.APROVADO


def test_r08_2_faltas_e_nota_6_5_reprovam() -> None:
    assert resultado_da_etapa(2, ler_nota("6,5")) == ResultadoEtapa.REPROVADO


def test_r08_7_faltas_reprovam_mesmo_com_nota_9() -> None:
    assert resultado_da_etapa(7, ler_nota("9")) == ResultadoEtapa.REPROVADO


def test_r23_sem_nota_o_resultado_fica_pendente() -> None:
    assert resultado_da_etapa(0, None) == ResultadoEtapa.PENDENTE


def test_r51_a_nota_vai_de_0_a_10_com_uma_casa_decimal() -> None:
    lidas = [str(ler_nota(texto)) for texto in ("0", "6,5", "6.5", "7", "7,0", " 8 ", "10")]

    assert lidas == ["0", "6,5", "6,5", "7", "7", "8", "10"]


@pytest.mark.parametrize("texto", ["6,75", "-1", "10,5", "11", "100", "", "seis", "6,"])
def test_r51_nota_com_duas_casas_ou_fora_de_0_a_10_e_recusada(texto: str) -> None:
    with pytest.raises(NotaInvalida, match="A nota vai de 0 a 10, com uma casa decimal, como 6,5."):
        ler_nota(texto)


def test_r08_a_nota_7_e_a_menor_que_aprova() -> None:
    assert ler_nota("6,9") < ler_nota("7") <= ler_nota("10")


def test_r20_depois_do_fim_da_24a_aula_a_nota_e_lancada() -> None:
    exigir_fim_da_etapa(FIM_DA_ETAPA, FIM_DA_ETAPA)
    exigir_fim_da_etapa(FIM_DA_ETAPA, LANCADA_EM_10_03_AS_10H)


def test_r17_antes_do_fim_da_etapa_a_nota_e_recusada() -> None:
    with pytest.raises(
        EtapaNaoTerminou,
        match="A nota da prova final só é lançada no fim da etapa, depois da 24ª aula: em "
        "09/03/2027, às 20h30.",
    ):
        exigir_fim_da_etapa(FIM_DA_ETAPA, em(9, 3, 20, 29))


def test_r22_carlos_corrige_a_nota_em_13_03_as_9h59() -> None:
    exigir_prazo_de_correcao(LANCADA_EM_10_03_AS_10H, em(13, 3, 9, 59), pelo_adm=False)


def test_r22_em_13_03_as_10h01_so_o_adm_corrige() -> None:
    with pytest.raises(
        PrazoDeCorrecaoVencido,
        match="O prazo de correção terminou em 13/03/2027, às 10h, 72 horas depois do "
        "lançamento: agora só o ADM pode corrigir.",
    ):
        exigir_prazo_de_correcao(LANCADA_EM_10_03_AS_10H, em(13, 3, 10, 1), pelo_adm=False)


def test_r22_nas_72_horas_em_ponto_o_prazo_ja_terminou() -> None:
    with pytest.raises(PrazoDeCorrecaoVencido):
        exigir_prazo_de_correcao(LANCADA_EM_10_03_AS_10H, em(13, 3, 10, 0), pelo_adm=False)


def test_r22_o_prazo_vale_tambem_para_a_presenca_lancada_em_01_03_as_20h30() -> None:
    with pytest.raises(PrazoDeCorrecaoVencido, match="terminou em 04/03/2027, às 20h30"):
        exigir_prazo_de_correcao(em(1, 3, 20, 30), em(5, 3), pelo_adm=False)


def test_r22_o_adm_corrige_depois_das_72_horas() -> None:
    exigir_prazo_de_correcao(LANCADA_EM_10_03_AS_10H, em(20, 3), pelo_adm=True)


def test_r49_o_resultado_da_nota_lancada_em_10_03_as_10h_vale_em_13_03_as_10h() -> None:
    prova = ProvaFinal(ANA, ler_nota("8"), LANCADA_EM_10_03_AS_10H)

    assert prova.vale_em == em(13, 3)


def test_r22_depois_que_o_resultado_valeu_a_correcao_que_aprova_promove() -> None:
    aplicar = resultado_a_aplicar(ResultadoEtapa.REPROVADO, ResultadoEtapa.APROVADO)

    assert aplicar == ResultadoEtapa.APROVADO


def test_r22_a_correcao_que_reprova_quem_ja_subiu_nao_muda_o_nivel() -> None:
    assert resultado_a_aplicar(ResultadoEtapa.APROVADO, ResultadoEtapa.REPROVADO) is None


def test_r49_antes_de_o_resultado_valer_a_correcao_nao_aplica_nada() -> None:
    assert resultado_a_aplicar(None, ResultadoEtapa.APROVADO) is None
    assert resultado_a_aplicar(ResultadoEtapa.REPROVADO, ResultadoEtapa.REPROVADO) is None


def test_a_nota_de_um_aluno_e_lancada_uma_vez() -> None:
    lancada = ProvaFinal(ANA, ler_nota("8"), LANCADA_EM_10_03_AS_10H)

    with pytest.raises(
        NotaJaLancada, match="A nota de ana@exemplo.com já foi lançada. Para mudar, corrija a nota."
    ):
        exigir_sem_nota(lancada, "ana@exemplo.com")
    exigir_sem_nota(None, "ana@exemplo.com")


def test_r22_so_a_nota_ja_lancada_e_corrigida() -> None:
    lancada = ProvaFinal(ANA, ler_nota("8"), LANCADA_EM_10_03_AS_10H)

    with pytest.raises(SemNota, match="A nota de ana@exemplo.com ainda não foi lançada."):
        exigir_nota(None, "ana@exemplo.com")
    assert exigir_nota(lancada, "ana@exemplo.com") == lancada


def test_r23_a_prova_final_e_de_quem_estava_na_turma_no_fim_da_etapa() -> None:
    ana = Matricula(1, TURMA, ANA, MATRICULA_EM_10_12_2026)
    # Bruno saiu da turma antes do fim da etapa, por vontade própria.
    bruno = Matricula(2, TURMA, BRUNO, MATRICULA_EM_10_12_2026, saiu_em=em(1, 3))
    # Carla entrou depois do fim da etapa, para a etapa seguinte.
    carla = Matricula(3, TURMA, CARLA, em(10, 3, 14))

    assert matriculas_da_etapa([ana, bruno, carla], FIM_DA_ETAPA) == [ana]


def test_r21_quem_saiu_por_reprovacao_depois_do_fim_continua_na_prova_final() -> None:
    # O reprovado sai quando o resultado vale (R49). O ADM ainda corrige a nota dele (H32).
    saiu_reprovada = Matricula(1, TURMA, ANA, MATRICULA_EM_10_12_2026, saiu_em=em(13, 3))

    assert matricula_na_etapa([saiu_reprovada], ANA, FIM_DA_ETAPA) == saiu_reprovada


def test_aluno_que_nao_estava_na_turma_no_fim_da_etapa_nao_recebe_nota() -> None:
    entrou_depois = Matricula(1, TURMA, CARLA, em(10, 3, 14))

    with pytest.raises(
        AlunoForaDaEtapa, match="Este aluno não estava na turma no fim da etapa."
    ):
        matricula_na_etapa([entrou_depois], CARLA, FIM_DA_ETAPA)
