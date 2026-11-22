"""Turmas com o banco SQLite e um relógio de teste (H29, H30, H31, H20): criar turma, trocar o
professor e ver as turmas. R04, R07, R11, R24, R26, R43 e RNF07."""

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, time

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
from plataforma.modules.identidade.domain.professor import (
    ProfessorNaoEncontrado,
    SemHabilitacao,
)
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
from plataforma.modules.materias.domain.materia import Materia, MateriaNaoEncontrada
from plataforma.modules.materias.infra.repositorio_de_materias import (
    RepositorioDeMateriasSqlite,
)
from plataforma.modules.nivelamento.application.promocao import Promocoes
from plataforma.modules.nivelamento.infra.repositorio_de_nivelamentos import (
    RepositorioDeNivelamentosSqlite,
)
from plataforma.modules.turmas.application.casos_de_uso import (
    CriarTurma,
    MudarHorario,
    ResumoDaTurma,
    TrocarProfessor,
    VerMinhasTurmas,
    VerTurmas,
)
from plataforma.modules.turmas.application.em_dia import TurmasEmDia
from plataforma.modules.turmas.domain.horario import (
    DiaDaSemana,
    HorarioInvalido,
    descrever_horario,
    novo_horario,
)
from plataforma.modules.turmas.domain.turma import (
    ConflitoDeHorario,
    HorarioFixo,
    MesmoProfessor,
    NivelForaDaMateria,
    Turma,
    TurmaNaoEncontrada,
)
from plataforma.modules.turmas.infra.repositorio_de_turmas import RepositorioDeTurmasSqlite
from tests.integracao.conftest import RelogioDeTeste

ADM = Usuario(id=1000, email="adm@exemplo.com", perfil=Perfil.ADM)
SEG, TER, QUA, QUI, SEX = (
    DiaDaSemana.SEGUNDA,
    DiaDaSemana.TERCA,
    DiaDaSemana.QUARTA,
    DiaDaSemana.QUINTA,
    DiaDaSemana.SEXTA,
)
TERCA_24_11_19H = datetime(2026, 11, 24, 19, 0, tzinfo=BRASILIA)


@dataclass(frozen=True)
class Casos:
    cadastrar_materia: CadastrarMateria
    cadastrar_professor: CadastrarProfessor
    habilitar_professor: HabilitarProfessor
    cadastrar_aluno: CadastrarAluno
    criar_turma: CriarTurma
    trocar_professor: TrocarProfessor
    mudar_horario: MudarHorario
    ver_turmas: VerTurmas
    ver_minhas_turmas: VerMinhasTurmas


@pytest.fixture
def casos(
    conexao: sqlite3.Connection, em_transacao: Transacao, relogio: RelogioDeTeste
) -> Casos:
    usuarios = RepositorioDeUsuariosSqlite(conexao)
    repositorio_de_professores = RepositorioDeProfessoresSqlite(conexao)
    professores = ConsultaDeProfessores(repositorio_de_professores)
    repositorio_de_materias = RepositorioDeMateriasSqlite(conexao)
    materias = ConsultaDeMaterias(repositorio_de_materias)
    turmas = RepositorioDeTurmasSqlite(conexao)
    promocoes = Promocoes(RepositorioDeNivelamentosSqlite(conexao), materias)
    em_dia = TurmasEmDia(turmas, materias, promocoes)
    leitura = (turmas, materias, professores, relogio, em_transacao, em_dia)
    return Casos(
        cadastrar_materia=CadastrarMateria(repositorio_de_materias, em_transacao),
        cadastrar_professor=CadastrarProfessor(usuarios, em_transacao),
        habilitar_professor=HabilitarProfessor(repositorio_de_professores, materias, em_transacao),
        cadastrar_aluno=CadastrarAluno(usuarios, em_transacao),
        criar_turma=CriarTurma(*leitura),
        trocar_professor=TrocarProfessor(*leitura),
        mudar_horario=MudarHorario(turmas),
        ver_turmas=VerTurmas(*leitura),
        ver_minhas_turmas=VerMinhasTurmas(*leitura),
    )


def professor_habilitado(casos: Casos, email: str, *materias: Materia) -> Usuario:
    professor = casos.cadastrar_professor.executar(ADM, email, "abcd1234")
    for materia in materias:
        casos.habilitar_professor.executar(ADM, professor.id, materia.id)
    return professor


def criar(
    casos: Casos,
    materia: Materia,
    nivel: int,
    professor: Usuario,
    dias: Sequence[DiaDaSemana],
    inicio: str = "19:00",
    fim: str = "20:30",
) -> Turma:
    return casos.criar_turma.executar(
        ADM,
        materia.id,
        nivel,
        professor.id,
        dias,
        time.fromisoformat(inicio),
        time.fromisoformat(fim),
    )


def professores_das_turmas(casos: Casos) -> list[str]:
    return [resumo.email_do_professor for resumo in casos.ver_turmas.executar(ADM)]


@pytest.fixture
def fisica(casos: Casos) -> Materia:
    return casos.cadastrar_materia.executar(ADM, "Física", 3, [40, 70], 20000)


@pytest.fixture
def matematica(casos: Casos) -> Materia:
    return casos.cadastrar_materia.executar(ADM, "Matemática", 5, [20, 40, 60, 80], 25000)


@pytest.fixture
def carlos(casos: Casos, fisica: Materia) -> Usuario:
    return professor_habilitado(casos, "carlos@exemplo.com", fisica)


@pytest.fixture
def dora(casos: Casos, fisica: Materia, matematica: Materia) -> Usuario:
    return professor_habilitado(casos, "dora@exemplo.com", fisica, matematica)


def test_r11_r24_turma_de_fisica_no_n2_com_carlos_nasce_antes_da_1a_aula_com_12_vagas(
    casos: Casos, fisica: Materia, carlos: Usuario
) -> None:
    turma = criar(casos, fisica, 2, carlos, [TER, QUI])

    assert casos.ver_turmas.executar(ADM) == [
        ResumoDaTurma(
            id=turma.id,
            materia_id=fisica.id,
            nome_da_materia="Física",
            nivel=2,
            professor_id=carlos.id,
            email_do_professor="carlos@exemplo.com",
            horario=novo_horario([TER, QUI], time(19), time(20, 30)),
            inicio_da_etapa=TERCA_24_11_19H,
            aulas_dadas=0,
            vagas_livres=12,
        )
    ]


def test_r43_criada_na_segunda_23_11_as_14h_a_1a_aula_e_na_terca_24_11_as_19h(
    casos: Casos, fisica: Materia, carlos: Usuario
) -> None:
    turma = criar(casos, fisica, 2, carlos, [TER, QUI])

    assert turma.inicio_da_etapa == TERCA_24_11_19H


def test_r43_as_aulas_dadas_seguem_o_relogio(
    casos: Casos, fisica: Materia, carlos: Usuario, relogio: RelogioDeTeste
) -> None:
    criar(casos, fisica, 2, carlos, [TER, QUI])

    # Da segunda 23/11 às 14h até a quinta 31/12 às 19h: 6 semanas de terças e quintas.
    relogio.avancar(days=38, hours=5)

    [resumo] = casos.ver_turmas.executar(ADM)
    assert resumo.aulas_dadas == 12


def test_r11_carlos_habilitado_em_fisica_cria_turma_de_fisica_no_n3(
    casos: Casos, fisica: Materia, carlos: Usuario
) -> None:
    turma = criar(casos, fisica, 3, carlos, [TER, QUI])

    assert (turma.materia_id, turma.nivel, turma.professor_id) == (fisica.id, 3, carlos.id)


def test_r11_carlos_habilitado_so_em_fisica_nao_entra_numa_turma_de_matematica(
    casos: Casos, matematica: Materia, carlos: Usuario
) -> None:
    with pytest.raises(
        SemHabilitacao, match="carlos@exemplo.com não tem habilitação em Matemática."
    ):
        criar(casos, matematica, 2, carlos, [TER, QUI])

    assert casos.ver_turmas.executar(ADM) == []


def test_r07_carlos_com_turma_as_tercas_19h_nao_pega_outra_as_tercas_20h(
    casos: Casos, fisica: Materia, carlos: Usuario
) -> None:
    criar(casos, fisica, 2, carlos, [TER], "19:00", "20:30")

    with pytest.raises(
        ConflitoDeHorario,
        match="carlos@exemplo.com já dá aula numa turma às terças, das 19h às 20h30.",
    ):
        criar(casos, fisica, 1, carlos, [TER], "20:00", "21:30")

    assert professores_das_turmas(casos) == ["carlos@exemplo.com"]


def test_r07_outro_professor_pode_ter_turma_no_mesmo_horario(
    casos: Casos, fisica: Materia, carlos: Usuario, dora: Usuario
) -> None:
    criar(casos, fisica, 2, carlos, [TER, QUI])

    criar(casos, fisica, 1, dora, [TER, QUI])

    assert professores_das_turmas(casos) == ["carlos@exemplo.com", "dora@exemplo.com"]


def test_r04_turma_com_aulas_as_segundas_quartas_e_sextas_e_recusada(
    casos: Casos, fisica: Materia, carlos: Usuario
) -> None:
    with pytest.raises(HorarioInvalido, match="A turma tem no máximo 2 aulas por semana."):
        criar(casos, fisica, 2, carlos, [SEG, QUA, SEX])

    assert casos.ver_turmas.executar(ADM) == []


def test_r24_nivel_que_a_materia_nao_tem_e_recusado(
    casos: Casos, fisica: Materia, carlos: Usuario
) -> None:
    with pytest.raises(NivelForaDaMateria, match="Física tem os níveis N1 a N3."):
        criar(casos, fisica, 4, carlos, [TER, QUI])


def test_r24_o_adm_nao_muda_o_horario_da_turma_para_as_18h(
    casos: Casos, fisica: Materia, carlos: Usuario
) -> None:
    turma = criar(casos, fisica, 2, carlos, [TER, QUI])

    with pytest.raises(HorarioFixo, match="O horário da turma não muda"):
        casos.mudar_horario.executar(ADM, turma.id, [TER, QUI], time(18), time(19, 30))

    [resumo] = casos.ver_turmas.executar(ADM)
    assert descrever_horario(resumo.horario) == "terças e quintas, das 19h às 20h30"


def test_rnf07_professor_nao_cria_turma(
    casos: Casos, fisica: Materia, carlos: Usuario
) -> None:
    with pytest.raises(AcessoNegado, match="Só o ADM pode criar turma."):
        casos.criar_turma.executar(
            carlos, fisica.id, 2, carlos.id, [TER, QUI], time(19), time(20, 30)
        )


def test_rnf07_professor_nao_tenta_mudar_o_horario(
    casos: Casos, fisica: Materia, carlos: Usuario
) -> None:
    turma = criar(casos, fisica, 2, carlos, [TER, QUI])

    with pytest.raises(AcessoNegado, match="Só o ADM pode mudar o horário da turma."):
        casos.mudar_horario.executar(carlos, turma.id, [TER, QUI], time(18), time(19, 30))


def test_turma_de_materia_que_nao_existe_e_recusada(casos: Casos, carlos: Usuario) -> None:
    with pytest.raises(MateriaNaoEncontrada):
        casos.criar_turma.executar(ADM, 999, 1, carlos.id, [TER], time(19), time(20, 30))


def test_turma_com_quem_nao_e_professor_e_recusada(casos: Casos, fisica: Materia) -> None:
    ana = casos.cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")

    with pytest.raises(ProfessorNaoEncontrado):
        criar(casos, fisica, 2, ana, [TER, QUI])


def test_r26_o_adm_troca_o_professor_da_turma_de_carlos_para_dora(
    casos: Casos, fisica: Materia, carlos: Usuario, dora: Usuario
) -> None:
    turma = criar(casos, fisica, 2, carlos, [TER, QUI])

    trocada = casos.trocar_professor.executar(ADM, turma.id, dora.id)

    assert trocada.professor_id == dora.id
    [resumo] = casos.ver_turmas.executar(ADM)
    assert resumo.email_do_professor == "dora@exemplo.com"
    assert (resumo.nivel, resumo.horario) == (turma.nivel, turma.horario)


def test_r11_troca_para_professor_habilitado_so_em_matematica_e_recusada(
    casos: Casos, fisica: Materia, matematica: Materia, carlos: Usuario
) -> None:
    turma = criar(casos, fisica, 2, carlos, [TER, QUI])
    eva = professor_habilitado(casos, "eva@exemplo.com", matematica)

    with pytest.raises(SemHabilitacao, match="eva@exemplo.com não tem habilitação em Física."):
        casos.trocar_professor.executar(ADM, turma.id, eva.id)

    assert professores_das_turmas(casos) == ["carlos@exemplo.com"]


def test_r07_troca_para_dora_com_outra_turma_no_mesmo_horario_e_recusada(
    casos: Casos, fisica: Materia, matematica: Materia, carlos: Usuario, dora: Usuario
) -> None:
    turma = criar(casos, fisica, 2, carlos, [TER], "19:00", "20:30")
    criar(casos, matematica, 1, dora, [TER], "19:00", "20:30")

    with pytest.raises(
        ConflitoDeHorario,
        match="dora@exemplo.com já dá aula numa turma às terças, das 19h às 20h30.",
    ):
        casos.trocar_professor.executar(ADM, turma.id, dora.id)

    assert professores_das_turmas(casos) == ["carlos@exemplo.com", "dora@exemplo.com"]


def test_r26_trocar_pelo_professor_que_ja_da_aula_na_turma_e_recusado(
    casos: Casos, fisica: Materia, carlos: Usuario
) -> None:
    turma = criar(casos, fisica, 2, carlos, [TER, QUI])

    with pytest.raises(MesmoProfessor, match="carlos@exemplo.com já dá aula nesta turma."):
        casos.trocar_professor.executar(ADM, turma.id, carlos.id)


def test_rnf07_professor_nao_troca_o_professor_da_turma(
    casos: Casos, fisica: Materia, carlos: Usuario, dora: Usuario
) -> None:
    turma = criar(casos, fisica, 2, carlos, [TER, QUI])

    with pytest.raises(AcessoNegado, match="Só o ADM pode trocar o professor da turma."):
        casos.trocar_professor.executar(carlos, turma.id, dora.id)


def test_turma_que_nao_existe_e_recusada(casos: Casos, carlos: Usuario) -> None:
    with pytest.raises(TurmaNaoEncontrada, match="Turma não encontrada."):
        casos.trocar_professor.executar(ADM, 999, carlos.id)


def test_r24_carlos_ve_so_as_suas_duas_turmas_de_fisica_com_nivel_dias_e_horario(
    casos: Casos, fisica: Materia, matematica: Materia, carlos: Usuario, dora: Usuario
) -> None:
    criar(casos, fisica, 1, carlos, [TER, QUI])
    criar(casos, fisica, 3, carlos, [SEG], "08:00", "09:30")
    criar(casos, matematica, 2, dora, [QUA])

    minhas = casos.ver_minhas_turmas.executar(carlos)

    assert [(r.nome_da_materia, r.nivel, descrever_horario(r.horario)) for r in minhas] == [
        ("Física", 1, "terças e quintas, das 19h às 20h30"),
        ("Física", 3, "segundas, das 8h às 9h30"),
    ]
    assert [r.nome_da_materia for r in casos.ver_minhas_turmas.executar(dora)] == ["Matemática"]


def test_rnf07_so_o_professor_ve_as_proprias_turmas(casos: Casos) -> None:
    ana = casos.cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")

    with pytest.raises(AcessoNegado, match="Só o professor pode ver as próprias turmas."):
        casos.ver_minhas_turmas.executar(ana)


def test_rnf07_so_o_adm_ve_todas_as_turmas(casos: Casos, carlos: Usuario) -> None:
    with pytest.raises(AcessoNegado, match="Só o ADM pode ver todas as turmas."):
        casos.ver_turmas.executar(carlos)
