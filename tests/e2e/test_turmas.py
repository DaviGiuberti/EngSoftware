"""Telas das turmas (H29, H30, H31, H20): o ADM cria turmas e troca o professor, e o professor vê
as turmas dele. O relógio do app está parado na segunda, 23/11/2026, às 14h."""

from collections.abc import Sequence
from datetime import time

from PySide6.QtCore import QTime

from plataforma.janela_principal import AreaDoAdm
from plataforma.modules.turmas.domain.horario import DiaDaSemana
from plataforma.modules.turmas.ui.telas import CamposDoHorario, TelaTurmas
from plataforma.modules.turmas.ui.telas_do_professor import TelaMinhasTurmas
from tests.e2e.conftest import (
    EMAIL_DO_ADM,
    SENHA_DO_ADM,
    SENHA_DOS_PROFESSORES,
    App,
    escolher,
    linhas,
)

SEG, TER, QUA, QUI, SEX = (
    DiaDaSemana.SEGUNDA,
    DiaDaSemana.TERCA,
    DiaDaSemana.QUARTA,
    DiaDaSemana.QUINTA,
    DiaDaSemana.SEXTA,
)


def abrir_turmas(app: App) -> TelaTurmas:
    """Abre o app, entra como ADM e vai para a aba de turmas."""
    janela = app.abrir()
    app.entrar(janela, EMAIL_DO_ADM, SENHA_DO_ADM)
    area = janela.tela_inicio.area
    assert isinstance(area, AreaDoAdm)
    area.setCurrentWidget(area.tela_turmas)
    return area.tela_turmas


def marcar_horario(
    app: App, campos: CamposDoHorario, dias: Sequence[DiaDaSemana], inicio: str, fim: str
) -> None:
    for dia, caixa in campos.dias.items():
        if caixa.isChecked() != (dia in dias):
            app.clicar(caixa)
    campos.inicio.setTime(QTime.fromString(inicio, "HH:mm"))
    campos.fim.setTime(QTime.fromString(fim, "HH:mm"))


def criar_turma(
    app: App,
    tela: TelaTurmas,
    materia: str,
    nivel: str,
    professor: str,
    dias: Sequence[DiaDaSemana],
    inicio: str = "19:00",
    fim: str = "20:30",
) -> None:
    escolher(tela.materia, materia)
    escolher(tela.nivel, nivel)
    escolher(tela.professor, professor)
    marcar_horario(app, tela.horario_da_nova, dias, inicio, fim)
    app.clicar(tela.botao_criar)


def test_r11_r24_o_adm_cria_a_turma_de_fisica_no_n2_com_carlos(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    tela = abrir_turmas(app)

    criar_turma(app, tela, "Física", "N2", "carlos@exemplo.com", [TER, QUI])

    assert tela.mensagem.text() == (
        "Turma de Física N2 criada. A 1ª aula é em 24/11/2026, às 19h."
    )
    assert linhas(tela.tabela) == [
        [
            "Física",
            "N2",
            "carlos@exemplo.com",
            "terças e quintas, das 19h às 20h30",
            "1ª aula em 24/11/2026, às 19h",
            "12",
        ]
    ]


def test_r07_o_adm_nao_cria_outra_turma_de_carlos_que_se_sobreponha(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    app.preparar_turma("Física", 2, "carlos@exemplo.com", [TER], time(19), time(20, 30))
    tela = abrir_turmas(app)

    criar_turma(app, tela, "Física", "N1", "carlos@exemplo.com", [TER], "20:00", "21:30")

    assert tela.mensagem.text() == (
        "carlos@exemplo.com já dá aula numa turma às terças, das 19h às 20h30."
    )
    assert len(linhas(tela.tabela)) == 1


def test_r04_turma_com_aulas_as_segundas_quartas_e_sextas_mostra_a_recusa(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    tela = abrir_turmas(app)

    criar_turma(app, tela, "Física", "N2", "carlos@exemplo.com", [SEG, QUA, SEX])

    assert tela.mensagem.text() == "A turma tem no máximo 2 aulas por semana."
    assert linhas(tela.tabela) == []


def test_r11_turma_de_matematica_com_carlos_habilitado_so_em_fisica_mostra_a_recusa(
    app: App,
) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_materia("Matemática", [20, 40, 60, 80], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    tela = abrir_turmas(app)

    criar_turma(app, tela, "Matemática", "N2", "carlos@exemplo.com", [TER, QUI])

    assert tela.mensagem.text() == "carlos@exemplo.com não tem habilitação em Matemática."
    assert linhas(tela.tabela) == []


def test_r24_o_adm_tenta_mudar_o_horario_para_as_18h_e_o_sistema_recusa(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    app.preparar_turma("Física", 2, "carlos@exemplo.com", [TER, QUI], time(19), time(20, 30))
    tela = abrir_turmas(app)
    tela.tabela.selectRow(0)
    marcar_horario(app, tela.horario_da_escolhida, [TER, QUI], "18:00", "19:30")

    app.clicar(tela.botao_mudar_horario)

    assert tela.mensagem.text() == (
        "O horário da turma não muda: ela continua às terças e quintas, das 19h às 20h30."
    )
    assert tela.horario_da_escolhida.inicio.time() == QTime(19, 0)
    assert linhas(tela.tabela)[0][3] == "terças e quintas, das 19h às 20h30"


def test_r26_o_adm_troca_o_professor_da_turma_de_carlos_para_dora(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    app.preparar_professor("dora@exemplo.com", "Física")
    app.preparar_turma("Física", 2, "carlos@exemplo.com", [TER, QUI], time(19), time(20, 30))
    tela = abrir_turmas(app)
    assert not tela.botao_trocar.isEnabled()
    tela.tabela.selectRow(0)
    assert tela.escolhida.text() == (
        "Física N2, terças e quintas, das 19h às 20h30, com carlos@exemplo.com"
    )
    escolher(tela.novo_professor, "dora@exemplo.com")

    app.clicar(tela.botao_trocar)

    assert tela.mensagem.text() == "dora@exemplo.com passa a dar aula na turma de Física N2."
    assert linhas(tela.tabela)[0][2] == "dora@exemplo.com"


def test_r24_carlos_ve_so_as_suas_turmas_com_nivel_dias_e_horario(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_materia("Matemática", [20, 40, 60, 80], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    app.preparar_professor("dora@exemplo.com", "Física", "Matemática")
    app.preparar_turma("Física", 1, "carlos@exemplo.com", [TER, QUI], time(19), time(20, 30))
    app.preparar_turma("Física", 3, "carlos@exemplo.com", [SEG], time(8), time(9, 30))
    app.preparar_turma("Matemática", 2, "dora@exemplo.com", [QUA], time(19), time(20, 30))
    janela = app.abrir()

    app.entrar(janela, "carlos@exemplo.com", SENHA_DOS_PROFESSORES)

    area = janela.tela_inicio.area
    assert isinstance(area, TelaMinhasTurmas)
    assert linhas(area.tabela) == [
        ["Física", "N1", "terças e quintas, das 19h às 20h30", "1ª aula em 24/11/2026, às 19h"],
        ["Física", "N3", "segundas, das 8h às 9h30", "1ª aula em 30/11/2026, às 8h"],
    ]


def test_r43_depois_da_1a_aula_a_etapa_mostra_as_aulas_dadas(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    app.preparar_turma("Física", 2, "carlos@exemplo.com", [TER, QUI], time(19), time(20, 30))
    # Da segunda 23/11 às 14h até a quinta 26/11 às 20h: já começaram as aulas de 24 e 26/11.
    app.relogio.avancar(days=3, hours=6)
    janela = app.abrir()

    app.entrar(janela, "carlos@exemplo.com", SENHA_DOS_PROFESSORES)

    area = janela.tela_inicio.area
    assert isinstance(area, TelaMinhasTurmas)
    assert linhas(area.tabela)[0][3] == "2 de 24 aulas dadas"


def test_o_professor_sem_turmas_ve_o_aviso(app: App) -> None:
    app.preparar_professor("carlos@exemplo.com")
    janela = app.abrir()

    app.entrar(janela, "carlos@exemplo.com", SENHA_DOS_PROFESSORES)

    area = janela.tela_inicio.area
    assert isinstance(area, TelaMinhasTurmas)
    assert area.mensagem.text() == "Você ainda não tem turmas. O ADM atribui as turmas a você."


def test_a_aba_turmas_mostra_na_hora_a_materia_e_o_professor_cadastrados(app: App) -> None:
    janela = app.abrir()
    app.criar_o_primeiro_adm(janela)
    area = janela.tela_inicio.area
    assert isinstance(area, AreaDoAdm)
    materias = area.tela_materias
    app.digitar(materias.nome, "Física")
    materias.mensalidade.setValue(200.00)
    app.clicar(materias.botao_cadastrar)
    professores = area.tela_professores
    app.digitar(professores.email, "carlos@exemplo.com")
    app.digitar(professores.senha, SENHA_DOS_PROFESSORES)

    app.clicar(professores.botao_cadastrar)

    tela = area.tela_turmas
    assert tela.materia.currentText() == "Física"
    assert [tela.nivel.itemText(i) for i in range(tela.nivel.count())] == ["N1", "N2", "N3"]
    assert tela.professor.currentText() == "carlos@exemplo.com"
