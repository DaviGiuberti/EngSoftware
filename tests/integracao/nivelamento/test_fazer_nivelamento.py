"""O aluno faz o nivelamento e o ADM abre exceções, com o banco SQLite e um relógio de teste
(H01, H02, H03, H33)."""

import sqlite3
from dataclasses import dataclass
from datetime import timedelta

import pytest

from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.application.casos_de_uso import (
    CadastrarAluno,
    ConsultaDeAlunos,
)
from plataforma.modules.identidade.domain.autorizacao import AcessoNegado
from plataforma.modules.identidade.domain.cadastro import AlunoNaoEncontrado
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.identidade.infra.repositorio_de_usuarios import (
    RepositorioDeUsuariosSqlite,
)
from plataforma.modules.materias.application.casos_de_uso import (
    CadastrarMateria,
    ConsultaDeMaterias,
)
from plataforma.modules.materias.domain.materia import Materia
from plataforma.modules.materias.infra.repositorio_de_materias import (
    RepositorioDeMateriasSqlite,
)
from plataforma.modules.nivelamento.application.casos_de_uso import CadastrarQuestao
from plataforma.modules.nivelamento.application.fazer_nivelamento import (
    ConcluirNivelamento,
    DarMaisTempo,
    EstadoDoNivelamento,
    FecharNivelamento,
    IniciarNivelamento,
    LiberarRefazer,
    RegistrarTempo,
    ResponderQuestao,
    Resultado,
    VerMeusNiveis,
)
from plataforma.modules.nivelamento.domain.nivelamento import (
    NadaParaRefazer,
    NivelamentoConcluido,
    NivelamentoJaFeito,
    NivelamentoNaoEncontrado,
    SemNivelamentoEmAndamento,
    SituacaoNaMateria,
)
from plataforma.modules.nivelamento.domain.questao import (
    NivelamentoIndisponivel,
    QuestaoParaResponder,
)
from plataforma.modules.nivelamento.infra.repositorio_de_nivelamentos import (
    RepositorioDeNivelamentosSqlite,
)
from plataforma.modules.nivelamento.infra.repositorio_de_questoes import (
    RepositorioDeQuestoesSqlite,
)
from tests.integracao.conftest import RelogioDeTeste

ADM = Usuario(id=1000, email="adm@exemplo.com", perfil=Perfil.ADM)
ALTERNATIVAS = ["A", "B", "C", "D", "E"]
# Todas as questões dos testes têm a correta na B.
CORRETA = 1
ERRADA = 0


@dataclass(frozen=True)
class Casos:
    cadastrar_aluno: CadastrarAluno
    cadastrar_materia: CadastrarMateria
    cadastrar_questao: CadastrarQuestao
    iniciar: IniciarNivelamento
    responder: ResponderQuestao
    registrar_tempo: RegistrarTempo
    fechar: FecharNivelamento
    concluir: ConcluirNivelamento
    ver_meus_niveis: VerMeusNiveis
    dar_mais_tempo: DarMaisTempo
    liberar_refazer: LiberarRefazer


@pytest.fixture
def casos(
    conexao: sqlite3.Connection, em_transacao: Transacao, relogio: RelogioDeTeste
) -> Casos:
    usuarios = RepositorioDeUsuariosSqlite(conexao)
    repositorio_de_materias = RepositorioDeMateriasSqlite(conexao)
    materias = ConsultaDeMaterias(repositorio_de_materias)
    questoes = RepositorioDeQuestoesSqlite(conexao)
    nivelamentos = RepositorioDeNivelamentosSqlite(conexao)
    alunos = ConsultaDeAlunos(usuarios)
    do_aluno = (nivelamentos, questoes, materias, relogio, em_transacao)
    return Casos(
        cadastrar_aluno=CadastrarAluno(usuarios, em_transacao),
        cadastrar_materia=CadastrarMateria(repositorio_de_materias, em_transacao),
        cadastrar_questao=CadastrarQuestao(questoes, materias, em_transacao),
        iniciar=IniciarNivelamento(*do_aluno),
        responder=ResponderQuestao(*do_aluno),
        registrar_tempo=RegistrarTempo(*do_aluno),
        fechar=FecharNivelamento(*do_aluno),
        concluir=ConcluirNivelamento(*do_aluno),
        ver_meus_niveis=VerMeusNiveis(nivelamentos, questoes, materias),
        dar_mais_tempo=DarMaisTempo(nivelamentos, materias, alunos, relogio, em_transacao),
        liberar_refazer=LiberarRefazer(nivelamentos, materias, alunos, em_transacao),
    )


def cadastrar_com_questoes(
    casos: Casos, nome: str, notas_minimas: list[int], quantidade_de_questoes: int
) -> Materia:
    materia = casos.cadastrar_materia.executar(
        ADM, nome, len(notas_minimas) + 1, notas_minimas, 20000
    )
    for numero in range(1, quantidade_de_questoes + 1):
        casos.cadastrar_questao.executar(
            ADM, materia.id, f"{nome}: questão {numero}?", ALTERNATIVAS, CORRETA
        )
    return materia


def fazer_com_acertos(
    casos: Casos, aluno: Usuario, materia: Materia, acertos: int
) -> EstadoDoNivelamento:
    """Inicia, acerta as primeiras questões, erra as outras e entrega o nivelamento."""
    estado = casos.iniciar.executar(aluno, materia.id)
    for indice, questao in enumerate(estado.questoes):
        posicao = CORRETA if indice < acertos else ERRADA
        estado = casos.responder.executar(aluno, estado.nivelamento_id, questao.id, posicao)
    return casos.concluir.executar(aluno, estado.nivelamento_id)


def niveis(casos: Casos, aluno: Usuario) -> list[tuple[str, int | None]]:
    return [(n.nome_da_materia, n.nivel) for n in casos.ver_meus_niveis.executar(aluno)]


@pytest.fixture
def ana(casos: Casos) -> Usuario:
    return casos.cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")


@pytest.fixture
def fisica(casos: Casos) -> Materia:
    return cadastrar_com_questoes(casos, "Física", [40, 70], 20)


def test_r02_8_acertos_em_20_questoes_de_fisica_dao_40_por_cento_e_o_n2(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    estado = fazer_com_acertos(casos, ana, fisica, 8)

    assert estado.resultado == Resultado(nota=40, nivel=2)
    assert niveis(casos, ana) == [("Física", 2)]


def test_r02_7_acertos_em_20_questoes_dao_35_por_cento_e_o_n1(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    assert fazer_com_acertos(casos, ana, fisica, 7).resultado == Resultado(nota=35, nivel=1)


def test_r01_o_nivel_de_uma_materia_nao_muda_o_de_outra(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    matematica = cadastrar_com_questoes(casos, "Matemática", [20, 40, 60, 80], 4)
    fazer_com_acertos(casos, ana, fisica, 15)

    fazer_com_acertos(casos, ana, matematica, 1)

    assert niveis(casos, ana) == [("Física", 3), ("Matemática", 2)]


def test_r03_o_nivelamento_e_feito_uma_vez_por_materia(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    fazer_com_acertos(casos, ana, fisica, 8)

    with pytest.raises(NivelamentoJaFeito, match="O nivelamento de Física já foi feito."):
        casos.iniciar.executar(ana, fisica.id)


def test_r34_quando_os_60_minutos_acabam_o_teste_e_corrigido_com_as_18_respostas(
    casos: Casos, ana: Usuario, relogio: RelogioDeTeste
) -> None:
    fisica = cadastrar_com_questoes(casos, "Física", [40, 70], 30)
    estado = casos.iniciar.executar(ana, fisica.id)
    for questao in estado.questoes[:18]:
        estado = casos.responder.executar(ana, estado.nivelamento_id, questao.id, CORRETA)
    relogio.avancar(minutes=60)

    estado = casos.registrar_tempo.executar(ana, estado.nivelamento_id)

    # As 12 questões sem resposta contam como erro: 18 de 30 dão 60%.
    assert estado.tempo_restante == timedelta(0)
    assert estado.resultado == Resultado(nota=60, nivel=2)


def test_r34_resposta_dada_depois_do_fim_do_tempo_nao_conta(
    casos: Casos, ana: Usuario, fisica: Materia, relogio: RelogioDeTeste
) -> None:
    estado = casos.iniciar.executar(ana, fisica.id)
    relogio.avancar(minutes=61)

    estado = casos.responder.executar(ana, estado.nivelamento_id, estado.questoes[0].id, CORRETA)

    assert estado.resultado == Resultado(nota=0, nivel=1)


def test_r34_entregar_depois_do_fim_do_tempo_corrige_com_o_que_foi_respondido(
    casos: Casos, ana: Usuario, fisica: Materia, relogio: RelogioDeTeste
) -> None:
    estado = casos.iniciar.executar(ana, fisica.id)
    for questao in estado.questoes[:8]:
        estado = casos.responder.executar(ana, estado.nivelamento_id, questao.id, CORRETA)
    relogio.avancar(minutes=61)

    estado = casos.concluir.executar(ana, estado.nivelamento_id)

    assert estado.resultado == Resultado(nota=40, nivel=2)


def test_r34_se_o_tempo_acabou_com_o_teste_fechado_ele_e_corrigido_ao_reabrir(
    casos: Casos, ana: Usuario, fisica: Materia, relogio: RelogioDeTeste
) -> None:
    estado = casos.iniciar.executar(ana, fisica.id)
    relogio.avancar(minutes=59)
    casos.registrar_tempo.executar(ana, estado.nivelamento_id)
    relogio.avancar(minutes=2)
    casos.fechar.executar(ana, estado.nivelamento_id)

    de_novo = casos.iniciar.executar(ana, fisica.id)

    assert de_novo.resultado == Resultado(nota=0, nivel=1)


def test_registrar_o_tempo_de_um_nivelamento_concluido_so_mostra_o_resultado(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    estado = fazer_com_acertos(casos, ana, fisica, 8)

    de_novo = casos.registrar_tempo.executar(ana, estado.nivelamento_id)

    assert de_novo.resultado == Resultado(nota=40, nivel=2)


def test_fechar_um_nivelamento_concluido_nao_muda_nada(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    estado = fazer_com_acertos(casos, ana, fisica, 8)

    casos.fechar.executar(ana, estado.nivelamento_id)

    assert niveis(casos, ana) == [("Física", 2)]


def test_nivelamento_que_nao_existe_e_recusado(casos: Casos, ana: Usuario) -> None:
    with pytest.raises(NivelamentoNaoEncontrado, match="Nivelamento não encontrado."):
        casos.responder.executar(ana, 999, 1, CORRETA)


def test_r30_as_respostas_dadas_continuam_salvas_quando_o_aluno_reabre(
    casos: Casos, ana: Usuario, relogio: RelogioDeTeste
) -> None:
    fisica = cadastrar_com_questoes(casos, "Física", [40, 70], 30)
    estado = casos.iniciar.executar(ana, fisica.id)
    for questao in estado.questoes[:10]:
        estado = casos.responder.executar(ana, estado.nivelamento_id, questao.id, CORRETA)
    casos.fechar.executar(ana, estado.nivelamento_id)
    relogio.avancar(hours=1)

    de_novo = casos.iniciar.executar(ana, fisica.id)

    assert de_novo.nivelamento_id == estado.nivelamento_id
    assert de_novo.respostas == {questao.id: CORRETA for questao in estado.questoes[:10]}


def test_r30_fechado_com_25_minutos_usados_e_reaberto_dois_dias_depois_tem_35(
    casos: Casos, ana: Usuario, fisica: Materia, relogio: RelogioDeTeste
) -> None:
    estado = casos.iniciar.executar(ana, fisica.id)
    relogio.avancar(minutes=25)
    casos.fechar.executar(ana, estado.nivelamento_id)
    relogio.avancar(days=2)

    assert casos.iniciar.executar(ana, fisica.id).tempo_restante == timedelta(minutes=35)


def test_r30_se_o_app_cai_o_tempo_depois_do_ultimo_registro_nao_conta(
    casos: Casos, ana: Usuario, fisica: Materia, relogio: RelogioDeTeste
) -> None:
    estado = casos.iniciar.executar(ana, fisica.id)
    relogio.avancar(minutes=20)
    casos.registrar_tempo.executar(ana, estado.nivelamento_id)
    relogio.avancar(days=1)

    assert casos.iniciar.executar(ana, fisica.id).tempo_restante == timedelta(minutes=40)


def test_o_aluno_recebe_as_questoes_sem_a_alternativa_correta(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    estado = casos.iniciar.executar(ana, fisica.id)

    assert len(estado.questoes) == 20
    assert all(isinstance(questao, QuestaoParaResponder) for questao in estado.questoes)
    assert estado.questoes[0].alternativas == tuple(ALTERNATIVAS)


def test_materia_sem_questoes_recusa_o_nivelamento(casos: Casos, ana: Usuario) -> None:
    quimica = casos.cadastrar_materia.executar(ADM, "Química", 3, [40, 70], 20000)

    with pytest.raises(
        NivelamentoIndisponivel, match="O nivelamento de Química ainda não está disponível."
    ):
        casos.iniciar.executar(ana, quimica.id)


def test_r01_o_aluno_no_n2_de_fisica_e_no_n4_de_matematica_ve_os_dois_niveis(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    matematica = cadastrar_com_questoes(casos, "Matemática", [20, 40, 60, 80], 5)
    fazer_com_acertos(casos, ana, fisica, 8)

    fazer_com_acertos(casos, ana, matematica, 3)

    assert niveis(casos, ana) == [("Física", 2), ("Matemática", 4)]


def test_r01_o_aluno_ve_a_situacao_de_cada_materia(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    matematica = cadastrar_com_questoes(casos, "Matemática", [20, 40, 60, 80], 5)
    casos.cadastrar_materia.executar(ADM, "Química", 3, [40, 70], 20000)
    fazer_com_acertos(casos, ana, fisica, 8)
    casos.iniciar.executar(ana, matematica.id)

    situacoes = [
        (n.nome_da_materia, n.nivel, n.situacao) for n in casos.ver_meus_niveis.executar(ana)
    ]

    assert situacoes == [
        ("Física", 2, SituacaoNaMateria.COM_NIVEL),
        ("Matemática", None, SituacaoNaMateria.EM_ANDAMENTO),
        ("Química", None, SituacaoNaMateria.INDISPONIVEL),
    ]


def test_r01_materia_sem_nivelamento_aparece_sem_nivel_e_com_a_opcao_de_fazer(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    [fisica_da_ana] = casos.ver_meus_niveis.executar(ana)

    assert fisica_da_ana.nivel is None
    assert fisica_da_ana.situacao == SituacaoNaMateria.SEM_NIVEL


def test_r30_o_adm_da_20_minutos_a_quem_tem_5_restantes_e_ele_fica_com_25(
    casos: Casos, ana: Usuario, fisica: Materia, relogio: RelogioDeTeste
) -> None:
    estado = casos.iniciar.executar(ana, fisica.id)
    relogio.avancar(minutes=55)
    casos.registrar_tempo.executar(ana, estado.nivelamento_id)

    novo_restante = casos.dar_mais_tempo.executar(ADM, "ana@exemplo.com", fisica.id, 20)

    assert novo_restante == timedelta(minutes=25)
    estado = casos.registrar_tempo.executar(ana, estado.nivelamento_id)
    assert estado.tempo_restante == timedelta(minutes=25)


def test_r30_o_adm_nao_da_mais_tempo_a_quem_nao_esta_fazendo_o_nivelamento(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    with pytest.raises(SemNivelamentoEmAndamento):
        casos.dar_mais_tempo.executar(ADM, "ana@exemplo.com", fisica.id, 20)


def test_r03_o_adm_libera_refazer_e_quem_tira_75_por_cento_passa_para_o_n3(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    fazer_com_acertos(casos, ana, fisica, 0)

    casos.liberar_refazer.executar(ADM, "ana@exemplo.com", fisica.id)
    estado = fazer_com_acertos(casos, ana, fisica, 15)

    assert estado.resultado == Resultado(nota=75, nivel=3)
    assert niveis(casos, ana) == [("Física", 3)]


def test_r03_a_liberacao_vale_para_uma_tentativa(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    fazer_com_acertos(casos, ana, fisica, 0)
    casos.liberar_refazer.executar(ADM, "ana@exemplo.com", fisica.id)
    fazer_com_acertos(casos, ana, fisica, 15)

    with pytest.raises(NivelamentoJaFeito):
        casos.iniciar.executar(ana, fisica.id)


def test_r42_resultado_menor_no_nivelamento_refeito_mantem_o_nivel(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    fazer_com_acertos(casos, ana, fisica, 8)
    casos.liberar_refazer.executar(ADM, "ana@exemplo.com", fisica.id)

    estado = fazer_com_acertos(casos, ana, fisica, 6)

    assert estado.resultado == Resultado(nota=30, nivel=2)
    assert niveis(casos, ana) == [("Física", 2)]


def test_r03_o_adm_nao_libera_refazer_para_quem_nao_fez_o_nivelamento(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    with pytest.raises(NadaParaRefazer):
        casos.liberar_refazer.executar(ADM, "ana@exemplo.com", fisica.id)


def test_o_adm_informa_um_email_que_nao_e_de_aluno(casos: Casos, fisica: Materia) -> None:
    with pytest.raises(AlunoNaoEncontrado, match="Nenhum aluno com este e-mail."):
        casos.liberar_refazer.executar(ADM, "ninguem@exemplo.com", fisica.id)


def test_nivelamento_concluido_nao_recebe_mais_respostas(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    estado = fazer_com_acertos(casos, ana, fisica, 8)

    with pytest.raises(NivelamentoConcluido, match="Este nivelamento já terminou."):
        casos.responder.executar(ana, estado.nivelamento_id, estado.questoes[0].id, CORRETA)


def test_rnf07_um_aluno_nao_responde_o_nivelamento_de_outro(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    bruno = casos.cadastrar_aluno.executar("bruno@exemplo.com", "abcd1234")
    estado = casos.iniciar.executar(ana, fisica.id)

    with pytest.raises(AcessoNegado, match="Este nivelamento é de outro aluno."):
        casos.responder.executar(bruno, estado.nivelamento_id, estado.questoes[0].id, CORRETA)


def test_rnf07_o_adm_nao_faz_nivelamento_e_o_aluno_nao_da_mais_tempo(
    casos: Casos, ana: Usuario, fisica: Materia
) -> None:
    with pytest.raises(AcessoNegado, match="Só o aluno pode fazer o nivelamento."):
        casos.iniciar.executar(ADM, fisica.id)

    with pytest.raises(AcessoNegado, match="Só o ADM pode dar mais tempo no nivelamento."):
        casos.dar_mais_tempo.executar(ana, "ana@exemplo.com", fisica.id, 20)
