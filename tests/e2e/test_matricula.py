"""Aba Turmas do aluno (H04, H05, H06, H13): as turmas do nível dele, a matrícula com a primeira
mensalidade, a lista de espera, o aviso da vaga e a saída da turma. O relógio do app está parado
na segunda, 23/11/2026, às 14h, e a turma de Física do N2 tem a 1ª aula na terça, 24/11."""

from datetime import time

from PySide6.QtWidgets import QPushButton

from plataforma.janela_principal import AbasDoAluno, JanelaPrincipal
from plataforma.modules.turmas.domain.horario import DiaDaSemana
from plataforma.modules.turmas.ui.telas_do_aluno import TelaTurmasDoAluno
from tests.e2e.conftest import SENHA_DOS_ALUNOS, App

# As questões preparadas têm a correta na B.
CORRETA = 1
ERRADA = 0


def preparar_fisica_com_turma_do_n2(app: App, questoes: int = 0) -> int:
    app.preparar_materia("Física", [40, 70], questoes)
    app.preparar_professor("carlos@exemplo.com", "Física")
    return app.preparar_turma(
        "Física",
        2,
        "carlos@exemplo.com",
        [DiaDaSemana.TERCA, DiaDaSemana.QUINTA],
        time(19),
        time(20, 30),
    )


def entrar_nas_turmas(app: App, janela: JanelaPrincipal, email: str) -> TelaTurmasDoAluno:
    """Entra como o aluno e abre a aba Turmas."""
    app.entrar(janela, email, SENHA_DOS_ALUNOS)
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    abas.setCurrentWidget(abas.turmas)
    return abas.turmas


def linhas(tela: TelaTurmasDoAluno) -> list[tuple[str, ...]]:
    """Cada turma como o aluno vê, com o texto do botão da última coluna."""
    resultado = []
    for linha in range(tela.tabela.rowCount()):
        textos = [tela.tabela.item(linha, coluna).text() for coluna in range(5)]
        botao = tela.tabela.cellWidget(linha, 5)
        textos.append(botao.text() if isinstance(botao, QPushButton) else "")
        resultado.append(tuple(textos))
    return resultado


def test_r27_ana_se_matricula_pagando_a_primeira_mensalidade(app: App) -> None:
    turma_id = preparar_fisica_com_turma_do_n2(app)
    app.preparar_aluno("ana@exemplo.com", {"Física": 2})
    tela = entrar_nas_turmas(app, app.abrir(), "ana@exemplo.com")
    assert linhas(tela) == [
        (
            "Física N2",
            "terças e quintas, das 19h às 20h30",
            "carlos@exemplo.com",
            "1ª aula em 24/11/2026, às 19h",
            "12 vagas livres.",
            "Matricular-se e pagar R$ 200,00",
        )
    ]

    app.clicar(tela.botoes[turma_id])

    assert tela.mensagem.text() == (
        "Matrícula feita na turma de Física N2. Você pagou R$ 200,00, e a próxima "
        "mensalidade vence em 23/12/2026."
    )
    assert linhas(tela)[0][4:] == (
        "Você está nesta turma. Próxima mensalidade: 23/12/2026.",
        "Sair da turma",
    )


def test_r05_ana_entra_na_lista_da_turma_cheia_e_confirma_a_vaga_que_abre(app: App) -> None:
    turma_id = preparar_fisica_com_turma_do_n2(app)
    for numero in range(1, 13):
        aluno = app.preparar_aluno(f"aluno{numero}@exemplo.com", {"Física": 2})
        app.preparar_matricula(aluno, turma_id)
    app.preparar_aluno("ana@exemplo.com", {"Física": 2})
    janela = app.abrir()
    tela = entrar_nas_turmas(app, janela, "ana@exemplo.com")
    assert linhas(tela)[0][4:] == ("Turma cheia.", "Entrar na lista de espera")

    app.clicar(tela.botoes[turma_id])

    assert tela.mensagem.text() == (
        "Você entrou na lista de espera da turma de Física N2, em 1º lugar."
    )
    assert linhas(tela)[0][4:] == ("Lista de espera: 1º lugar.", "")
    app.clicar(janela.tela_inicio.botao_sair)
    saindo = entrar_nas_turmas(app, janela, "aluno1@exemplo.com")
    app.clicar(saindo.botoes[turma_id])
    assert saindo.mensagem.text() == (
        "Você saiu da turma de Física N2. A mensalidade já paga não é devolvida."
    )
    app.clicar(janela.tela_inicio.botao_sair)
    tela = entrar_nas_turmas(app, janela, "ana@exemplo.com")
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    assert abas.tabText(abas.indexOf(tela)) == "Turmas · 1 vaga para você"
    assert tela.avisos.text() == (
        "Abriu uma vaga para você na turma de Física N2, terças e quintas, das 19h às 20h30. "
        "Confirme até 26/11/2026, às 14h."
    )

    app.clicar(tela.botoes[turma_id])

    assert tela.mensagem.text() == (
        "Vaga confirmada: você está na turma de Física N2. Você pagou R$ 200,00, e a próxima "
        "mensalidade vence em 23/12/2026."
    )
    assert linhas(tela)[0][4] == "Você está nesta turma. Próxima mensalidade: 23/12/2026."
    assert tela.avisos.text() == ""
    assert abas.tabText(abas.indexOf(tela)) == "Turmas"


def test_r19_quando_a_13a_aula_comeca_a_matricula_mostra_a_recusa(app: App) -> None:
    turma_id = preparar_fisica_com_turma_do_n2(app)
    app.preparar_aluno("ana@exemplo.com", {"Física": 2})
    # Da segunda 23/11/2026 às 14h até a terça 05/01/2027 às 19h, quando começa a 13ª aula.
    app.relogio.avancar(days=43, hours=5)
    tela = entrar_nas_turmas(app, app.abrir(), "ana@exemplo.com")

    app.clicar(tela.botoes[turma_id])

    assert tela.mensagem.text() == (
        "A matrícula nesta turma fechou: só dá para entrar até antes da 13ª aula da etapa."
    )


def test_o_aluno_sem_nivel_ve_que_precisa_fazer_o_nivelamento(app: App) -> None:
    preparar_fisica_com_turma_do_n2(app)
    app.preparar_aluno("ana@exemplo.com")

    tela = entrar_nas_turmas(app, app.abrir(), "ana@exemplo.com")

    assert linhas(tela) == []
    assert tela.mensagem.text() == (
        "Você ainda não tem turmas do seu nível. Faça o nivelamento em Meus níveis para ver "
        "as turmas de cada matéria."
    )


def test_depois_do_nivelamento_a_aba_turmas_mostra_as_turmas_do_novo_nivel(app: App) -> None:
    preparar_fisica_com_turma_do_n2(app, questoes=5)
    app.preparar_aluno("ana@exemplo.com")
    janela = app.abrir()
    app.entrar(janela, "ana@exemplo.com", SENHA_DOS_ALUNOS)
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    nivelamento = abas.nivelamento
    app.clicar(nivelamento.tela_meus_niveis.botoes["Física"])
    teste = nivelamento.tela_do_nivelamento
    # 2 de 5 certas dão 40%, o N2 de Física.
    for indice, posicao in enumerate([CORRETA, CORRETA, ERRADA, ERRADA, ERRADA]):
        app.clicar(teste.alternativas[posicao])
        if indice < 4:
            app.clicar(teste.botao_proxima)
    app.clicar(teste.botao_entregar)

    abas.setCurrentWidget(abas.turmas)

    assert [linha[0] for linha in linhas(abas.turmas)] == ["Física N2"]
