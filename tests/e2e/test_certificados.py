"""Aba Meus certificados do aluno (H12). O relógio do app começa na segunda, 23/11/2026, às 14h. A
turma de Física, de terça e quinta, termina a etapa na quinta 11/02/2027 às 20h30, e a nota
lançada na sexta 12/02 às 10h vale na segunda 15/02 às 10h (R49)."""

from datetime import time

from plataforma.janela_principal import AbasDoAluno, JanelaPrincipal
from plataforma.modules.nivelamento.ui.telas_do_aluno import TelaMeusCertificados
from plataforma.modules.turmas.domain.horario import DiaDaSemana
from tests.e2e.conftest import SENHA_DOS_ALUNOS, App, linhas


def preparar_ana_aprovada(app: App, nivel: int) -> None:
    """Ana, na turma de Física do nível, tira 8 na prova final, e o resultado vale."""
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    turma_id = app.preparar_turma(
        "Física",
        nivel,
        "carlos@exemplo.com",
        [DiaDaSemana.TERCA, DiaDaSemana.QUINTA],
        time(19),
        time(20, 30),
    )
    ana = app.preparar_aluno("ana@exemplo.com", {"Física": nivel})
    app.preparar_matricula(ana, turma_id)
    # Até a sexta 12/02/2027, às 10h, e depois até a segunda 15/02, às 10h.
    app.relogio.avancar(days=80, hours=20)
    app.preparar_nota(turma_id, nivel, ana, "8")
    app.relogio.avancar(days=3)


def abrir_meus_certificados(app: App, janela: JanelaPrincipal) -> TelaMeusCertificados:
    app.entrar(janela, "ana@exemplo.com", SENHA_DOS_ALUNOS)
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    abas.setCurrentWidget(abas.certificados)
    return abas.certificados


def test_r33_ana_promovida_do_n1_ve_o_certificado_de_nivel_do_n1(app: App) -> None:
    preparar_ana_aprovada(app, nivel=1)

    tela = abrir_meus_certificados(app, app.abrir())

    assert linhas(tela.tabela) == [["Física", "Certificado de nível", "N1", "15/02/2027"]]


def test_r36_ana_aprovada_no_n3_ve_o_certificado_do_n3_e_o_de_trilha(app: App) -> None:
    preparar_ana_aprovada(app, nivel=3)

    tela = abrir_meus_certificados(app, app.abrir())

    assert linhas(tela.tabela) == [
        ["Física", "Certificado de nível", "N3", "15/02/2027"],
        ["Física", "Certificado de trilha", "N3", "15/02/2027"],
    ]


def test_r33_quem_so_fez_o_nivelamento_ve_que_ainda_nao_tem_certificados(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_aluno("ana@exemplo.com", {"Física": 3})

    tela = abrir_meus_certificados(app, app.abrir())

    assert linhas(tela.tabela) == []
    assert tela.mensagem.text() == (
        "Você ainda não tem certificados. O certificado de nível sai quando você é aprovado na "
        "etapa de uma turma, e o de trilha, quando é aprovado no nível máximo da matéria."
    )
