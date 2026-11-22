"""Fim da etapa com o banco SQLite e um relógio de teste (H23, H09, H10, H11, H24, H32, H20, H03,
H12): a turma passa de nível e encerra, a nota da prova final é lançada e corrigida, e o resultado
vale no fim das 72 horas de correção, com a promoção e os certificados ou a saída da turma. R04,
R07, R08, R09, R10, R17, R19, R20 a R23, R25, R26, R33, R36, R48, R49 a R52, RNF05 e RNF07."""

import shutil
import sqlite3
from collections.abc import Collection, Mapping
from contextlib import closing
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

import pytest

from plataforma.banco import PASTA_MIGRACOES, aplicar_migracoes, conectar
from plataforma.compartilhado.horario import BRASILIA
from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.application.casos_de_uso import (
    CadastrarAluno,
    CadastrarProfessor,
    ConsultaDeAlunos,
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
from plataforma.modules.nivelamento.application.certificados import VerMeusCertificados
from plataforma.modules.nivelamento.application.consulta_de_niveis import ConsultaDeNiveis
from plataforma.modules.nivelamento.application.fazer_nivelamento import VerMeusNiveis
from plataforma.modules.nivelamento.application.promocao import Promocoes
from plataforma.modules.nivelamento.domain.certificado import TipoDeCertificado
from plataforma.modules.nivelamento.domain.nivelamento import NivelDoAluno
from plataforma.modules.nivelamento.domain.promocao import Promocao
from plataforma.modules.nivelamento.infra.repositorio_de_nivelamentos import (
    RepositorioDeNivelamentosSqlite,
)
from plataforma.modules.nivelamento.infra.repositorio_de_questoes import (
    RepositorioDeQuestoesSqlite,
)
from plataforma.modules.turmas.application.casos_de_uso import (
    CriarTurma,
    EncerrarTurma,
    ResumoDaTurma,
    VerMinhasTurmas,
    VerTurmas,
)
from plataforma.modules.turmas.application.em_dia import AtualizarTurmas, TurmasEmDia
from plataforma.modules.turmas.application.matricula import (
    EntrarNaListaDeEspera,
    Matricular,
    SairDaTurma,
    TurmaDoAluno,
    VerTurmasDoAluno,
)
from plataforma.modules.turmas.application.presenca import (
    CorrigirPresenca,
    LancarPresenca,
    MarcarAulaNaoRealizada,
    SituacaoDaAula,
    VerAulasDaTurma,
)
from plataforma.modules.turmas.application.prova_final import (
    AlunoNaProvaFinal,
    CorrigirNota,
    LancarNota,
    VerProvaFinal,
)
from plataforma.modules.turmas.domain.etapa import EtapaTerminada
from plataforma.modules.turmas.domain.horario import DiaDaSemana
from plataforma.modules.turmas.domain.matricula import SituacaoNaTurma
from plataforma.modules.turmas.domain.prova_final import (
    AlunoForaDaEtapa,
    EtapaNaoTerminou,
    NotaInvalida,
    NotaJaLancada,
    PrazoDeCorrecaoVencido,
    ResultadoEtapa,
)
from plataforma.modules.turmas.domain.turma import Turma, TurmaAberta, TurmaEncerrada
from plataforma.modules.turmas.infra.repositorio_de_turmas import RepositorioDeTurmasSqlite
from tests.integracao.conftest import RelogioDeTeste, pagar_mensalidades

ADM = Usuario(id=1000, email="adm@exemplo.com", perfil=Perfil.ADM)
TER_E_QUI = (DiaDaSemana.TERCA, DiaDaSemana.QUINTA)
SEG_E_QUA = (DiaDaSemana.SEGUNDA, DiaDaSemana.QUARTA)


def em(dia: int, mes: int, hora: int = 10, minuto: int = 0, ano: int = 2027) -> datetime:
    return datetime(ano, mes, dia, hora, minuto, tzinfo=BRASILIA)


# A turma de terça e quinta, das 19h às 20h30, criada na quarta 16/12/2026 tem a 1ª aula na
# quinta 17/12/2026, a 5ª na quinta 31/12, a 20ª na terça 23/02/2027 e a 24ª na terça 09/03/2027.
# A etapa termina às 20h30 de 09/03, e a seguinte começa na quinta 11/03, às 19h.
CRIACAO = em(16, 12, 14, ano=2026)
DURANTE_A_24A_AULA = em(9, 3, 20)
FIM_DA_ETAPA = em(9, 3, 20, 30)
INICIO_DA_ETAPA_SEGUINTE = em(11, 3, 19)
NOTA_EM_10_03_AS_10H = em(10, 3)


@dataclass(frozen=True)
class Escola:
    """Os casos de uso e o que os testes precisam para montar a situação de cada critério."""

    conexao: sqlite3.Connection
    relogio: RelogioDeTeste
    cadastrar_aluno: CadastrarAluno
    cadastrar_professor: CadastrarProfessor
    habilitar_professor: HabilitarProfessor
    criar_turma: CriarTurma
    ver_turmas: VerTurmas
    ver_minhas_turmas: VerMinhasTurmas
    encerrar_turma: EncerrarTurma
    atualizar: AtualizarTurmas
    matricular: Matricular
    sair_da_turma: SairDaTurma
    entrar_na_lista: EntrarNaListaDeEspera
    ver_turmas_do_aluno: VerTurmasDoAluno
    ver_aulas: VerAulasDaTurma
    lancar_presenca: LancarPresenca
    corrigir_presenca: CorrigirPresenca
    marcar_nao_realizada: MarcarAulaNaoRealizada
    ver_prova_final: VerProvaFinal
    lancar_nota: LancarNota
    corrigir_nota: CorrigirNota
    ver_meus_niveis: VerMeusNiveis
    ver_meus_certificados: VerMeusCertificados
    niveis: ConsultaDeNiveis
    promocoes: Promocoes
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

    def professor(self, email: str, materia: Materia) -> Usuario:
        professor = self.cadastrar_professor.executar(ADM, email, "abcd1234")
        self.habilitar_professor.executar(ADM, professor.id, materia.id)
        return professor

    def turma(
        self,
        materia: Materia,
        nivel: int,
        professor: Usuario,
        dias: tuple[DiaDaSemana, ...] = TER_E_QUI,
    ) -> Turma:
        """Uma turma criada na hora do relógio, das 19h às 20h30."""
        return self.criar_turma.executar(
            ADM, materia.id, nivel, professor.id, dias, time(19), time(20, 30)
        )

    def data_da_aula(self, turma: Turma, numero: int, nivel: int) -> date:
        """A data da aula de número dado na etapa do nível."""
        etapa = next(etapa for etapa in self.turmas.etapas(turma.id) if etapa.nivel == nivel)
        return next(aula.data for aula in etapa.calendario() if aula.numero == numero)

    def lancar(
        self, quem: Usuario, turma: Turma, numero: int, ausentes: Collection[Usuario] = ()
    ) -> None:
        """Lança a presença de uma aula da etapa em que a turma foi criada."""
        data = self.data_da_aula(turma, numero, turma.nivel)
        self.lancar_presenca.executar(quem, turma.id, data, {aluno.id for aluno in ausentes})

    def lancar_a_etapa(
        self, quem: Usuario, turma: Turma, faltas: Mapping[Usuario, Collection[int]]
    ) -> None:
        """Lança as 24 aulas da etapa, com as aulas a que cada aluno faltou."""
        for numero in range(1, 25):
            ausentes = [aluno for aluno, aulas in faltas.items() if numero in aulas]
            self.lancar(quem, turma, numero, ausentes)

    def nivel(self, aluno: Usuario, materia: Materia) -> int | None:
        """O nível do aluno com as turmas em dia, como o app faz quando alguém entra."""
        self.atualizar.executar()
        return self.niveis.nivel_do_aluno(aluno.id, materia.id)

    def resumo(self, turma: Turma) -> ResumoDaTurma:
        return next(resumo for resumo in self.ver_turmas.executar(ADM) if resumo.id == turma.id)

    def como_o_aluno_ve(self, aluno: Usuario, turma: Turma) -> TurmaDoAluno:
        return next(
            vista
            for vista in self.ver_turmas_do_aluno.executar(aluno)
            if vista.resumo.id == turma.id
        )

    def esta_na_turma(self, aluno: Usuario, turma: Turma) -> bool:
        return any(
            vista.resumo.id == turma.id and vista.situacao == SituacaoNaTurma.MATRICULADO
            for vista in self.ver_turmas_do_aluno.executar(aluno)
        )

    def na_prova_final(self, turma: Turma, aluno: Usuario, nivel: int = 2) -> AlunoNaProvaFinal:
        prova_final = self.ver_prova_final.executar(ADM, turma.id, nivel)
        return next(na_prova for na_prova in prova_final.alunos if na_prova.aluno_id == aluno.id)

    def nota(self, turma: Turma, aluno: Usuario, nivel: int = 2) -> str | None:
        prova = self.na_prova_final(turma, aluno, nivel).prova
        return None if prova is None else str(prova.nota)

    def certificados(
        self, aluno: Usuario
    ) -> list[tuple[str, TipoDeCertificado, int, datetime]]:
        """Os certificados do aluno com as turmas em dia, como o app faz ao abrir a aba."""
        self.atualizar.executar()
        return [
            (c.nome_da_materia, c.tipo, c.nivel, c.emitido_em)
            for c in self.ver_meus_certificados.executar(aluno)
        ]


@pytest.fixture
def escola(
    conexao: sqlite3.Connection, em_transacao: Transacao, relogio: RelogioDeTeste
) -> Escola:
    usuarios = RepositorioDeUsuariosSqlite(conexao)
    repositorio_de_professores = RepositorioDeProfessoresSqlite(conexao)
    professores = ConsultaDeProfessores(repositorio_de_professores)
    materias = ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao))
    nivelamentos = RepositorioDeNivelamentosSqlite(conexao)
    promocoes = Promocoes(nivelamentos, materias)
    niveis = ConsultaDeNiveis(nivelamentos)
    alunos = ConsultaDeAlunos(usuarios)
    turmas = RepositorioDeTurmasSqlite(conexao)
    em_dia = TurmasEmDia(turmas, materias, promocoes)
    leitura = (turmas, materias, professores, relogio, em_transacao, em_dia)
    do_aluno = (turmas, materias, professores, niveis, relogio, em_transacao, em_dia)
    das_aulas = (turmas, materias, professores, alunos, relogio, em_transacao, em_dia)
    return Escola(
        conexao=conexao,
        relogio=relogio,
        cadastrar_aluno=CadastrarAluno(usuarios, em_transacao),
        cadastrar_professor=CadastrarProfessor(usuarios, em_transacao),
        habilitar_professor=HabilitarProfessor(repositorio_de_professores, materias, em_transacao),
        criar_turma=CriarTurma(turmas, materias, professores, relogio, em_transacao, em_dia),
        ver_turmas=VerTurmas(*leitura),
        ver_minhas_turmas=VerMinhasTurmas(*leitura),
        encerrar_turma=EncerrarTurma(turmas, materias, relogio, em_transacao, em_dia),
        atualizar=AtualizarTurmas(em_dia, relogio, em_transacao),
        matricular=Matricular(*do_aluno),
        sair_da_turma=SairDaTurma(*do_aluno),
        entrar_na_lista=EntrarNaListaDeEspera(*do_aluno),
        ver_turmas_do_aluno=VerTurmasDoAluno(*do_aluno),
        ver_aulas=VerAulasDaTurma(*das_aulas),
        lancar_presenca=LancarPresenca(*das_aulas),
        corrigir_presenca=CorrigirPresenca(*das_aulas),
        marcar_nao_realizada=MarcarAulaNaoRealizada(*das_aulas),
        ver_prova_final=VerProvaFinal(*das_aulas),
        lancar_nota=LancarNota(*das_aulas),
        corrigir_nota=CorrigirNota(*das_aulas),
        ver_meus_niveis=VerMeusNiveis(
            nivelamentos, RepositorioDeQuestoesSqlite(conexao), materias
        ),
        ver_meus_certificados=VerMeusCertificados(nivelamentos, materias),
        niveis=niveis,
        promocoes=promocoes,
        turmas=turmas,
    )


@pytest.fixture
def fisica(escola: Escola, em_transacao: Transacao) -> Materia:
    repositorio = RepositorioDeMateriasSqlite(escola.conexao)
    return CadastrarMateria(repositorio, em_transacao).executar(ADM, "Física", 3, [40, 70], 20000)


@pytest.fixture
def carlos(escola: Escola, fisica: Materia) -> Usuario:
    return escola.professor("carlos@exemplo.com", fisica)


@dataclass(frozen=True)
class TurmaDoCarlos:
    """Turma de Física do Carlos criada em 16/12/2026, com Ana e Bruno desde a 1ª aula e as
    mensalidades pagas, para não perderem a vaga por atraso (R28)."""

    turma: Turma
    ana: Usuario
    bruno: Usuario


def turma_com_ana_e_bruno(
    escola: Escola, fisica: Materia, carlos: Usuario, nivel: int
) -> TurmaDoCarlos:
    escola.ir_para(CRIACAO)
    turma = escola.turma(fisica, nivel, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica, nivel)
    bruno = escola.aluno("bruno@exemplo.com", fisica, nivel)
    escola.matricular.executar(ana, turma.id)
    escola.matricular.executar(bruno, turma.id)
    for aluno in (ana, bruno):
        pagar_mensalidades(escola.conexao, aluno.id, turma.id)
    return TurmaDoCarlos(turma, ana, bruno)


@pytest.fixture
def no_n2(escola: Escola, fisica: Materia, carlos: Usuario) -> TurmaDoCarlos:
    return turma_com_ana_e_bruno(escola, fisica, carlos, 2)


@pytest.fixture
def nota_6_da_ana(escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos) -> TurmaDoCarlos:
    """Carlos lançou nota 6 para Ana em 10/03 às 10h."""
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.ana.id, "6")
    return no_n2


# H10 e H20: a turma passa de nível, com o mesmo professor, e encerra no nível máximo.


def test_r04_r26_no_fim_da_etapa_do_n2_a_turma_passa_para_o_n3_com_o_mesmo_professor(
    escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(em(9, 3, 20, 29))
    assert escola.resumo(no_n2.turma).nivel == 2

    escola.ir_para(FIM_DA_ETAPA)

    resumo = escola.resumo(no_n2.turma)
    assert (resumo.nivel, resumo.professor_id, resumo.horario) == (
        3,
        carlos.id,
        no_n2.turma.horario,
    )
    assert (resumo.aulas_dadas, resumo.inicio_da_etapa) == (0, INICIO_DA_ETAPA_SEGUINTE)


def test_r26_carlos_ve_a_mesma_turma_agora_no_n3_nos_mesmos_dias_e_horario(
    escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(FIM_DA_ETAPA)

    [turma] = escola.ver_minhas_turmas.executar(carlos)

    assert (turma.id, turma.nivel, turma.horario) == (no_n2.turma.id, 3, no_n2.turma.horario)


def test_r04_ana_promovida_continua_matriculada_na_turma_sem_nova_matricula(
    escola: Escola, fisica: Materia, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    antes = escola.turmas.matriculas_do_aluno(no_n2.ana.id)
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.ana.id, "8")

    escola.ir_para(em(13, 3))

    assert escola.nivel(no_n2.ana, fisica) == 3
    assert escola.turmas.matriculas_do_aluno(no_n2.ana.id) == antes
    assert escola.como_o_aluno_ve(no_n2.ana, no_n2.turma).resumo.nivel == 3


def test_r09_a_turma_no_n3_o_nivel_maximo_encerra_no_fim_da_etapa(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    no_n3 = turma_com_ana_e_bruno(escola, fisica, carlos, 3)

    escola.ir_para(FIM_DA_ETAPA)

    resumo = escola.resumo(no_n3.turma)
    assert (resumo.nivel, resumo.encerrada_em) == (3, FIM_DA_ETAPA)


def test_r25_o_adm_nao_encerra_a_turma_do_n2(escola: Escola, no_n2: TurmaDoCarlos) -> None:
    with pytest.raises(
        TurmaAberta,
        match="A turma não pode ser encerrada: ela encerra sozinha no fim da etapa do N3, o "
        "nível máximo.",
    ):
        escola.encerrar_turma.executar(ADM, no_n2.turma.id)


def test_rnf07_so_o_adm_tenta_encerrar_a_turma(
    escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    with pytest.raises(AcessoNegado, match="Só o ADM pode encerrar turma."):
        escola.encerrar_turma.executar(carlos, no_n2.turma.id)


def test_r25_a_turma_com_um_unico_aluno_continua_aberta_com_12_vagas_quando_ele_sai(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    escola.ir_para(CRIACAO)
    turma = escola.turma(fisica, 2, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica, 2)
    escola.matricular.executar(ana, turma.id)

    escola.sair_da_turma.executar(ana, turma.id)

    resumo = escola.resumo(turma)
    assert (resumo.encerrada_em, resumo.vagas_livres) == (None, 12)


def test_r09_a_turma_encerrada_nao_aparece_para_o_aluno_do_n3_nem_aceita_matricula(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    no_n3 = turma_com_ana_e_bruno(escola, fisica, carlos, 3)
    carla = escola.aluno("carla@exemplo.com", fisica, 3)
    escola.ir_para(NOTA_EM_10_03_AS_10H)

    assert escola.ver_turmas_do_aluno.executar(carla) == []
    with pytest.raises(TurmaEncerrada, match="Esta turma foi encerrada"):
        escola.matricular.executar(carla, no_n3.turma.id)


def test_r07_a_turma_encerrada_nao_ocupa_mais_o_horario_de_carlos(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    no_n3 = turma_com_ana_e_bruno(escola, fisica, carlos, 3)
    escola.ir_para(NOTA_EM_10_03_AS_10H)

    nova = escola.turma(fisica, 1, carlos)

    assert nova.horario == no_n3.turma.horario


def test_r48_a_aula_da_etapa_que_terminou_nao_e_marcada_como_nao_realizada(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    no_n3 = turma_com_ana_e_bruno(escola, fisica, carlos, 3)
    escola.ir_para(NOTA_EM_10_03_AS_10H)

    with pytest.raises(
        EtapaTerminada, match="A etapa do N3 terminou em 09/03/2027, às 20h30"
    ):
        escola.marcar_nao_realizada.executar(carlos, no_n3.turma.id, date(2027, 3, 9))


# H23: a nota da prova final é lançada depois da 24ª aula.


def test_r20_carlos_lanca_nota_8_para_ana_em_10_03_as_10h_e_ela_fica_registrada(
    escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)

    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.ana.id, "8")

    prova = escola.na_prova_final(no_n2.turma, no_n2.ana).prova
    assert prova is not None
    assert (str(prova.nota), prova.lancada_em) == ("8", NOTA_EM_10_03_AS_10H)


def test_r17_com_20_aulas_dadas_a_nota_da_prova_final_e_recusada(
    escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    # A 20ª aula foi na terça 23/02/2027.
    escola.ir_para(em(24, 2))

    with pytest.raises(
        EtapaNaoTerminou,
        match="A nota da prova final só é lançada no fim da etapa, depois da 24ª aula: em "
        "09/03/2027, às 20h30.",
    ):
        escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.ana.id, "8")


def test_r10_dora_nao_lanca_nota_na_turma_do_carlos(
    escola: Escola, fisica: Materia, no_n2: TurmaDoCarlos
) -> None:
    dora = escola.professor("dora@exemplo.com", fisica)
    escola.ir_para(NOTA_EM_10_03_AS_10H)

    with pytest.raises(AcessoNegado, match="Esta turma é de outro professor."):
        escola.lancar_nota.executar(dora, no_n2.turma.id, 2, no_n2.ana.id, "8")


def test_rnf07_o_aluno_nao_lanca_a_nota(escola: Escola, no_n2: TurmaDoCarlos) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)

    with pytest.raises(
        AcessoNegado, match="Só o professor da turma ou o ADM pode lançar a nota da prova final."
    ):
        escola.lancar_nota.executar(no_n2.ana, no_n2.turma.id, 2, no_n2.ana.id, "10")


def test_r23_sem_nota_ana_continua_na_turma_no_n3_ocupando_a_vaga_com_o_resultado_pendente(
    escola: Escola, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)

    resumo = escola.resumo(no_n2.turma)

    assert (resumo.nivel, resumo.vagas_livres) == (3, 10)
    assert escola.esta_na_turma(no_n2.ana, no_n2.turma)
    assert escola.na_prova_final(no_n2.turma, no_n2.ana).resultado == ResultadoEtapa.PENDENTE


def test_r49_a_nota_8_lancada_em_10_03_as_10h_promove_ana_para_o_n3_em_13_03_as_10h(
    escola: Escola, fisica: Materia, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.ana.id, "8")
    escola.ir_para(em(13, 3, 9, 59))
    assert escola.nivel(no_n2.ana, fisica) == 2

    escola.ir_para(em(13, 3))

    assert escola.nivel(no_n2.ana, fisica) == 3
    assert escola.promocoes.promocoes(no_n2.ana.id) == [Promocao(fisica.id, 2, 3, em(13, 3))]


def test_a_nota_de_ana_na_etapa_e_lancada_uma_vez(
    escola: Escola, carlos: Usuario, nota_6_da_ana: TurmaDoCarlos
) -> None:
    situacao = nota_6_da_ana

    with pytest.raises(NotaJaLancada, match="A nota de ana@exemplo.com já foi lançada."):
        escola.lancar_nota.executar(carlos, situacao.turma.id, 2, situacao.ana.id, "7")


def test_quem_entrou_na_etapa_do_n3_nao_tem_nota_na_etapa_do_n2(
    escola: Escola, fisica: Materia, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    carla = escola.aluno("carla@exemplo.com", fisica, 3)
    escola.matricular.executar(carla, no_n2.turma.id)

    with pytest.raises(AlunoForaDaEtapa):
        escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, carla.id, "8")


def test_o_aluno_ve_a_nota_e_quando_vale_o_resultado_da_etapa_que_terminou(
    escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.ana.id, "8")

    vista = escola.como_o_aluno_ve(no_n2.ana, no_n2.turma)

    assert vista.prova_final is not None
    assert (vista.prova_final.nivel, vista.prova_final.resultado) == (2, ResultadoEtapa.APROVADO)
    assert vista.prova_final.prova is not None
    assert vista.prova_final.prova.vale_em == em(13, 3)


# H09: o resultado da etapa (R08) e a promoção.


def test_r08_ana_com_6_faltas_e_nota_7_e_promovida_para_o_n3(
    escola: Escola, fisica: Materia, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(DURANTE_A_24A_AULA)
    escola.lancar_a_etapa(carlos, no_n2.turma, {no_n2.ana: {1, 4, 8, 12, 16, 20}})
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.ana.id, "7")
    na_prova = escola.na_prova_final(no_n2.turma, no_n2.ana)
    assert (na_prova.faltas, na_prova.resultado) == (6, ResultadoEtapa.APROVADO)

    escola.ir_para(em(13, 3))

    assert escola.nivel(no_n2.ana, fisica) == 3


def test_r08_bruno_com_2_faltas_e_nota_6_5_e_reprovado_e_continua_no_n2(
    escola: Escola, fisica: Materia, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(DURANTE_A_24A_AULA)
    escola.lancar_a_etapa(carlos, no_n2.turma, {no_n2.bruno: {3, 9}})
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.bruno.id, "6,5")
    na_prova = escola.na_prova_final(no_n2.turma, no_n2.bruno)
    assert (na_prova.faltas, na_prova.resultado) == (2, ResultadoEtapa.REPROVADO)

    escola.ir_para(em(13, 3))

    assert escola.nivel(no_n2.bruno, fisica) == 2


def test_r08_bruno_com_7_faltas_e_nota_9_e_reprovado_e_continua_no_n2(
    escola: Escola, fisica: Materia, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(DURANTE_A_24A_AULA)
    escola.lancar_a_etapa(carlos, no_n2.turma, {no_n2.bruno: {2, 5, 8, 11, 14, 17, 23}})
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.bruno.id, "9")
    na_prova = escola.na_prova_final(no_n2.turma, no_n2.bruno)
    assert (na_prova.faltas, na_prova.resultado) == (7, ResultadoEtapa.REPROVADO)

    escola.ir_para(em(13, 3))

    assert escola.nivel(no_n2.bruno, fisica) == 2


def test_r09_ana_no_n1_sem_faltas_e_com_nota_10_sobe_para_o_n2_e_nao_para_o_n3(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    no_n1 = turma_com_ana_e_bruno(escola, fisica, carlos, 1)
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n1.turma.id, 1, no_n1.ana.id, "10")

    escola.ir_para(em(13, 3))

    assert escola.nivel(no_n1.ana, fisica) == 2


def test_r09_ana_aprovada_no_n3_o_nivel_maximo_continua_nele_e_conclui_a_trilha(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    no_n3 = turma_com_ana_e_bruno(escola, fisica, carlos, 3)
    escola.ir_para(DURANTE_A_24A_AULA)
    escola.lancar_a_etapa(carlos, no_n3.turma, {no_n3.ana: {2, 5, 7}})
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n3.turma.id, 3, no_n3.ana.id, "8")

    escola.ir_para(em(13, 3))

    assert escola.nivel(no_n3.ana, fisica) == 3
    [fisica_da_ana] = escola.ver_meus_niveis.executar(no_n3.ana)
    assert fisica_da_ana.trilha_concluida
    # A turma encerrou: quem concluiu a trilha sai dela.
    assert not escola.esta_na_turma(no_n3.ana, no_n3.turma)


# H11: o reprovado fica na turma durante as 72 horas e depois procura outra turma do nível.


def test_r23_bruno_reprovado_com_nota_5_continua_na_turma_ocupando_a_vaga_em_12_03(
    escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.bruno.id, "5")

    escola.ir_para(em(12, 3))

    assert escola.esta_na_turma(no_n2.bruno, no_n2.turma)
    assert escola.resumo(no_n2.turma).vagas_livres == 10


def test_r21_sem_correcao_bruno_sai_da_turma_em_13_03_as_10h01_e_continua_no_n2(
    escola: Escola, fisica: Materia, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.bruno.id, "5")

    escola.ir_para(em(13, 3, 10, 1))

    assert not escola.esta_na_turma(no_n2.bruno, no_n2.turma)
    assert escola.nivel(no_n2.bruno, fisica) == 2
    assert escola.resumo(no_n2.turma).vagas_livres == 11


def test_r19_r21_bruno_reprovado_entra_noutra_turma_do_n2_que_ja_deu_8_aulas(
    escola: Escola, fisica: Materia, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    # A outra turma, de segunda e quarta, tem a 1ª aula na segunda 15/02/2027. A 8ª é na quarta
    # 10/03, e a 9ª, na segunda 15/03.
    escola.ir_para(em(11, 2, 14))
    dora = escola.professor("dora@exemplo.com", fisica)
    outra = escola.turma(fisica, 2, dora, SEG_E_QUA)
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.bruno.id, "5")
    escola.ir_para(em(13, 3, 10, 1))

    feita = escola.matricular.executar(no_n2.bruno, outra.id)

    assert feita.aula_de_entrada == 9


def test_r50_no_fim_da_etapa_bruno_sai_da_lista_e_a_turma_comeca_o_n3_com_a_lista_vazia(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    escola.ir_para(CRIACAO)
    turma = escola.turma(fisica, 2, carlos)
    for numero in range(1, 13):
        aluno = escola.aluno(f"aluno{numero}@exemplo.com", fisica, 2)
        escola.matricular.executar(aluno, turma.id)
        pagar_mensalidades(escola.conexao, aluno.id, turma.id)
    bruno = escola.aluno("bruno@exemplo.com", fisica, 2)
    escola.entrar_na_lista.executar(bruno, turma.id)
    escola.ir_para(em(9, 3, 20, 29))
    escola.atualizar.executar()
    assert [na_lista.aluno_id for na_lista in escola.turmas.lista_de_espera(turma.id)] == [
        bruno.id
    ]

    escola.ir_para(FIM_DA_ETAPA)
    escola.atualizar.executar()

    assert escola.turmas.lista_de_espera(turma.id) == ()
    assert escola.resumo(turma).nivel == 3


# H24: o professor corrige até 72 horas depois do lançamento (R22).


def test_r22_carlos_corrige_a_nota_de_ana_de_6_para_7_em_13_03_as_9h59(
    escola: Escola, carlos: Usuario, nota_6_da_ana: TurmaDoCarlos
) -> None:
    situacao = nota_6_da_ana
    escola.ir_para(em(13, 3, 9, 59))

    escola.corrigir_nota.executar(carlos, situacao.turma.id, 2, situacao.ana.id, "7")

    assert escola.nota(situacao.turma, situacao.ana) == "7"


def test_r22_em_13_03_as_10h01_carlos_nao_corrige_a_nota_e_so_o_adm_pode(
    escola: Escola, carlos: Usuario, nota_6_da_ana: TurmaDoCarlos
) -> None:
    situacao = nota_6_da_ana
    escola.ir_para(em(13, 3, 10, 1))

    with pytest.raises(PrazoDeCorrecaoVencido, match="agora só o ADM pode corrigir."):
        escola.corrigir_nota.executar(carlos, situacao.turma.id, 2, situacao.ana.id, "7")

    assert escola.nota(situacao.turma, situacao.ana) == "6"


def test_r22_a_falta_de_bruno_lancada_em_01_03_as_20h30_nao_e_corrigida_por_carlos_em_05_03(
    escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(em(1, 3, 20, 30))
    escola.lancar(carlos, no_n2.turma, 5, ausentes=[no_n2.bruno])
    quinta_aula = escola.data_da_aula(no_n2.turma, 5, 2)
    escola.ir_para(em(5, 3))

    with pytest.raises(PrazoDeCorrecaoVencido, match="agora só o ADM pode corrigir."):
        escola.corrigir_presenca.executar(carlos, no_n2.turma.id, quinta_aula, set())

    assert escola.como_o_aluno_ve(no_n2.bruno, no_n2.turma).faltas == 1


def test_r22_carlos_corrige_a_falta_de_bruno_dentro_das_72_horas(
    escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(em(1, 3, 20, 30))
    escola.lancar(carlos, no_n2.turma, 5, ausentes=[no_n2.bruno])
    quinta_aula = escola.data_da_aula(no_n2.turma, 5, 2)
    escola.ir_para(em(4, 3, 20, 29))

    escola.corrigir_presenca.executar(carlos, no_n2.turma.id, quinta_aula, {no_n2.ana.id})

    assert escola.como_o_aluno_ve(no_n2.bruno, no_n2.turma).faltas == 0
    assert escola.como_o_aluno_ve(no_n2.ana, no_n2.turma).faltas == 1
    aula = next(
        aula
        for aula in escola.ver_aulas.executar(carlos, no_n2.turma.id).aulas
        if aula.numero == 5
    )
    assert aula.situacao == SituacaoDaAula.COM_PRESENCA
    assert {aluno.email: aluno.presente for aluno in aula.alunos} == {
        "ana@exemplo.com": False,
        "bruno@exemplo.com": True,
    }


def test_r22_r49_carlos_corrige_a_nota_de_ana_de_7_para_6_em_11_03_e_ela_fica_reprovada(
    escola: Escola, fisica: Materia, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.ana.id, "7")
    escola.ir_para(em(11, 3))

    escola.corrigir_nota.executar(carlos, no_n2.turma.id, 2, no_n2.ana.id, "6")

    assert escola.na_prova_final(no_n2.turma, no_n2.ana).resultado == ResultadoEtapa.REPROVADO
    escola.ir_para(em(13, 3))
    assert escola.nivel(no_n2.ana, fisica) == 2
    assert not escola.esta_na_turma(no_n2.ana, no_n2.turma)


def test_r51_carlos_nao_corrige_a_nota_de_ana_para_6_75(
    escola: Escola, carlos: Usuario, nota_6_da_ana: TurmaDoCarlos
) -> None:
    situacao = nota_6_da_ana
    escola.ir_para(em(11, 3))

    with pytest.raises(NotaInvalida, match="A nota vai de 0 a 10, com uma casa decimal, como 6,5."):
        escola.corrigir_nota.executar(carlos, situacao.turma.id, 2, situacao.ana.id, "6,75")


# H32: o ADM lança e corrige em qualquer turma, e depois das 72 horas o nível só sobe (R22).


def test_r23_dez_dias_depois_do_fim_da_etapa_o_adm_lanca_nota_8_para_ana(
    escola: Escola, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(em(19, 3, 20, 30))

    escola.lancar_nota.executar(ADM, no_n2.turma.id, 2, no_n2.ana.id, "8")

    assert escola.nota(no_n2.turma, no_n2.ana) == "8"


def test_r22_r52_o_adm_corrige_para_7_e_ana_que_saiu_reprovada_sobe_sem_voltar_para_a_turma(
    escola: Escola, fisica: Materia, nota_6_da_ana: TurmaDoCarlos
) -> None:
    situacao = nota_6_da_ana
    escola.ir_para(em(13, 3, 10, 1))
    assert not escola.esta_na_turma(situacao.ana, situacao.turma)
    escola.ir_para(em(20, 3))

    escola.corrigir_nota.executar(ADM, situacao.turma.id, 2, situacao.ana.id, "7")

    assert escola.nivel(situacao.ana, fisica) == 3
    assert not escola.esta_na_turma(situacao.ana, situacao.turma)
    assert escola.promocoes.promocoes(situacao.ana.id) == [Promocao(fisica.id, 2, 3, em(20, 3))]


def test_r22_o_adm_corrige_para_5_a_nota_de_ana_ja_promovida_e_ela_continua_no_n3(
    escola: Escola, fisica: Materia, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.ana.id, "8")
    escola.ir_para(em(20, 3))

    escola.corrigir_nota.executar(ADM, no_n2.turma.id, 2, no_n2.ana.id, "5")

    assert escola.nota(no_n2.turma, no_n2.ana) == "5"
    assert escola.nivel(no_n2.ana, fisica) == 3


def test_r22_a_correcao_de_presenca_do_adm_que_deixa_bruno_com_6_faltas_o_promove(
    escola: Escola, fisica: Materia, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(DURANTE_A_24A_AULA)
    escola.lancar_a_etapa(carlos, no_n2.turma, {no_n2.bruno: {1, 2, 3, 4, 5, 6, 7}})
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.bruno.id, "9")
    escola.ir_para(em(20, 3))
    assert escola.nivel(no_n2.bruno, fisica) == 2

    setima_aula = escola.data_da_aula(no_n2.turma, 7, 2)
    escola.corrigir_presenca.executar(ADM, no_n2.turma.id, setima_aula, set())

    assert escola.nivel(no_n2.bruno, fisica) == 3


# As aulas da etapa que terminou continuam com o professor.


def test_o_professor_lanca_a_presenca_da_24a_aula_depois_que_a_turma_passou_para_o_n3(
    escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)

    escola.lancar(carlos, no_n2.turma, 24, ausentes=[no_n2.ana])

    aulas = escola.ver_aulas.executar(carlos, no_n2.turma.id, nivel=2)
    assert aulas.aulas[-1].situacao == SituacaoDaAula.COM_PRESENCA
    assert escola.na_prova_final(no_n2.turma, no_n2.ana).faltas == 1


def test_o_professor_ve_as_etapas_da_turma_e_as_aulas_da_etapa_do_n2_que_terminou(
    escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)

    atual = escola.ver_aulas.executar(carlos, no_n2.turma.id)
    do_n2 = escola.ver_aulas.executar(carlos, no_n2.turma.id, nivel=2)

    assert [(etapa.nivel, etapa.atual) for etapa in atual.etapas] == [(2, False), (3, True)]
    assert (atual.nivel, atual.em_andamento) == (3, True)
    assert (do_n2.nivel, do_n2.em_andamento) == (2, False)
    assert (do_n2.aulas[-1].numero, do_n2.aulas[-1].data) == (24, date(2027, 3, 9))


def test_rnf05_erro_ao_promover_nao_deixa_os_resultados_pela_metade(
    escola: Escola, fisica: Materia, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    # A nota de Bruno vale às 9h de 13/03, e a de Ana, às 10h: Bruno sai antes de Ana subir.
    escola.ir_para(em(10, 3, 9))
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.bruno.id, "5")
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.ana.id, "8")
    escola.conexao.execute(
        "CREATE TRIGGER falha_na_promocao BEFORE INSERT ON promocao "
        "BEGIN SELECT RAISE(ABORT, 'falha forçada no teste'); END"
    )
    escola.ir_para(em(13, 3))

    with pytest.raises(sqlite3.DatabaseError, match="falha forçada no teste"):
        escola.atualizar.executar()

    assert escola.niveis.nivel_do_aluno(no_n2.ana.id, fisica.id) == 2
    assert [m.aluno_id for m in escola.turmas.matriculas_da_turma(no_n2.turma.id)] == [
        no_n2.ana.id,
        no_n2.bruno.id,
    ]
    provas = escola.turmas.provas_finais(no_n2.turma.id, 2)
    assert [prova.resultado_aplicado for prova in provas] == [None, None]


# H12: os certificados de nível e de trilha.


def test_r33_ana_promovida_do_n1_para_o_n2_recebe_o_certificado_de_nivel_do_n1(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    no_n1 = turma_com_ana_e_bruno(escola, fisica, carlos, 1)
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n1.turma.id, 1, no_n1.ana.id, "8")

    escola.ir_para(em(13, 3))

    assert escola.certificados(no_n1.ana) == [
        ("Física", TipoDeCertificado.NIVEL, 1, em(13, 3))
    ]


def test_r36_ana_aprovada_no_n3_recebe_o_certificado_de_nivel_do_n3_e_o_de_trilha(
    escola: Escola, fisica: Materia, carlos: Usuario
) -> None:
    no_n3 = turma_com_ana_e_bruno(escola, fisica, carlos, 3)
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n3.turma.id, 3, no_n3.ana.id, "8")

    escola.ir_para(em(13, 3))

    assert escola.certificados(no_n3.ana) == [
        ("Física", TipoDeCertificado.NIVEL, 3, em(13, 3)),
        ("Física", TipoDeCertificado.TRILHA, 3, em(13, 3)),
    ]


def test_r33_bruno_reprovado_no_n2_nao_recebe_certificado(
    escola: Escola, carlos: Usuario, no_n2: TurmaDoCarlos
) -> None:
    escola.ir_para(NOTA_EM_10_03_AS_10H)
    escola.lancar_nota.executar(carlos, no_n2.turma.id, 2, no_n2.bruno.id, "5")

    escola.ir_para(em(13, 3))

    assert escola.certificados(no_n2.bruno) == []


def test_r33_quem_ficou_no_n3_pelo_nivelamento_nao_tem_certificado_do_n1_nem_do_n2(
    escola: Escola, fisica: Materia
) -> None:
    carla = escola.aluno("carla@exemplo.com", fisica, 3)

    assert escola.certificados(carla) == []


def test_r22_r33_a_promocao_pela_correcao_do_adm_tambem_da_o_certificado(
    escola: Escola, nota_6_da_ana: TurmaDoCarlos
) -> None:
    situacao = nota_6_da_ana
    escola.ir_para(em(20, 3))

    escola.corrigir_nota.executar(ADM, situacao.turma.id, 2, situacao.ana.id, "7")

    assert escola.certificados(situacao.ana) == [
        ("Física", TipoDeCertificado.NIVEL, 2, em(20, 3))
    ]


def test_rnf07_so_o_aluno_ve_os_proprios_certificados(escola: Escola, carlos: Usuario) -> None:
    with pytest.raises(AcessoNegado, match="Só o aluno pode ver os próprios certificados."):
        escola.ver_meus_certificados.executar(carlos)


def test_rnf16_a_turma_criada_antes_da_migracao_0010_continua_na_etapa_que_tinha(
    tmp_path: Path,
) -> None:
    ate_a_0009 = tmp_path / "ate_a_0009"
    ate_a_0009.mkdir()
    for migracao in PASTA_MIGRACOES.glob("*.sql"):
        if int(migracao.name.split("_", 1)[0]) <= 9:
            shutil.copy(migracao, ate_a_0009 / migracao.name)
    caminho_banco = tmp_path / "plataforma.db"
    aplicar_migracoes(caminho_banco, ate_a_0009, tmp_path / "copias")
    with closing(sqlite3.connect(caminho_banco)) as conexao:
        conexao.execute(
            "INSERT INTO turma (materia_id, nivel, professor_id, primeiro_dia, segundo_dia, "
            "inicio, fim, inicio_da_etapa) VALUES (1, 2, 10, 1, 3, '19:00', '20:30', "
            "'2026-11-24T19:00:00-03:00')"
        )
        conexao.commit()

    aplicar_migracoes(caminho_banco, PASTA_MIGRACOES, tmp_path / "copias")

    with closing(conectar(caminho_banco)) as conexao:
        [turma] = RepositorioDeTurmasSqlite(conexao).listar()
    assert (turma.nivel, turma.inicio_da_etapa, turma.encerrada_em) == (
        2,
        em(24, 11, 19, ano=2026),
        None,
    )
