"""O lado do aluno no catálogo (H14, H16): a vitrine com os publicados de todos os níveis, com
destaque para os do nível do aluno (R15, R31), as aulas que ele assiste só com o acesso ativo
(R12, R61) e a aula concluída, que não é desfeita (R62)."""

from datetime import date, datetime

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.catalogo.domain.aulas_do_aluno import (
    AcessoAoPacote,
    AulaConcluida,
    AulaJaConcluida,
    NaVitrine,
    SemAcesso,
    concluir_aula,
    exigir_acesso,
    progresso,
    vitrine,
)
from plataforma.modules.catalogo.domain.pacote import (
    AulaGravada,
    AulaNaoEncontrada,
    EstadoPacote,
    Pacote,
)

FISICA, MATEMATICA = 1, 2
CARLOS = 10
ANA = 2


def pacote(id_do_pacote: int, materia_id: int, nivel: int, estado: EstadoPacote) -> Pacote:
    return Pacote(id_do_pacote, f"Pacote {id_do_pacote}", materia_id, nivel, CARLOS, estado)


RASCUNHO = pacote(1, FISICA, 2, EstadoPacote.RASCUNHO)
EM_REVISAO = pacote(2, FISICA, 2, EstadoPacote.EM_REVISAO)
FISICA_N1 = pacote(3, FISICA, 1, EstadoPacote.PUBLICADO)
FISICA_N2 = pacote(4, FISICA, 2, EstadoPacote.PUBLICADO)
FISICA_N3 = pacote(5, FISICA, 3, EstadoPacote.PUBLICADO)
ARQUIVADO = pacote(6, FISICA, 2, EstadoPacote.ARQUIVADO)
MATEMATICA_N2 = pacote(7, MATEMATICA, 2, EstadoPacote.PUBLICADO)

DEZ_AULAS = Pacote(
    8,
    "Cinemática",
    FISICA,
    1,
    CARLOS,
    EstadoPacote.PUBLICADO,
    tuple(
        AulaGravada(n, f"Aula {n}", f"https://www.youtube.com/watch?v=aula{n:07d}")
        for n in range(1, 11)
    ),
    12000,
)
ATIVO = AcessoAoPacote(ate=date(2028, 3, 10), ativo=True)
VENCIDO = AcessoAoPacote(ate=date(2028, 3, 10), ativo=False)
DOZE_DE_MARCO = datetime(2027, 3, 12, 20, 0, tzinfo=BRASILIA)


def test_r15_so_pacotes_publicados_aparecem() -> None:
    todos = [RASCUNHO, EM_REVISAO, FISICA_N2, ARQUIVADO]

    assert vitrine(todos, niveis={}) == [NaVitrine(FISICA_N2, destaque=False)]


def test_r31_todos_os_niveis_aparecem_com_destaque_para_o_do_aluno() -> None:
    na_vitrine = vitrine([FISICA_N1, FISICA_N2, FISICA_N3], niveis={FISICA: 2})

    assert na_vitrine == [
        NaVitrine(FISICA_N2, destaque=True),
        NaVitrine(FISICA_N1, destaque=False),
        NaVitrine(FISICA_N3, destaque=False),
    ]


def test_r31_o_destaque_e_do_nivel_do_aluno_em_cada_materia() -> None:
    na_vitrine = vitrine([FISICA_N2, MATEMATICA_N2], niveis={MATEMATICA: 2})

    assert na_vitrine == [
        NaVitrine(MATEMATICA_N2, destaque=True),
        NaVitrine(FISICA_N2, destaque=False),
    ]


def test_r31_aluno_sem_nivel_ve_todos_os_pacotes_sem_destaque() -> None:
    na_vitrine = vitrine([FISICA_N1, FISICA_N2, MATEMATICA_N2], niveis={})

    assert [item.destaque for item in na_vitrine] == [False, False, False]
    assert [item.pacote for item in na_vitrine] == [FISICA_N1, FISICA_N2, MATEMATICA_N2]


def test_r12_r61_com_acesso_ativo_o_aluno_assiste() -> None:
    exigir_acesso(ATIVO)


def test_r12_r61_acesso_vencido_bloqueia_as_aulas() -> None:
    with pytest.raises(SemAcesso, match="Seu acesso a este pacote venceu em 10/03/2028."):
        exigir_acesso(VENCIDO)


def test_r12_r61_sem_compra_o_aluno_nao_assiste() -> None:
    with pytest.raises(
        SemAcesso, match="Você não tem acesso a este pacote. Compre o pacote para assistir."
    ):
        exigir_acesso(None)


def test_r12_r62_com_acesso_o_aluno_conclui_a_3a_aula_e_o_pacote_mostra_1_de_10() -> None:
    concluida = concluir_aula(DEZ_AULAS, 3, ATIVO, concluidas=[], agora=DOZE_DE_MARCO)

    assert concluida == AulaConcluida(DEZ_AULAS.id, 3, DOZE_DE_MARCO)
    assert progresso(DEZ_AULAS, [concluida]) == (1, 10)


def test_r62_a_aula_concluida_nao_e_marcada_de_novo() -> None:
    concluida = AulaConcluida(DEZ_AULAS.id, 3, DOZE_DE_MARCO)

    with pytest.raises(AulaJaConcluida, match="Você já concluiu a 3ª aula em 12/03/2027."):
        concluir_aula(DEZ_AULAS, 3, ATIVO, concluidas=[concluida], agora=DOZE_DE_MARCO)


def test_r62_sem_acesso_ativo_a_aula_nao_e_concluida() -> None:
    with pytest.raises(SemAcesso):
        concluir_aula(DEZ_AULAS, 3, VENCIDO, concluidas=[], agora=DOZE_DE_MARCO)


def test_aula_que_o_pacote_nao_tem_nao_e_concluida() -> None:
    with pytest.raises(AulaNaoEncontrada, match="O pacote não tem a 11ª aula."):
        concluir_aula(DEZ_AULAS, 11, ATIVO, concluidas=[], agora=DOZE_DE_MARCO)


def test_o_progresso_conta_so_as_aulas_do_pacote() -> None:
    de_outro_pacote = AulaConcluida(99, 1, DOZE_DE_MARCO)
    concluidas = [AulaConcluida(DEZ_AULAS.id, n, DOZE_DE_MARCO) for n in (1, 2)]

    assert progresso(DEZ_AULAS, [*concluidas, de_outro_pacote]) == (2, 10)
