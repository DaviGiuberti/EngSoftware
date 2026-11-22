"""Telas da presença (H21, H22, H08): o professor lança a presença e marca aula não realizada, e
o aluno acompanha as faltas. O relógio do app começa na segunda, 23/11/2026, às 14h, e a turma
de Física do N2, de terça e quinta, tem a 1ª aula na terça 24/11, às 19h."""

from datetime import date, time

from plataforma.janela_principal import AbasDoAluno, JanelaPrincipal
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.turmas.domain.horario import DiaDaSemana
from plataforma.modules.turmas.ui.telas_do_aluno import TelaTurmasDoAluno
from plataforma.modules.turmas.ui.telas_do_professor import TelaMinhasTurmas
from tests.e2e.conftest import SENHA_DOS_ALUNOS, SENHA_DOS_PROFESSORES, App

# As 7 primeiras aulas da turma.
AULAS = [
    date(2026, 11, 24),
    date(2026, 11, 26),
    date(2026, 12, 1),
    date(2026, 12, 3),
    date(2026, 12, 8),
    date(2026, 12, 10),
    date(2026, 12, 15),
]


def preparar_turma_com_ana_e_bruno(app: App) -> tuple[int, Usuario, Usuario]:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    turma_id = app.preparar_turma(
        "Física",
        2,
        "carlos@exemplo.com",
        [DiaDaSemana.TERCA, DiaDaSemana.QUINTA],
        time(19),
        time(20, 30),
    )
    ana = app.preparar_aluno("ana@exemplo.com", {"Física": 2})
    bruno = app.preparar_aluno("bruno@exemplo.com", {"Física": 2})
    app.preparar_matricula(ana, turma_id)
    app.preparar_matricula(bruno, turma_id)
    return turma_id, ana, bruno


def entrar_como_carlos(app: App, janela: JanelaPrincipal) -> TelaMinhasTurmas:
    """Entra como o professor e escolhe a turma dele na tabela."""
    app.entrar(janela, "carlos@exemplo.com", SENHA_DOS_PROFESSORES)
    tela = janela.tela_inicio.area
    assert isinstance(tela, TelaMinhasTurmas)
    tela.tabela.selectRow(0)
    return tela


def entrar_como_ana(app: App, janela: JanelaPrincipal) -> TelaTurmasDoAluno:
    app.entrar(janela, "ana@exemplo.com", SENHA_DOS_ALUNOS)
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    abas.setCurrentWidget(abas.turmas)
    return abas.turmas


def linhas_das_aulas(tela: TelaMinhasTurmas) -> list[tuple[str, ...]]:
    return [
        tuple(tela.aulas.item(linha, coluna).text() for coluna in range(3))
        for linha in range(tela.aulas.rowCount())
    ]


def linhas_das_etapas(tela: TelaTurmasDoAluno) -> list[tuple[str, ...]]:
    return [
        tuple(tela.etapas.item(linha, coluna).text() for coluna in range(3))
        for linha in range(tela.etapas.rowCount())
    ]


def test_r10_carlos_lanca_a_1a_aula_com_bruno_ausente(app: App) -> None:
    _, _, bruno = preparar_turma_com_ana_e_bruno(app)
    # Até a terça 24/11, às 21h: a 1ª aula já começou.
    app.relogio.avancar(days=1, hours=7)
    tela = entrar_como_carlos(app, app.abrir())
    assert linhas_das_aulas(tela)[:2] == [
        ("1ª aula", "24/11/2026, às 19h", "falta lançar a presença"),
        ("2ª aula", "26/11/2026, às 19h", "ainda não aconteceu"),
    ]
    app.clicar(tela.botoes_de_presenca[AULAS[0]])
    assert tela.titulo_da_presenca.text() == (
        "Presença da 1ª aula, 24/11/2026, às 19h. Desmarque quem faltou."
    )
    assert [caixa.text() for caixa in tela.presencas.values()] == [
        "ana@exemplo.com",
        "bruno@exemplo.com",
    ]
    app.clicar(tela.presencas[bruno.id])

    app.clicar(tela.botao_lancar)

    assert tela.mensagem.text() == "Presença da 1ª aula lançada: 1 falta."
    assert linhas_das_aulas(tela)[0][2] == "presença lançada: 1 falta"
    assert AULAS[0] not in tela.botoes_de_presenca
    assert not tela.grupo_da_presenca.isVisible()


def test_r18_carlos_marca_a_2a_aula_como_nao_realizada_e_a_etapa_ganha_uma_aula_no_fim(
    app: App,
) -> None:
    preparar_turma_com_ana_e_bruno(app)
    tela = entrar_como_carlos(app, app.abrir())

    app.clicar(tela.botoes_de_nao_realizada[AULAS[1]])

    assert tela.mensagem.text() == (
        "A aula de 26/11/2026 não foi realizada. Ela será reposta no fim da etapa: a 24ª aula "
        "passa para 16/02/2027, às 19h."
    )
    linhas = linhas_das_aulas(tela)
    assert linhas[1] == ("—", "26/11/2026, às 19h", "não realizada: reposta no fim da etapa")
    assert linhas[2][0] == "2ª aula"
    assert linhas[-1] == ("24ª aula", "16/02/2027, às 19h", "ainda não aconteceu")
    assert AULAS[1] not in tela.botoes_de_nao_realizada


def test_r08_a_aluna_ve_as_faltas_e_a_aula_da_etapa(app: App) -> None:
    turma_id, ana, _ = preparar_turma_com_ana_e_bruno(app)
    # Até a terça 01/12, às 21h: a turma deu 3 aulas, e a Ana faltou à 2ª.
    app.relogio.avancar(days=8, hours=7)
    app.preparar_presenca(turma_id, AULAS[0])
    app.preparar_presenca(turma_id, AULAS[1], [ana])
    app.preparar_presenca(turma_id, AULAS[2])

    tela = entrar_como_ana(app, app.abrir())

    assert linhas_das_etapas(tela) == [("Física N2", "aula 3 de 24", "1 de 6 faltas permitidas")]


def test_r08_com_7_faltas_a_aluna_ve_que_nao_sera_promovida_nesta_etapa(app: App) -> None:
    turma_id, ana, _ = preparar_turma_com_ana_e_bruno(app)
    # Até a terça 15/12, às 21h: a turma deu 7 aulas, e a Ana faltou a todas.
    app.relogio.avancar(days=22, hours=7)
    for data in AULAS:
        app.preparar_presenca(turma_id, data, [ana])

    tela = entrar_como_ana(app, app.abrir())

    assert linhas_das_etapas(tela) == [
        (
            "Física N2",
            "aula 7 de 24",
            "7 faltas: você passou do limite de 6 e não será promovido nesta etapa.",
        )
    ]
