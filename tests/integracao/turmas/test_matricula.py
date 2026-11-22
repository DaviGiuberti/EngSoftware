"""Matrícula, lista de espera, mensalidade e saída da turma com o banco SQLite e um relógio de
teste (H04, H05, H06, H07, H13, H27). R04 a R07, R19, R27 a R29, R35, R37, R44 a R47, R53 a R55,
RNF05 e RNF07."""

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.application.casos_de_uso import (
    CadastrarAluno,
    CadastrarProfessor,
    ConsultaDeProfessores,
    HabilitarProfessor,
)
from plataforma.modules.identidade.domain.autorizacao import AcessoNegado
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.identidade.infra.repositorio_de_professores import (
    RepositorioDeProfessoresSqlite,
)
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
from plataforma.modules.nivelamento.application.consulta_de_niveis import ConsultaDeNiveis
from plataforma.modules.nivelamento.application.promocao import Promocoes
from plataforma.modules.nivelamento.domain.nivelamento import NivelDoAluno
from plataforma.modules.nivelamento.infra.repositorio_de_nivelamentos import (
    RepositorioDeNivelamentosSqlite,
)
from plataforma.modules.turmas.application.casos_de_uso import CriarTurma, VerTurmas
from plataforma.modules.turmas.application.em_dia import TurmasEmDia
from plataforma.modules.turmas.application.matricula import (
    ConfirmarVaga,
    EntrarNaListaDeEspera,
    Matricular,
    PagarMensalidade,
    SairDaTurma,
    TurmaDoAluno,
    VerTurmasDoAluno,
    VerVagasPerdidas,
)
from plataforma.modules.turmas.domain.horario import DiaDaSemana
from plataforma.modules.turmas.domain.lista_de_espera import (
    ListaFechada,
    PrazoVencido,
    TurmaComVaga,
)
from plataforma.modules.turmas.domain.matricula import (
    JaTemTurmaNaMateria,
    MatriculaFechada,
    NivelDiferenteDaTurma,
    SemMatricula,
    SemNivelNaMateria,
    SituacaoNaTurma,
    TurmaCheia,
)
from plataforma.modules.turmas.domain.mensalidade import (
    MensalidadeNaoAberta,
    SemMensalidade,
    SituacaoDaMensalidade,
)
from plataforma.modules.turmas.domain.turma import ConflitoDeHorario, Turma
from plataforma.modules.turmas.infra.repositorio_de_turmas import RepositorioDeTurmasSqlite
from tests.integracao.conftest import RelogioDeTeste, pagar_mensalidades

ADM = Usuario(id=1000, email="adm@exemplo.com", perfil=Perfil.ADM)
SEG, TER, QUA, QUI = (
    DiaDaSemana.SEGUNDA,
    DiaDaSemana.TERCA,
    DiaDaSemana.QUARTA,
    DiaDaSemana.QUINTA,
)


def em(dia: int, mes: int, ano: int, hora: int = 14, minuto: int = 0) -> datetime:
    return datetime(ano, mes, dia, hora, minuto, tzinfo=BRASILIA)


@dataclass(frozen=True)
class Escola:
    """Os casos de uso e o que os testes precisam para montar a situação de cada critério."""

    conexao: sqlite3.Connection
    relogio: RelogioDeTeste
    cadastrar_aluno: CadastrarAluno
    cadastrar_materia: CadastrarMateria
    cadastrar_professor: CadastrarProfessor
    habilitar_professor: HabilitarProfessor
    criar_turma: CriarTurma
    ver_turmas: VerTurmas
    ver_turmas_do_aluno: VerTurmasDoAluno
    matricular: Matricular
    entrar_na_lista: EntrarNaListaDeEspera
    confirmar_vaga: ConfirmarVaga
    sair_da_turma: SairDaTurma
    pagar_mensalidade: PagarMensalidade
    ver_vagas_perdidas: VerVagasPerdidas
    niveis: ConsultaDeNiveis
    turmas: RepositorioDeTurmasSqlite

    def ir_para(self, momento: datetime) -> None:
        self.relogio.avancar(seconds=(momento - self.relogio.agora()).total_seconds())

    def aluno(self, email: str, materia: Materia, nivel: int) -> Usuario:
        """Um aluno com nível na matéria, como se tivesse feito o nivelamento."""
        aluno = self.cadastrar_aluno.executar(email, "abcd1234")
        RepositorioDeNivelamentosSqlite(self.conexao).salvar_nivel(
            aluno.id, NivelDoAluno(materia.id, nivel)
        )
        return aluno

    def professor(self, email: str, *materias: Materia) -> Usuario:
        professor = self.cadastrar_professor.executar(ADM, email, "abcd1234")
        for materia in materias:
            self.habilitar_professor.executar(ADM, professor.id, materia.id)
        return professor

    def turma(
        self,
        materia: Materia,
        nivel: int,
        professor: Usuario,
        dias: Sequence[DiaDaSemana] = (TER, QUI),
        inicio: time = time(19),
        fim: time = time(20, 30),
    ) -> Turma:
        return self.criar_turma.executar(
            ADM, materia.id, nivel, professor.id, dias, inicio, fim
        )

    def encher(self, turma: Turma, materia: Materia, quantos: int = 12) -> list[Usuario]:
        """Matricula na turma alunos do nível dela, até ela ter quantos alunos, com as
        mensalidades pagas, para eles não perderem a vaga por atraso (R28)."""
        alunos = [
            self.aluno(f"aluno{numero}.turma{turma.id}@exemplo.com", materia, turma.nivel)
            for numero in range(1, quantos + 1)
        ]
        for aluno in alunos:
            self.matricular.executar(aluno, turma.id)
            pagar_mensalidades(self.conexao, aluno.id, turma.id)
        return alunos

    def como_o_aluno_ve(self, aluno: Usuario, turma: Turma) -> TurmaDoAluno:
        return next(
            vista
            for vista in self.ver_turmas_do_aluno.executar(aluno)
            if vista.resumo.id == turma.id
        )

    def vagas_livres(self, turma: Turma) -> int:
        return next(r.vagas_livres for r in self.ver_turmas.executar(ADM) if r.id == turma.id)


@pytest.fixture
def escola(
    conexao: sqlite3.Connection, em_transacao: Transacao, relogio: RelogioDeTeste
) -> Escola:
    usuarios = RepositorioDeUsuariosSqlite(conexao)
    repositorio_de_professores = RepositorioDeProfessoresSqlite(conexao)
    professores = ConsultaDeProfessores(repositorio_de_professores)
    repositorio_de_materias = RepositorioDeMateriasSqlite(conexao)
    materias = ConsultaDeMaterias(repositorio_de_materias)
    nivelamentos = RepositorioDeNivelamentosSqlite(conexao)
    niveis = ConsultaDeNiveis(nivelamentos)
    turmas = RepositorioDeTurmasSqlite(conexao)
    em_dia = TurmasEmDia(turmas, materias, Promocoes(nivelamentos, materias))
    do_aluno = (turmas, materias, professores, niveis, relogio, em_transacao, em_dia)
    return Escola(
        conexao=conexao,
        relogio=relogio,
        cadastrar_aluno=CadastrarAluno(usuarios, em_transacao),
        cadastrar_materia=CadastrarMateria(repositorio_de_materias, em_transacao),
        cadastrar_professor=CadastrarProfessor(usuarios, em_transacao),
        habilitar_professor=HabilitarProfessor(repositorio_de_professores, materias, em_transacao),
        criar_turma=CriarTurma(turmas, materias, professores, relogio, em_transacao, em_dia),
        ver_turmas=VerTurmas(turmas, materias, professores, relogio, em_transacao, em_dia),
        ver_turmas_do_aluno=VerTurmasDoAluno(*do_aluno),
        matricular=Matricular(*do_aluno),
        entrar_na_lista=EntrarNaListaDeEspera(*do_aluno),
        confirmar_vaga=ConfirmarVaga(*do_aluno),
        sair_da_turma=SairDaTurma(*do_aluno),
        pagar_mensalidade=PagarMensalidade(*do_aluno),
        ver_vagas_perdidas=VerVagasPerdidas(*do_aluno),
        niveis=niveis,
        turmas=turmas,
    )


@pytest.fixture
def fisica(escola: Escola) -> Materia:
    return escola.cadastrar_materia.executar(ADM, "Física", 3, [40, 70], 20000)


@pytest.fixture
def matematica(escola: Escola) -> Materia:
    return escola.cadastrar_materia.executar(ADM, "Matemática", 5, [20, 40, 60, 80], 25000)


@pytest.fixture
def carlos(escola: Escola, fisica: Materia) -> Usuario:
    return escola.professor("carlos@exemplo.com", fisica)


@pytest.fixture
def dora(escola: Escola, fisica: Materia, matematica: Materia) -> Usuario:
    return escola.professor("dora@exemplo.com", fisica, matematica)


# A turma criada pelo relógio de teste, na segunda 23/11/2026 às 14h, tem a 1ª aula na terça
# 24/11, às 19h. A 12ª aula é na quinta 31/12, e a 13ª, na terça 05/01/2027, às 19h.


def test_r27_ana_se_matricula_em_10_03_paga_r_200_e_a_proxima_vence_em_10_04(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    escola.ir_para(em(8, 3, 2027))
    turma = escola.turma(fisica, 2, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    escola.ir_para(em(10, 3, 2027, 10))

    feita = escola.matricular.executar(ana, turma.id)

    assert feita.valor_pago_em_centavos == 20000
    assert feita.proximo_vencimento == date(2027, 4, 10)
    vista = escola.como_o_aluno_ve(ana, turma)
    assert vista.situacao == SituacaoNaTurma.MATRICULADO
    assert vista.proximo_vencimento == date(2027, 4, 10)
    assert escola.vagas_livres(turma) == 11


def test_r27_a_primeira_mensalidade_de_uma_turma_de_matematica_e_de_r_250(
    escola: Escola, matematica: Materia, dora: Usuario
) -> None:
    turma = escola.turma(matematica, 2, dora)
    ana = escola.aluno("ana@exemplo.com", matematica, 2)

    assert escola.matricular.executar(ana, turma.id).valor_pago_em_centavos == 25000


def test_r06_aluno_no_n2_nao_se_matricula_numa_turma_do_n3(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 3, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)

    with pytest.raises(NivelDiferenteDaTurma, match="Esta turma é do N3 de Física"):
        escola.matricular.executar(ana, turma.id)

    assert escola.vagas_livres(turma) == 12


def test_r06_aluno_sem_nivel_na_materia_nao_se_matricula(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 2, carlos)
    ana = escola.cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")

    with pytest.raises(SemNivelNaMateria, match="Faça o nivelamento de Física"):
        escola.matricular.executar(ana, turma.id)


def test_r07_aluno_com_matematica_as_tercas_19h_nao_entra_em_fisica_as_tercas_20h(
    escola: Escola, fisica: Materia, matematica: Materia, carlos: Usuario, dora: Usuario
) -> None:
    matematica_ter_19h = escola.turma(matematica, 2, dora, [TER], time(19), time(20, 30))
    fisica_ter_e_qui_20h = escola.turma(fisica, 2, carlos, [TER, QUI], time(20), time(21, 30))
    ana = escola.aluno("ana@exemplo.com", matematica, 2)
    RepositorioDeNivelamentosSqlite(escola.conexao).salvar_nivel(ana.id, NivelDoAluno(fisica.id, 2))
    escola.matricular.executar(ana, matematica_ter_19h.id)

    with pytest.raises(
        ConflitoDeHorario,
        match="Conflito de horário: você já tem uma turma às terças, das 19h às 20h30.",
    ):
        escola.matricular.executar(ana, fisica_ter_e_qui_20h.id)


def test_r19_com_12_aulas_dadas_a_matricula_e_aceita_e_ele_fara_da_13a_a_24a(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 2, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    escola.ir_para(em(1, 1, 2027, 10))

    assert escola.matricular.executar(ana, turma.id).aula_de_entrada == 13


def test_r19_com_13_aulas_dadas_a_matricula_e_recusada(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 2, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    escola.ir_para(em(5, 1, 2027, 19))

    with pytest.raises(MatriculaFechada, match="só dá para entrar até antes da 13ª aula"):
        escola.matricular.executar(ana, turma.id)


def test_r44_aluno_com_turma_de_fisica_nao_se_matricula_em_outra_de_fisica(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    terca_e_quinta = escola.turma(fisica, 2, carlos)
    segunda = escola.turma(fisica, 2, carlos, [SEG])
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    escola.matricular.executar(ana, terca_e_quinta.id)

    with pytest.raises(JaTemTurmaNaMateria, match="Você já está numa turma de Física."):
        escola.matricular.executar(ana, segunda.id)


def test_r04_turma_com_12_alunos_recusa_a_matricula_e_oferece_a_lista(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 2, carlos)
    escola.encher(turma, fisica)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)

    with pytest.raises(TurmaCheia, match="Turma cheia: você pode entrar na lista de espera."):
        escola.matricular.executar(ana, turma.id)

    assert escola.como_o_aluno_ve(ana, turma).situacao == SituacaoNaTurma.CHEIA


def test_r05_a_lista_segue_a_ordem_de_entrada(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 2, carlos)
    escola.encher(turma, fisica)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    bruno = escola.aluno("bruno@exemplo.com", fisica, 2)

    assert escola.entrar_na_lista.executar(ana, turma.id) == 1
    assert escola.entrar_na_lista.executar(bruno, turma.id) == 2
    assert escola.como_o_aluno_ve(bruno, turma).posicao_na_lista == 2


def test_r06_a_lista_de_espera_tambem_exige_o_nivel_da_turma(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 2, carlos)
    escola.encher(turma, fisica)
    ana = escola.aluno("ana@exemplo.com", fisica, 1)

    with pytest.raises(NivelDiferenteDaTurma):
        escola.entrar_na_lista.executar(ana, turma.id)


def test_r05_turma_com_11_alunos_nao_tem_lista_e_oferece_a_matricula(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 2, carlos)
    escola.encher(turma, fisica, 11)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)

    with pytest.raises(TurmaComVaga, match="você pode se matricular"):
        escola.entrar_na_lista.executar(ana, turma.id)


def test_r45_a_partir_da_13a_aula_a_lista_nao_recebe_ninguem(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 2, carlos)
    escola.encher(turma, fisica)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    escola.ir_para(em(5, 1, 2027, 19))

    with pytest.raises(ListaFechada):
        escola.entrar_na_lista.executar(ana, turma.id)


@dataclass(frozen=True)
class TurmaComLista:
    turma: Turma
    alunos: list[Usuario]
    ana: Usuario
    bruno: Usuario


@pytest.fixture
def turma_cheia_com_ana_e_bruno_na_lista(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> TurmaComLista:
    """Turma de Física do N2, criada na segunda 08/03/2027, cheia, com Ana em 1º na lista de
    espera e Bruno em 2º."""
    escola.ir_para(em(8, 3, 2027))
    turma = escola.turma(fisica, 2, carlos)
    alunos = escola.encher(turma, fisica)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    bruno = escola.aluno("bruno@exemplo.com", fisica, 2)
    escola.entrar_na_lista.executar(ana, turma.id)
    escola.entrar_na_lista.executar(bruno, turma.id)
    return TurmaComLista(turma, alunos, ana, bruno)


@pytest.fixture
def vaga_para_ana_ate_13_03_14h(
    escola: Escola, turma_cheia_com_ana_e_bruno_na_lista: TurmaComLista
) -> TurmaComLista:
    """Um aluno sai da turma em 10/03 às 14h."""
    situacao = turma_cheia_com_ana_e_bruno_na_lista
    escola.ir_para(em(10, 3, 2027))
    escola.sair_da_turma.executar(situacao.alunos[0], situacao.turma.id)
    return situacao


def test_r05_aluno_sai_em_10_03_as_14h_e_ana_e_avisada_para_confirmar_ate_13_03_as_14h(
    escola: Escola, vaga_para_ana_ate_13_03_14h: TurmaComLista
) -> None:
    situacao = vaga_para_ana_ate_13_03_14h

    vista_da_ana = escola.como_o_aluno_ve(situacao.ana, situacao.turma)

    assert vista_da_ana.situacao == SituacaoNaTurma.VAGA_OFERECIDA
    assert vista_da_ana.prazo_para_confirmar == em(13, 3, 2027)
    vista_do_bruno = escola.como_o_aluno_ve(situacao.bruno, situacao.turma)
    assert vista_do_bruno.situacao == SituacaoNaTurma.NA_LISTA
    assert vista_do_bruno.posicao_na_lista == 2


def test_r05_a_vaga_fica_reservada_e_outro_aluno_e_recusado_em_11_03(
    escola: Escola, fisica: Materia, vaga_para_ana_ate_13_03_14h: TurmaComLista
) -> None:
    situacao = vaga_para_ana_ate_13_03_14h
    carla = escola.aluno("carla@exemplo.com", fisica, 2)
    escola.ir_para(em(11, 3, 2027))

    with pytest.raises(TurmaCheia, match="reservada para a lista de espera"):
        escola.matricular.executar(carla, situacao.turma.id)

    assert escola.vagas_livres(situacao.turma) == 0


def test_r05_r47_ana_confirma_as_13h59_fica_matriculada_com_a_mensalidade_paga(
    escola: Escola, vaga_para_ana_ate_13_03_14h: TurmaComLista
) -> None:
    situacao = vaga_para_ana_ate_13_03_14h
    escola.ir_para(em(13, 3, 2027, 13, 59))

    feita = escola.confirmar_vaga.executar(situacao.ana, situacao.turma.id)

    assert feita.valor_pago_em_centavos == 20000
    assert escola.como_o_aluno_ve(situacao.ana, situacao.turma).situacao == (
        SituacaoNaTurma.MATRICULADO
    )
    assert escola.como_o_aluno_ve(situacao.bruno, situacao.turma).posicao_na_lista == 1


def test_r05_r35_as_14h_ana_sai_da_lista_e_bruno_pode_confirmar_ate_16_03_as_14h(
    escola: Escola, vaga_para_ana_ate_13_03_14h: TurmaComLista
) -> None:
    situacao = vaga_para_ana_ate_13_03_14h
    escola.ir_para(em(13, 3, 2027))

    vista_do_bruno = escola.como_o_aluno_ve(situacao.bruno, situacao.turma)

    assert vista_do_bruno.situacao == SituacaoNaTurma.VAGA_OFERECIDA
    assert vista_do_bruno.prazo_para_confirmar == em(16, 3, 2027)
    assert escola.como_o_aluno_ve(situacao.ana, situacao.turma).situacao == SituacaoNaTurma.CHEIA
    with pytest.raises(PrazoVencido, match="terminou em 13/03/2027, às 14h"):
        escola.confirmar_vaga.executar(situacao.ana, situacao.turma.id)


def test_r45_a_vaga_que_abre_a_partir_da_13a_aula_nao_e_oferecida(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 2, carlos)
    alunos = escola.encher(turma, fisica)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    escola.entrar_na_lista.executar(ana, turma.id)
    escola.ir_para(em(5, 1, 2027, 20))

    escola.sair_da_turma.executar(alunos[0], turma.id)

    assert escola.como_o_aluno_ve(ana, turma).situacao == SituacaoNaTurma.NA_LISTA
    assert escola.vagas_livres(turma) == 1


def test_r44_ana_na_lista_de_duas_turmas_de_fisica_confirma_uma_e_sai_da_outra(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    terca_e_quinta = escola.turma(fisica, 2, carlos)
    segunda = escola.turma(fisica, 2, carlos, [SEG])
    alunos = escola.encher(terca_e_quinta, fisica)
    escola.encher(segunda, fisica)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    escola.entrar_na_lista.executar(ana, terca_e_quinta.id)
    escola.entrar_na_lista.executar(ana, segunda.id)
    escola.sair_da_turma.executar(alunos[0], terca_e_quinta.id)

    escola.confirmar_vaga.executar(ana, terca_e_quinta.id)

    assert escola.como_o_aluno_ve(ana, terca_e_quinta).situacao == SituacaoNaTurma.MATRICULADO
    assert escola.como_o_aluno_ve(ana, segunda).situacao == SituacaoNaTurma.CHEIA


def test_r29_aluno_sai_da_turma_sem_reembolso_e_continua_no_n2(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    escola.ir_para(em(8, 3, 2027))
    turma = escola.turma(fisica, 2, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    escola.ir_para(em(10, 3, 2027))
    matricula = escola.matricular.executar(ana, turma.id).matricula
    escola.ir_para(em(20, 3, 2027))

    escola.sair_da_turma.executar(ana, turma.id)

    assert escola.como_o_aluno_ve(ana, turma).situacao == SituacaoNaTurma.COM_VAGA
    assert escola.vagas_livres(turma) == 12
    [paga] = escola.turmas.mensalidades(matricula.id)
    assert paga.valor_em_centavos == 20000
    assert escola.niveis.nivel_do_aluno(ana.id, fisica.id) == 2


def test_quem_nao_tem_matricula_nao_sai_da_turma(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 2, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)

    with pytest.raises(SemMatricula, match="Você não tem matrícula nesta turma."):
        escola.sair_da_turma.executar(ana, turma.id)


def test_r46_matricula_em_31_01_e_em_10_02_a_proxima_mensalidade_vence_em_28_02(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    escola.ir_para(em(25, 1, 2027))
    turma = escola.turma(fisica, 2, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    escola.ir_para(em(31, 1, 2027, 10))
    escola.matricular.executar(ana, turma.id)

    escola.ir_para(em(10, 2, 2027))

    assert escola.como_o_aluno_ve(ana, turma).proximo_vencimento == date(2027, 2, 28)


def test_o_aluno_ve_as_turmas_do_nivel_dele_e_as_dele(
    escola: Escola, fisica: Materia, matematica: Materia, carlos: Usuario, dora: Usuario
) -> None:
    fisica_n2 = escola.turma(fisica, 2, carlos)
    escola.turma(fisica, 3, carlos, [SEG])
    escola.turma(matematica, 1, dora, [QUA])
    ana = escola.aluno("ana@exemplo.com", fisica, 2)

    vistas = escola.ver_turmas_do_aluno.executar(ana)

    assert [(v.resumo.id, v.situacao, v.mensalidade_em_centavos) for v in vistas] == [
        (fisica_n2.id, SituacaoNaTurma.COM_VAGA, 20000)
    ]


def test_rnf07_so_o_aluno_se_matricula_e_entra_na_lista(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 2, carlos)

    with pytest.raises(AcessoNegado, match="Só o aluno pode se matricular numa turma."):
        escola.matricular.executar(ADM, turma.id)
    with pytest.raises(AcessoNegado, match="Só o aluno pode entrar na lista de espera."):
        escola.entrar_na_lista.executar(carlos, turma.id)


def test_rnf05_erro_ao_gravar_a_mensalidade_nao_deixa_a_matricula_pela_metade(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    turma = escola.turma(fisica, 2, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    # A matrícula é gravada antes da mensalidade. O trigger faz a mensalidade falhar.
    escola.conexao.execute(
        "CREATE TRIGGER falha_na_mensalidade BEFORE INSERT ON mensalidade "
        "BEGIN SELECT RAISE(ABORT, 'falha forçada no teste'); END"
    )

    with pytest.raises(sqlite3.DatabaseError, match="falha forçada no teste"):
        escola.matricular.executar(ana, turma.id)

    assert escola.vagas_livres(turma) == 12


# H07: a mensalidade seguinte, o pagamento e a perda da vaga por atraso.


@pytest.fixture
def ana_desde_10_03(escola: Escola, fisica: Materia, carlos: Usuario) -> tuple[Usuario, Turma]:
    """Ana se matriculou em 10/03/2027 numa turma de Física do N2 criada em 09/03, de terça e
    quinta: a mensalidade de 10/04 fica em aberto desde 10/03."""
    escola.ir_para(em(9, 3, 2027))
    turma = escola.turma(fisica, 2, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    escola.ir_para(em(10, 3, 2027, 10))
    escola.matricular.executar(ana, turma.id)
    return ana, turma


def test_r27_matriculada_em_10_03_ana_ve_em_20_03_a_mensalidade_de_r_200_que_vence_em_10_04(
    escola: Escola, ana_desde_10_03: tuple[Usuario, Turma]
) -> None:
    ana, turma = ana_desde_10_03
    escola.ir_para(em(20, 3, 2027))

    vista = escola.como_o_aluno_ve(ana, turma)

    assert vista.mensalidade_devida is not None
    assert (vista.mensalidade_devida.vencimento, vista.mensalidade_em_centavos) == (
        date(2027, 4, 10),
        20000,
    )
    assert vista.situacao_da_mensalidade == SituacaoDaMensalidade.EM_ABERTO


def test_r27_r53_ana_paga_em_08_04_a_de_10_04_e_a_de_10_05_so_abre_em_10_04(
    escola: Escola, ana_desde_10_03: tuple[Usuario, Turma]
) -> None:
    ana, turma = ana_desde_10_03
    escola.ir_para(em(8, 4, 2027))

    paga = escola.pagar_mensalidade.executar(ana, turma.id)

    assert (paga.vencimento, paga.valor_em_centavos, paga.paga_em) == (
        date(2027, 4, 10),
        20000,
        em(8, 4, 2027),
    )
    assert paga.proximo_vencimento == date(2027, 5, 10)
    vista = escola.como_o_aluno_ve(ana, turma)
    assert vista.proximo_vencimento == date(2027, 5, 10)
    assert vista.situacao_da_mensalidade == SituacaoDaMensalidade.A_ABRIR
    with pytest.raises(
        MensalidadeNaoAberta, match="A mensalidade de 10/05/2027 só pode ser paga a partir de "
    ):
        escola.pagar_mensalidade.executar(ana, turma.id)


def test_r28_ana_paga_em_17_04_as_23h_continua_na_turma_e_a_proxima_vence_em_10_05(
    escola: Escola, ana_desde_10_03: tuple[Usuario, Turma]
) -> None:
    ana, turma = ana_desde_10_03
    escola.ir_para(em(17, 4, 2027, 23))
    assert escola.como_o_aluno_ve(ana, turma).situacao_da_mensalidade == (
        SituacaoDaMensalidade.ATRASADA
    )

    escola.pagar_mensalidade.executar(ana, turma.id)

    escola.ir_para(em(18, 4, 2027))
    vista = escola.como_o_aluno_ve(ana, turma)
    assert vista.situacao == SituacaoNaTurma.MATRICULADO
    assert vista.proximo_vencimento == date(2027, 5, 10)


def test_r28_r55_sem_pagar_a_de_10_04_ana_perde_a_vaga_em_18_04_e_ve_o_aviso(
    escola: Escola, ana_desde_10_03: tuple[Usuario, Turma]
) -> None:
    ana, turma = ana_desde_10_03
    escola.ir_para(em(17, 4, 2027, 23, 59))
    assert escola.como_o_aluno_ve(ana, turma).situacao == SituacaoNaTurma.MATRICULADO
    assert escola.ver_vagas_perdidas.executar(ana) == []

    escola.ir_para(em(18, 4, 2027, 0))

    assert escola.como_o_aluno_ve(ana, turma).situacao == SituacaoNaTurma.COM_VAGA
    assert escola.vagas_livres(turma) == 12
    [perdida] = escola.ver_vagas_perdidas.executar(ana)
    assert (perdida.turma_id, perdida.nome_da_materia, perdida.perdida_em) == (
        turma.id,
        "Física",
        em(18, 4, 2027, 0),
    )
    with pytest.raises(SemMatricula):
        escola.pagar_mensalidade.executar(ana, turma.id)


def test_r55_o_aviso_some_quando_ana_entra_de_novo_numa_turma_de_fisica(
    escola: Escola, ana_desde_10_03: tuple[Usuario, Turma]
) -> None:
    ana, turma = ana_desde_10_03
    # Na segunda 19/04, a turma deu 12 aulas: a matrícula ainda está aberta (R19).
    escola.ir_para(em(19, 4, 2027))
    assert len(escola.ver_vagas_perdidas.executar(ana)) == 1

    escola.matricular.executar(ana, turma.id)

    assert escola.ver_vagas_perdidas.executar(ana) == []


def test_r05_r28_a_vaga_que_ana_perde_vai_para_bruno_na_lista_de_espera(
    escola: Escola, fisica: Materia, ana_desde_10_03: tuple[Usuario, Turma]
) -> None:
    _, turma = ana_desde_10_03
    escola.encher(turma, fisica, quantos=11)
    bruno = escola.aluno("bruno@exemplo.com", fisica, 2)
    escola.entrar_na_lista.executar(bruno, turma.id)

    escola.ir_para(em(18, 4, 2027, 1))

    vista = escola.como_o_aluno_ve(bruno, turma)
    assert vista.situacao == SituacaoNaTurma.VAGA_OFERECIDA
    assert vista.prazo_para_confirmar == em(21, 4, 2027, 0)


def test_r54_depois_que_a_turma_encerra_nenhuma_mensalidade_vence_e_ana_continua_nela(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    # A turma do N3, o nível máximo, criada em 16/12/2026, encerra em 09/03/2027 às 20h30. Ana
    # pagou as mensalidades de 16/01 e 16/02 e espera a nota da prova final (R23).
    escola.ir_para(em(16, 12, 2026))
    turma = escola.turma(fisica, 3, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica, 3)
    escola.matricular.executar(ana, turma.id)
    pagar_mensalidades(escola.conexao, ana.id, turma.id, quantas=2)

    escola.ir_para(em(25, 3, 2027))

    vista = escola.como_o_aluno_ve(ana, turma)
    assert vista.situacao == SituacaoNaTurma.MATRICULADO
    assert vista.situacao_da_mensalidade == SituacaoDaMensalidade.SEM_MENSALIDADE
    with pytest.raises(SemMensalidade, match="A turma encerrou: não há mensalidade a pagar."):
        escola.pagar_mensalidade.executar(ana, turma.id)


def test_rnf07_so_o_aluno_paga_a_mensalidade(
    escola: Escola, carlos: Usuario, ana_desde_10_03: tuple[Usuario, Turma]
) -> None:
    _, turma = ana_desde_10_03

    with pytest.raises(AcessoNegado, match="Só o aluno pode pagar a mensalidade."):
        escola.pagar_mensalidade.executar(carlos, turma.id)


def test_quem_nao_tem_matricula_nao_paga_mensalidade(
    escola: Escola, fisica: Materia, ana_desde_10_03: tuple[Usuario, Turma]
) -> None:
    _, turma = ana_desde_10_03
    bruno = escola.aluno("bruno@exemplo.com", fisica, 2)

    with pytest.raises(SemMatricula, match="Você não tem matrícula nesta turma."):
        escola.pagar_mensalidade.executar(bruno, turma.id)
