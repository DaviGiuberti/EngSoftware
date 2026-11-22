"""Métricas M1, M2 e M3 (H36): cada aluno numa matéria conta pelo primeiro nivelamento dele, no mês
em que o concluiu (R64). M1 é a taxa de promovidos em até 6 meses (R65), M2 a de quem estudou na
4ª semana (R66) e M3 a mediana dos dias até estudar no nível recebido (R67)."""

from datetime import date, datetime

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.metricas.domain.metricas import (
    AtividadeDeEstudo,
    ContinuidadeNaTrilha,
    Nivelado,
    Subida,
    TaxaDeProgressao,
    TempoAteNivelCerto,
    continuidade_na_trilha,
    do_mes,
    fim_do_prazo_da_progressao,
    nivelados,
    taxa_de_progressao,
    tempo_ate_nivel_certo,
)

FISICA, MATEMATICA = 1, 2


def em(dia: int, mes: int, ano: int = 2027, hora: int = 10) -> datetime:
    return datetime(ano, mes, dia, hora, 0, tzinfo=BRASILIA)


def nivelado(aluno_id: int, dia: int = 10, mes: int = 3, nivel: int = 2) -> Nivelado:
    return Nivelado(aluno_id, FISICA, nivel, em(dia, mes))


def atividade(
    aluno_id: int, quando: date, nivel: int = 2, materia: int = FISICA
) -> AtividadeDeEstudo:
    return AtividadeDeEstudo(aluno_id, materia, nivel, quando)


DEZ_DE_MARCO = [nivelado(aluno) for aluno in range(1, 11)]


# R64: quem conta e em que mês


def test_r64_conta_o_primeiro_nivelamento_de_cada_aluno_em_cada_materia() -> None:
    primeiro = Nivelado(1, FISICA, 1, em(10, 3))
    refeito = Nivelado(1, FISICA, 2, em(20, 4))
    de_matematica = Nivelado(1, MATEMATICA, 3, em(5, 4))

    assert nivelados([refeito, de_matematica, primeiro]) == [primeiro, de_matematica]


def test_r64_o_periodo_e_o_mes_em_que_o_nivelamento_foi_concluido() -> None:
    de_marco = [nivelado(1, 1, 3), nivelado(2, 31, 3)]
    fora = [nivelado(3, 28, 2), nivelado(4, 1, 4), Nivelado(5, FISICA, 2, em(15, 3, 2026))]

    assert do_mes([*de_marco, *fora], 2027, 3) == de_marco


# R65: M1, taxa de progressão


def test_m1_r65_3_de_10_promovidos_em_ate_6_meses_e_30_por_cento() -> None:
    subidas = [Subida(aluno, FISICA, em(1, 8)) for aluno in (1, 2, 3)]

    m1 = taxa_de_progressao(DEZ_DE_MARCO, subidas, agora=em(1, 12))

    assert m1 == TaxaDeProgressao(promovidos=3, nivelados=10, ainda_no_prazo=0)
    assert m1.porcentagem == 30


def test_r65_o_prazo_vai_ate_o_mesmo_dia_6_meses_depois() -> None:
    assert fim_do_prazo_da_progressao(nivelado(1, 10, 3)) == date(2027, 9, 10)
    assert fim_do_prazo_da_progressao(nivelado(1, 31, 3)) == date(2027, 9, 30)


def test_r65_promocao_depois_dos_6_meses_ou_em_outra_materia_nao_conta() -> None:
    subidas = [
        Subida(1, FISICA, em(10, 9, hora=23)),
        Subida(2, FISICA, em(11, 9)),
        Subida(3, MATEMATICA, em(1, 5)),
    ]

    m1 = taxa_de_progressao(DEZ_DE_MARCO[:3], subidas, agora=em(1, 12))

    assert (m1.promovidos, m1.nivelados) == (1, 3)


def test_r65_promovido_duas_vezes_conta_uma_so() -> None:
    subidas = [Subida(1, FISICA, em(1, 6)), Subida(1, FISICA, em(1, 8))]

    assert taxa_de_progressao(DEZ_DE_MARCO[:1], subidas, agora=em(1, 12)).promovidos == 1


def test_r65_entram_todos_e_a_tela_diz_quantos_ainda_estao_no_prazo() -> None:
    subidas = [Subida(1, FISICA, em(1, 5))]

    m1 = taxa_de_progressao(DEZ_DE_MARCO[:4], subidas, agora=em(10, 9, hora=23))

    assert m1 == TaxaDeProgressao(promovidos=1, nivelados=4, ainda_no_prazo=3)
    assert taxa_de_progressao(DEZ_DE_MARCO[:4], subidas, em(11, 9)).ainda_no_prazo == 0


def test_r65_sem_nivelados_no_mes_a_m1_fica_sem_valor() -> None:
    assert taxa_de_progressao([], [], agora=em(1, 12)).porcentagem is None


# R66: M2, continuidade na trilha


def test_m2_r66_5_de_10_com_atividade_na_4a_semana_e_50_por_cento() -> None:
    na_4a_semana = [atividade(aluno, date(2027, 3, 31)) for aluno in (1, 2, 3, 4, 5)]

    m2 = continuidade_na_trilha(DEZ_DE_MARCO, na_4a_semana, agora=em(7, 4))

    assert m2 == ContinuidadeNaTrilha(com_atividade=5, elegiveis=10)
    assert m2.porcentagem == 50


def test_r66_a_4a_semana_vai_do_21o_ao_27o_dia() -> None:
    # Nivelamento em 10/03: o dia 21 é 31/03, e o dia 27 é 06/04.
    atividades = [
        atividade(1, date(2027, 3, 30)),
        atividade(2, date(2027, 3, 31)),
        atividade(3, date(2027, 4, 6)),
        atividade(4, date(2027, 4, 7)),
    ]

    m2 = continuidade_na_trilha(DEZ_DE_MARCO[:4], atividades, agora=em(1, 5))

    assert m2 == ContinuidadeNaTrilha(com_atividade=2, elegiveis=4)


def test_r66_so_entra_quem_se_nivelou_ha_pelo_menos_28_dias() -> None:
    nivelados_do_mes = [nivelado(1, 10, 3), nivelado(2, 11, 3)]

    m2 = continuidade_na_trilha(nivelados_do_mes, [], agora=em(7, 4, hora=0))

    assert m2.elegiveis == 1


def test_r64_r66_a_atividade_e_na_materia_do_nivelamento_em_qualquer_nivel() -> None:
    atividades = [
        atividade(1, date(2027, 4, 1), nivel=3),
        atividade(2, date(2027, 4, 1), materia=MATEMATICA),
    ]

    m2 = continuidade_na_trilha(DEZ_DE_MARCO[:2], atividades, agora=em(1, 5))

    assert m2.com_atividade == 1


def test_r66_sem_elegiveis_a_m2_fica_sem_valor() -> None:
    assert continuidade_na_trilha(DEZ_DE_MARCO, [], agora=em(15, 3)).porcentagem is None


# R67: M3, tempo até estudar no nível certo


def test_m3_r67_atividades_em_1_2_e_6_dias_dao_mediana_de_2_dias() -> None:
    atividades = [
        atividade(1, date(2027, 3, 11)),
        atividade(2, date(2027, 3, 12)),
        atividade(3, date(2027, 3, 16)),
    ]

    m3 = tempo_ate_nivel_certo(DEZ_DE_MARCO[:3], atividades)

    assert m3 == TempoAteNivelCerto(dias=(1, 2, 6))
    assert m3.mediana == 2


def test_r67_com_numero_par_a_mediana_e_a_media_dos_dois_do_meio() -> None:
    atividades = [
        atividade(1, date(2027, 3, 11)),
        atividade(2, date(2027, 3, 12)),
        atividade(3, date(2027, 3, 13)),
        atividade(4, date(2027, 3, 16)),
    ]

    assert tempo_ate_nivel_certo(DEZ_DE_MARCO[:4], atividades).mediana == 2.5


def test_m3_r67_atividade_em_outro_nivel_nao_conta() -> None:
    so_no_n1 = [atividade(1, date(2027, 3, 11), nivel=1)]

    m3 = tempo_ate_nivel_certo(DEZ_DE_MARCO[:1], so_no_n1)

    assert m3.dias == ()
    assert m3.mediana is None


def test_r67_conta_a_primeira_atividade_no_nivel_desde_o_dia_do_nivelamento() -> None:
    atividades = [
        atividade(1, date(2027, 3, 9)),
        atividade(1, date(2027, 3, 20)),
        atividade(1, date(2027, 3, 14)),
        atividade(2, date(2027, 3, 10)),
    ]

    assert tempo_ate_nivel_certo(DEZ_DE_MARCO[:2], atividades).dias == (0, 4)


def test_r67_a_mediana_tem_uma_casa_decimal() -> None:
    atividades = [atividade(1, date(2027, 3, 11)), atividade(2, date(2027, 3, 12))]

    assert tempo_ate_nivel_certo(DEZ_DE_MARCO[:2], atividades).mediana == 1.5
