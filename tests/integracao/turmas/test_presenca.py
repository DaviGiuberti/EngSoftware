"""Presença, aula não realizada e faltas com o banco SQLite e um relógio de teste (H21, H22,
H08). R08, R10, R17, R18, R19, R43, R48 e RNF07."""

import sqlite3
from collections.abc import Collection
from dataclasses import dataclass
from datetime import date, datetime, time

import pytest

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
from plataforma.modules.nivelamento.application.consulta_de_niveis import ConsultaDeNiveis
from plataforma.modules.nivelamento.domain.nivelamento import NivelDoAluno
from plataforma.modules.nivelamento.infra.repositorio_de_nivelamentos import (
    RepositorioDeNivelamentosSqlite,
)
from plataforma.modules.turmas.application.casos_de_uso import CriarTurma
from plataforma.modules.turmas.application.matricula import (
    Matricular,
    TurmaDoAluno,
    VerTurmasDoAluno,
)
from plataforma.modules.turmas.application.presenca import (
    AulasDaTurma,
    LancarPresenca,
    MarcarAulaNaoRealizada,
    SituacaoDaAula,
    VerAulasDaTurma,
)
from plataforma.modules.turmas.domain.etapa import AulaComPresenca
from plataforma.modules.turmas.domain.horario import DiaDaSemana
from plataforma.modules.turmas.domain.presenca import (
    AulaAindaNaoComecou,
    PresencaEmAulaNaoRealizada,
    PresencaJaLancada,
)
from plataforma.modules.turmas.domain.turma import Turma
from plataforma.modules.turmas.infra.repositorio_de_turmas import RepositorioDeTurmasSqlite
from tests.integracao.conftest import RelogioDeTeste

ADM = Usuario(id=1000, email="adm@exemplo.com", perfil=Perfil.ADM)
TER_E_QUI = (DiaDaSemana.TERCA, DiaDaSemana.QUINTA)


def em(dia: int, mes: int, ano: int, hora: int = 14, minuto: int = 0) -> datetime:
    return datetime(ano, mes, dia, hora, minuto, tzinfo=BRASILIA)


@dataclass(frozen=True)
class Escola:
    """Os casos de uso e o que os testes precisam para montar a situação de cada critério."""

    conexao: sqlite3.Connection
    relogio: RelogioDeTeste
    cadastrar_aluno: CadastrarAluno
    cadastrar_professor: CadastrarProfessor
    habilitar_professor: HabilitarProfessor
    criar_turma: CriarTurma
    matricular: Matricular
    ver_turmas_do_aluno: VerTurmasDoAluno
    lancar_presenca: LancarPresenca
    marcar_nao_realizada: MarcarAulaNaoRealizada
    ver_aulas: VerAulasDaTurma
    turmas: RepositorioDeTurmasSqlite

    def ir_para(self, momento: datetime) -> None:
        self.relogio.avancar(seconds=(momento - self.relogio.agora()).total_seconds())

    def aluno(self, email: str, materia: Materia, nivel: int = 2) -> Usuario:
        aluno = self.cadastrar_aluno.executar(email, "abcd1234")
        RepositorioDeNivelamentosSqlite(self.conexao).salvar_nivel(
            aluno.id, NivelDoAluno(materia.id, nivel)
        )
        return aluno

    def professor(self, email: str, materia: Materia) -> Usuario:
        professor = self.cadastrar_professor.executar(ADM, email, "abcd1234")
        self.habilitar_professor.executar(ADM, professor.id, materia.id)
        return professor

    def turma(self, materia: Materia, professor: Usuario) -> Turma:
        return self.criar_turma.executar(
            ADM, materia.id, 2, professor.id, TER_E_QUI, time(19), time(20, 30)
        )

    def data_da_aula(self, turma: Turma, numero: int) -> date:
        """A data da aula de número dado, com as não realizadas que a turma tiver agora."""
        atual = self.turmas.buscar(turma.id)
        assert atual is not None
        return next(aula.data for aula in atual.calendario() if aula.numero == numero)

    def lancar(
        self, quem: Usuario, turma: Turma, numero: int, ausentes: Collection[Usuario] = ()
    ) -> None:
        self.lancar_presenca.executar(
            quem, turma.id, self.data_da_aula(turma, numero), {a.id for a in ausentes}
        )

    def como_o_aluno_ve(self, aluno: Usuario, turma: Turma) -> TurmaDoAluno:
        return next(
            vista
            for vista in self.ver_turmas_do_aluno.executar(aluno)
            if vista.resumo.id == turma.id
        )


@pytest.fixture
def escola(
    conexao: sqlite3.Connection, em_transacao: Transacao, relogio: RelogioDeTeste
) -> Escola:
    usuarios = RepositorioDeUsuariosSqlite(conexao)
    repositorio_de_professores = RepositorioDeProfessoresSqlite(conexao)
    professores = ConsultaDeProfessores(repositorio_de_professores)
    materias = ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao))
    niveis = ConsultaDeNiveis(RepositorioDeNivelamentosSqlite(conexao))
    alunos = ConsultaDeAlunos(usuarios)
    turmas = RepositorioDeTurmasSqlite(conexao)
    do_aluno = (turmas, materias, professores, niveis, relogio, em_transacao)
    das_aulas = (turmas, materias, professores, alunos, relogio, em_transacao)
    return Escola(
        conexao=conexao,
        relogio=relogio,
        cadastrar_aluno=CadastrarAluno(usuarios, em_transacao),
        cadastrar_professor=CadastrarProfessor(usuarios, em_transacao),
        habilitar_professor=HabilitarProfessor(repositorio_de_professores, materias, em_transacao),
        criar_turma=CriarTurma(turmas, materias, professores, relogio, em_transacao),
        matricular=Matricular(*do_aluno),
        ver_turmas_do_aluno=VerTurmasDoAluno(*do_aluno),
        lancar_presenca=LancarPresenca(*das_aulas),
        marcar_nao_realizada=MarcarAulaNaoRealizada(*das_aulas),
        ver_aulas=VerAulasDaTurma(*das_aulas),
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
    """Turma de Física do Carlos, criada na segunda 23/11/2026, com Ana e Bruno desde o início.
    A 1ª aula é na terça 24/11, e a 5ª, na terça 08/12, às 19h."""

    turma: Turma
    ana: Usuario
    bruno: Usuario


@pytest.fixture
def turma_do_carlos(escola: Escola, fisica: Materia, carlos: Usuario) -> TurmaDoCarlos:
    turma = escola.turma(fisica, carlos)
    ana = escola.aluno("ana@exemplo.com", fisica)
    bruno = escola.aluno("bruno@exemplo.com", fisica)
    escola.matricular.executar(ana, turma.id)
    escola.matricular.executar(bruno, turma.id)
    return TurmaDoCarlos(turma, ana, bruno)


def presencas_da_aula(aulas: AulasDaTurma, numero: int) -> dict[str, bool | None]:
    aula = next(aula for aula in aulas.aulas if aula.numero == numero)
    return {aluno.email: aluno.presente for aluno in aula.alunos}


def test_r10_carlos_lanca_a_5a_aula_com_ana_presente_e_bruno_ausente(
    escola: Escola, carlos: Usuario, turma_do_carlos: TurmaDoCarlos
) -> None:
    situacao = turma_do_carlos
    escola.ir_para(em(8, 12, 2026, 21))

    escola.lancar(carlos, situacao.turma, 5, ausentes=[situacao.bruno])

    aulas = escola.ver_aulas.executar(carlos, situacao.turma.id)
    assert presencas_da_aula(aulas, 5) == {"ana@exemplo.com": True, "bruno@exemplo.com": False}
    assert escola.como_o_aluno_ve(situacao.bruno, situacao.turma).faltas == 1
    assert escola.como_o_aluno_ve(situacao.ana, situacao.turma).faltas == 0


def test_r10_dora_nao_lanca_presenca_na_turma_do_carlos(
    escola: Escola, fisica: Materia, turma_do_carlos: TurmaDoCarlos
) -> None:
    dora = escola.professor("dora@exemplo.com", fisica)
    escola.ir_para(em(8, 12, 2026, 21))

    with pytest.raises(AcessoNegado, match="Esta turma é de outro professor."):
        escola.lancar(dora, turma_do_carlos.turma, 5)


def test_r10_o_adm_lanca_presenca_em_qualquer_turma(
    escola: Escola, turma_do_carlos: TurmaDoCarlos
) -> None:
    escola.ir_para(em(8, 12, 2026, 21))

    escola.lancar(ADM, turma_do_carlos.turma, 5, ausentes=[turma_do_carlos.ana])

    assert escola.como_o_aluno_ve(turma_do_carlos.ana, turma_do_carlos.turma).faltas == 1


def test_rnf07_o_aluno_nao_lanca_presenca(
    escola: Escola, turma_do_carlos: TurmaDoCarlos
) -> None:
    escola.ir_para(em(8, 12, 2026, 21))

    with pytest.raises(
        AcessoNegado, match="Só o professor da turma ou o ADM pode lançar presença."
    ):
        escola.lancar(turma_do_carlos.ana, turma_do_carlos.turma, 5)


def test_r43_a_aula_que_ainda_nao_comecou_nao_recebe_presenca(
    escola: Escola, carlos: Usuario, turma_do_carlos: TurmaDoCarlos
) -> None:
    escola.ir_para(em(8, 12, 2026, 18, 59))

    with pytest.raises(AulaAindaNaoComecou, match="A 5ª aula começa em 08/12/2026, às 19h"):
        escola.lancar(carlos, turma_do_carlos.turma, 5)


def test_a_presenca_de_uma_aula_e_lancada_uma_vez(
    escola: Escola, carlos: Usuario, turma_do_carlos: TurmaDoCarlos
) -> None:
    escola.ir_para(em(8, 12, 2026, 21))
    escola.lancar(carlos, turma_do_carlos.turma, 5)

    with pytest.raises(PresencaJaLancada, match="A presença da 5ª aula já foi lançada."):
        escola.lancar(carlos, turma_do_carlos.turma, 5, ausentes=[turma_do_carlos.ana])


@pytest.fixture
def turma_que_comeca_em_11_03(escola: Escola, fisica: Materia, carlos: Usuario) -> Turma:
    """Turma de terça e quinta criada na quarta 10/03/2027: a 1ª aula é na quinta 11/03, a 10ª,
    na terça 13/04, e a 24ª, na terça 01/06."""
    escola.ir_para(em(10, 3, 2027))
    return escola.turma(fisica, carlos)


def test_r17_r18_ja_deu_9_aulas_marca_13_04_e_a_proxima_continua_sendo_a_10a(
    escola: Escola, carlos: Usuario, turma_que_comeca_em_11_03: Turma
) -> None:
    turma = turma_que_comeca_em_11_03
    escola.ir_para(em(12, 4, 2027))

    escola.marcar_nao_realizada.executar(carlos, turma.id, date(2027, 4, 13))

    aulas = escola.ver_aulas.executar(carlos, turma.id)
    proxima = next(a for a in aulas.aulas if a.situacao == SituacaoDaAula.FUTURA)
    assert (proxima.numero, proxima.data) == (10, date(2027, 4, 15))
    assert aulas.resumo.aulas_dadas == 9
    escola.ir_para(em(13, 4, 2027, 20))
    assert escola.ver_aulas.executar(carlos, turma.id).resumo.aulas_dadas == 9


def test_r18_a_24a_aula_que_seria_numa_terca_passa_para_a_quinta_seguinte(
    escola: Escola, carlos: Usuario, turma_que_comeca_em_11_03: Turma
) -> None:
    turma = turma_que_comeca_em_11_03
    antes = escola.ver_aulas.executar(carlos, turma.id).aulas[-1]
    assert (antes.numero, antes.data) == (24, date(2027, 6, 1))

    escola.marcar_nao_realizada.executar(carlos, turma.id, date(2027, 4, 13))

    depois = escola.ver_aulas.executar(carlos, turma.id).aulas[-1]
    assert (depois.numero, depois.inicio) == (24, em(3, 6, 2027, 19))


def test_r18_a_aula_nao_realizada_nao_recebe_presenca(
    escola: Escola, carlos: Usuario, turma_que_comeca_em_11_03: Turma
) -> None:
    turma = turma_que_comeca_em_11_03
    escola.marcar_nao_realizada.executar(carlos, turma.id, date(2027, 4, 13))
    escola.ir_para(em(13, 4, 2027, 21))

    with pytest.raises(PresencaEmAulaNaoRealizada, match="A aula de 13/04/2027 não foi realizada"):
        escola.lancar_presenca.executar(carlos, turma.id, date(2027, 4, 13), set())

    aula = next(a for a in escola.ver_aulas.executar(carlos, turma.id).aulas if a.numero is None)
    assert aula.situacao == SituacaoDaAula.NAO_REALIZADA


def test_r48_a_5a_aula_com_presenca_lancada_nao_vira_nao_realizada(
    escola: Escola, carlos: Usuario, turma_do_carlos: TurmaDoCarlos
) -> None:
    escola.ir_para(em(8, 12, 2026, 21))
    escola.lancar(carlos, turma_do_carlos.turma, 5)

    with pytest.raises(AulaComPresenca, match="já tem presença lançada: ela aconteceu"):
        escola.marcar_nao_realizada.executar(
            carlos, turma_do_carlos.turma.id, date(2026, 12, 8)
        )


def test_r48_aula_que_ja_passou_sem_presenca_pode_ser_marcada(
    escola: Escola, carlos: Usuario, turma_do_carlos: TurmaDoCarlos
) -> None:
    turma = turma_do_carlos.turma
    escola.ir_para(em(25, 11, 2026))

    escola.marcar_nao_realizada.executar(carlos, turma.id, date(2026, 11, 24))

    assert escola.ver_aulas.executar(carlos, turma.id).resumo.aulas_dadas == 0


def test_rnf07_so_o_professor_da_turma_marca_aula_nao_realizada(
    escola: Escola, fisica: Materia, turma_do_carlos: TurmaDoCarlos
) -> None:
    dora = escola.professor("dora@exemplo.com", fisica)
    turma_id = turma_do_carlos.turma.id

    with pytest.raises(AcessoNegado, match="Esta turma é de outro professor."):
        escola.marcar_nao_realizada.executar(dora, turma_id, date(2026, 12, 8))
    with pytest.raises(
        AcessoNegado, match="Só o professor pode marcar aula como não realizada."
    ):
        escola.marcar_nao_realizada.executar(ADM, turma_id, date(2026, 12, 8))


def test_r08_4_faltas_nas_15_aulas_dadas(
    escola: Escola, carlos: Usuario, turma_do_carlos: TurmaDoCarlos
) -> None:
    situacao = turma_do_carlos
    # Da 1ª aula, na terça 24/11, à 15ª, na terça 12/01/2027.
    escola.ir_para(em(12, 1, 2027, 21))

    for numero in range(1, 16):
        ausentes = [situacao.ana] if numero in {2, 6, 9, 14} else []
        escola.lancar(carlos, situacao.turma, numero, ausentes)

    vista = escola.como_o_aluno_ve(situacao.ana, situacao.turma)
    assert (vista.faltas, vista.resumo.aulas_dadas) == (4, 15)


def test_r08_quem_entrou_antes_da_10a_aula_e_faltou_a_2_tem_2_faltas(
    escola: Escola, fisica: Materia, carlos: Usuario, turma_do_carlos: TurmaDoCarlos
) -> None:
    situacao = turma_do_carlos
    # A 9ª aula é na terça 22/12, e a 10ª, na quinta 24/12.
    escola.ir_para(em(23, 12, 2026))
    for numero in range(1, 10):
        escola.lancar(carlos, situacao.turma, numero)
    carla = escola.aluno("carla@exemplo.com", fisica)
    assert escola.matricular.executar(carla, situacao.turma.id).aula_de_entrada == 10
    # A 15ª aula é na terça 12/01/2027.
    escola.ir_para(em(12, 1, 2027, 21))

    for numero in range(10, 16):
        ausentes = [carla] if numero in {11, 13} else []
        escola.lancar(carlos, situacao.turma, numero, ausentes)

    assert escola.como_o_aluno_ve(carla, situacao.turma).faltas == 2
    aulas = escola.ver_aulas.executar(carlos, situacao.turma.id)
    assert "carla@exemplo.com" not in presencas_da_aula(aulas, 9)
    assert presencas_da_aula(aulas, 10)["carla@exemplo.com"] is True


def test_r08_7_faltas_na_etapa(
    escola: Escola, carlos: Usuario, turma_do_carlos: TurmaDoCarlos
) -> None:
    situacao = turma_do_carlos
    escola.ir_para(em(10, 12, 2026, 21))

    for numero in range(1, 7):
        escola.lancar(carlos, situacao.turma, numero, ausentes=[situacao.bruno])
    escola.ir_para(em(15, 12, 2026, 21))
    escola.lancar(carlos, situacao.turma, 7, ausentes=[situacao.bruno])

    assert escola.como_o_aluno_ve(situacao.bruno, situacao.turma).faltas == 7


def test_r18_r19_com_uma_aula_nao_realizada_a_13a_data_ainda_aceita_matricula(
    escola: Escola, fisica: Materia, carlos: Usuario, turma_do_carlos: TurmaDoCarlos
) -> None:
    turma = turma_do_carlos.turma
    escola.marcar_nao_realizada.executar(carlos, turma.id, date(2026, 12, 1))
    carla = escola.aluno("carla@exemplo.com", fisica)
    # Às 19h de 05/01/2027 começa a 13ª data de aula, mas só 12 aulas foram dadas.
    escola.ir_para(em(5, 1, 2027, 19))

    assert escola.matricular.executar(carla, turma.id).aula_de_entrada == 13


def test_o_professor_ve_as_aulas_da_etapa_com_a_situacao_de_cada_uma(
    escola: Escola, carlos: Usuario, turma_do_carlos: TurmaDoCarlos
) -> None:
    turma = turma_do_carlos.turma
    escola.ir_para(em(26, 11, 2026, 21))
    escola.lancar(carlos, turma, 1)

    aulas = escola.ver_aulas.executar(carlos, turma.id).aulas

    assert [aula.situacao for aula in aulas[:3]] == [
        SituacaoDaAula.COM_PRESENCA,
        SituacaoDaAula.SEM_PRESENCA,
        SituacaoDaAula.FUTURA,
    ]
    assert [aluno.email for aluno in aulas[1].alunos] == ["ana@exemplo.com", "bruno@exemplo.com"]
    assert all(aluno.presente is None for aluno in aulas[1].alunos)
