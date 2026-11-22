"""Lista de espera (H05, H06, H13): ordem de entrada e só para turma cheia (R05), oferta da vaga
ao 1º da lista com 72 horas para confirmar (R05), saída de quem não confirma (R35), nada de
oferta a partir da 13ª aula (R45) e saída das outras listas da matéria (R44)."""

from datetime import datetime, time, timedelta

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.turmas.domain.horario import DiaDaSemana, novo_horario
from plataforma.modules.turmas.domain.lista_de_espera import (
    JaEstaNaLista,
    ListaDeEspera,
    ListaFechada,
    NaLista,
    PrazoVencido,
    SemOferta,
    TurmaComVaga,
    confirmar,
    entrar,
    exigir_lista_aberta,
    exigir_turma_cheia,
    oferecer_vaga,
    pode_oferecer_em,
    posicao,
    reservadas,
    sair,
    vencer_prazos,
)
from plataforma.modules.turmas.domain.turma import Turma

ANA, BRUNO, CARLA = 1, 2, 3
SAIU_EM_10_03_14H = datetime(2027, 3, 10, 14, 0, tzinfo=BRASILIA)
ATE_13_03_14H = datetime(2027, 3, 13, 14, 0, tzinfo=BRASILIA)
ATE_16_03_14H = datetime(2027, 3, 16, 14, 0, tzinfo=BRASILIA)
UM_MINUTO = timedelta(minutes=1)


def sempre(_momento: datetime) -> bool:
    return True


def nunca(_momento: datetime) -> bool:
    return False


def lista_com(*alunos: int) -> ListaDeEspera:
    """Os alunos entram na lista um dia depois do outro, na ordem dada."""
    lista: ListaDeEspera = ()
    for dias, aluno in enumerate(alunos):
        lista = entrar(lista, aluno, datetime(2027, 3, 1 + dias, 9, 0, tzinfo=BRASILIA))
    return lista


def ana_com_a_vaga_ate_13_03_14h() -> ListaDeEspera:
    return oferecer_vaga(lista_com(ANA, BRUNO), SAIU_EM_10_03_14H, pode_oferecer=True)


def prazos(lista: ListaDeEspera) -> dict[int, datetime | None]:
    return {na_lista.aluno_id: na_lista.prazo for na_lista in lista}


def test_r05_a_lista_segue_a_ordem_de_entrada() -> None:
    lista = lista_com(ANA, BRUNO)

    assert posicao(lista, ANA) == 1
    assert posicao(lista, BRUNO) == 2


def test_quem_ja_esta_na_lista_nao_entra_de_novo() -> None:
    with pytest.raises(JaEstaNaLista, match="Você já está na lista de espera desta turma."):
        entrar(lista_com(ANA), ANA, SAIU_EM_10_03_14H)


def test_r05_turma_com_vaga_nao_tem_lista_de_espera_e_oferece_a_matricula() -> None:
    with pytest.raises(
        TurmaComVaga, match="A turma tem vaga: você pode se matricular sem lista de espera."
    ):
        exigir_turma_cheia(vagas_livres=1)


def test_r05_turma_cheia_aceita_a_lista_de_espera() -> None:
    exigir_turma_cheia(vagas_livres=0)


def test_r45_a_partir_da_13a_aula_a_lista_nao_recebe_ninguem() -> None:
    exigir_lista_aberta(aulas_dadas=12)

    with pytest.raises(
        ListaFechada, match="A lista de espera desta turma fechou: a etapa já chegou à 13ª aula."
    ):
        exigir_lista_aberta(aulas_dadas=13)


def test_r05_abre_vaga_as_14h_de_10_03_e_ana_pode_confirmar_ate_13_03_as_14h() -> None:
    lista = ana_com_a_vaga_ate_13_03_14h()

    assert prazos(lista) == {ANA: ATE_13_03_14H, BRUNO: None}
    assert reservadas(lista) == 1


def test_r05_com_duas_vagas_abertas_ana_e_bruno_recebem_uma_cada() -> None:
    lista = oferecer_vaga(ana_com_a_vaga_ate_13_03_14h(), SAIU_EM_10_03_14H, pode_oferecer=True)

    assert prazos(lista) == {ANA: ATE_13_03_14H, BRUNO: ATE_13_03_14H}
    assert reservadas(lista) == 2


def test_r45_a_vaga_que_abre_a_partir_da_13a_aula_nao_e_oferecida() -> None:
    lista = oferecer_vaga(lista_com(ANA, BRUNO), SAIU_EM_10_03_14H, pode_oferecer=False)

    assert prazos(lista) == {ANA: None, BRUNO: None}
    assert reservadas(lista) == 0


def test_r45_a_turma_oferece_a_vaga_ate_antes_de_comecar_a_13a_aula_da_etapa() -> None:
    # Turma de terça e quinta com a 1ª aula na terça 24/11/2026: a 13ª é na terça 05/01/2027.
    horario = novo_horario([DiaDaSemana.TERCA, DiaDaSemana.QUINTA], time(19), time(20, 30))
    turma = Turma(1, 1, 2, 10, horario, datetime(2026, 11, 24, 19, 0, tzinfo=BRASILIA))

    pode_oferecer = pode_oferecer_em(turma)

    assert pode_oferecer(datetime(2027, 1, 5, 18, 59, tzinfo=BRASILIA))
    assert not pode_oferecer(datetime(2027, 1, 5, 19, 0, tzinfo=BRASILIA))


def test_r05_ana_confirma_as_13h59_de_13_03_e_sai_da_lista() -> None:
    lista = confirmar(ana_com_a_vaga_ate_13_03_14h(), ANA, ATE_13_03_14H - UM_MINUTO, sempre)

    assert prazos(lista) == {BRUNO: None}


def test_r05_ana_nao_confirma_mais_as_14h_de_13_03() -> None:
    with pytest.raises(
        PrazoVencido, match="O prazo para confirmar a vaga terminou em 13/03/2027, às 14h."
    ):
        confirmar(ana_com_a_vaga_ate_13_03_14h(), ANA, ATE_13_03_14H, sempre)


def test_r35_bruno_confirma_a_vaga_que_passou_para_ele_quando_o_prazo_de_ana_venceu() -> None:
    # Ninguém olhou a lista depois das 14h de 13/03: a oferta do Bruno ainda não foi gravada.
    lista = confirmar(ana_com_a_vaga_ate_13_03_14h(), BRUNO, ATE_16_03_14H - UM_MINUTO, sempre)

    assert lista == ()


def test_quem_nao_recebeu_oferta_nao_confirma_vaga() -> None:
    with pytest.raises(SemOferta, match="Você não tem vaga oferecida nesta turma."):
        confirmar(ana_com_a_vaga_ate_13_03_14h(), BRUNO, SAIU_EM_10_03_14H, sempre)


def test_r05_r35_as_14h_de_13_03_ana_sai_da_lista_e_bruno_pode_confirmar_ate_16_03() -> None:
    lista = vencer_prazos(ana_com_a_vaga_ate_13_03_14h(), ATE_13_03_14H, sempre)

    assert prazos(lista) == {BRUNO: ATE_16_03_14H}


def test_r05_antes_do_fim_do_prazo_nada_muda() -> None:
    lista = ana_com_a_vaga_ate_13_03_14h()

    assert vencer_prazos(lista, ATE_13_03_14H - UM_MINUTO, sempre) == lista


def test_r35_cada_prazo_vencido_passa_a_vaga_adiante_ate_alguem_poder_confirmar() -> None:
    lista = oferecer_vaga(lista_com(ANA, BRUNO, CARLA), SAIU_EM_10_03_14H, pode_oferecer=True)

    lista = vencer_prazos(lista, ATE_16_03_14H + timedelta(hours=1), sempre)

    assert prazos(lista) == {CARLA: datetime(2027, 3, 19, 14, 0, tzinfo=BRASILIA)}


def test_r35_sem_ninguem_depois_o_ultimo_sai_e_a_vaga_fica_livre() -> None:
    lista = oferecer_vaga(lista_com(ANA), SAIU_EM_10_03_14H, pode_oferecer=True)

    assert vencer_prazos(lista, ATE_13_03_14H, sempre) == ()


def test_r45_o_prazo_que_vence_a_partir_da_13a_aula_nao_passa_a_vaga_adiante() -> None:
    lista = vencer_prazos(ana_com_a_vaga_ate_13_03_14h(), ATE_13_03_14H, nunca)

    assert prazos(lista) == {BRUNO: None}


def test_r44_ana_com_oferta_sai_da_lista_e_a_vaga_passa_para_bruno() -> None:
    agora = SAIU_EM_10_03_14H + timedelta(hours=5)

    lista = sair(ana_com_a_vaga_ate_13_03_14h(), ANA, agora, pode_oferecer=True)

    assert prazos(lista) == {BRUNO: agora + timedelta(hours=72)}


def test_r44_ana_sem_oferta_so_sai_da_lista() -> None:
    lista = sair(lista_com(ANA, BRUNO), ANA, SAIU_EM_10_03_14H, pode_oferecer=True)

    assert prazos(lista) == {BRUNO: None}


def test_sair_de_uma_lista_em_que_o_aluno_nao_esta_nao_muda_nada() -> None:
    lista = lista_com(BRUNO)

    assert sair(lista, ANA, SAIU_EM_10_03_14H, pode_oferecer=True) == lista


def test_na_lista_guarda_quando_o_aluno_entrou() -> None:
    entrou_em = datetime(2027, 3, 1, 9, 0, tzinfo=BRASILIA)

    assert lista_com(ANA) == (NaLista(aluno_id=ANA, entrou_em=entrou_em),)
