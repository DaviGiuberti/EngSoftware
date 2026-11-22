"""Certificados de nível e de trilha (H12): o de nível sai de cada promoção, do nível em que o
aluno foi aprovado (R33). A aprovação no nível máximo dá o certificado de nível desse nível e o
de trilha (R36). Sem promoção nem trilha concluída, como no nivelamento, não há certificado."""

from datetime import datetime

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.nivelamento.domain.certificado import (
    Certificado,
    TipoDeCertificado,
    certificados,
)
from plataforma.modules.nivelamento.domain.promocao import Promocao

FISICA, MATEMATICA = 1, 2
NIVEIS_MAXIMOS = {FISICA: 3, MATEMATICA: 5}
EM_13_03 = datetime(2027, 3, 13, 10, 0, tzinfo=BRASILIA)
EM_20_08 = datetime(2027, 8, 20, 10, 0, tzinfo=BRASILIA)


def test_r33_promovido_do_n1_para_o_n2_recebe_o_certificado_de_nivel_do_n1() -> None:
    promocao = Promocao(FISICA, nivel_anterior=1, nivel_novo=2, em=EM_13_03)

    assert certificados([promocao], {}, NIVEIS_MAXIMOS) == [
        Certificado(TipoDeCertificado.NIVEL, FISICA, 1, EM_13_03)
    ]


def test_r36_aprovado_no_n3_o_nivel_maximo_recebe_o_certificado_do_n3_e_o_de_trilha() -> None:
    assert certificados([], {FISICA: EM_13_03}, NIVEIS_MAXIMOS) == [
        Certificado(TipoDeCertificado.NIVEL, FISICA, 3, EM_13_03),
        Certificado(TipoDeCertificado.TRILHA, FISICA, 3, EM_13_03),
    ]


def test_r33_sem_promocao_nem_trilha_concluida_nao_ha_certificado() -> None:
    # Quem foi reprovado ou só fez o nivelamento não tem promoção guardada.
    assert certificados([], {}, NIVEIS_MAXIMOS) == []


def test_os_certificados_vem_na_ordem_em_que_foram_emitidos() -> None:
    do_n2 = Promocao(FISICA, nivel_anterior=2, nivel_novo=3, em=EM_13_03)
    de_matematica = Promocao(MATEMATICA, nivel_anterior=1, nivel_novo=2, em=EM_13_03)

    emitidos = certificados([de_matematica, do_n2], {FISICA: EM_20_08}, NIVEIS_MAXIMOS)

    assert [(c.materia_id, c.tipo, c.nivel, c.emitido_em) for c in emitidos] == [
        (FISICA, TipoDeCertificado.NIVEL, 2, EM_13_03),
        (MATEMATICA, TipoDeCertificado.NIVEL, 1, EM_13_03),
        (FISICA, TipoDeCertificado.NIVEL, 3, EM_20_08),
        (FISICA, TipoDeCertificado.TRILHA, 3, EM_20_08),
    ]
