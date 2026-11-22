"""Mensalidades do aluno na aba Turmas (H07). O relógio do app começa na segunda, 23/11/2026, às
14h, quando a Ana se matricula na turma de Física do N2, de terça e quinta, das 19h às 20h30. A
mensalidade de 23/12 fica em aberto desde a matrícula (R53), e sem pagá-la a Ana perde a vaga na
virada para 31/12 (R28, R37)."""

from datetime import time

from plataforma.janela_principal import AbasDoAluno, JanelaPrincipal
from plataforma.modules.turmas.domain.horario import DiaDaSemana
from plataforma.modules.turmas.ui.telas_do_aluno import TelaTurmasDoAluno
from tests.e2e.conftest import SENHA_DOS_ALUNOS, App, linhas


def preparar_ana_na_turma(app: App) -> int:
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
    app.preparar_matricula(ana, turma_id)
    return turma_id


def abrir_turmas_da_ana(app: App, janela: JanelaPrincipal) -> TelaTurmasDoAluno:
    app.entrar(janela, "ana@exemplo.com", SENHA_DOS_ALUNOS)
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    abas.setCurrentWidget(abas.turmas)
    return abas.turmas


def test_r27_r53_ana_paga_a_mensalidade_em_aberto_e_a_proxima_so_abre_no_vencimento(
    app: App,
) -> None:
    turma_id = preparar_ana_na_turma(app)
    tela = abrir_turmas_da_ana(app, app.abrir())
    assert linhas(tela.mensalidades) == [
        ["Física N2", "R$ 200,00", "23/12/2026", "em aberto", ""]
    ]

    app.clicar(tela.botoes_de_pagamento[turma_id])

    assert tela.mensagem.text() == (
        "Mensalidade de 23/12/2026 paga: R$ 200,00. A próxima vence em 23/01/2027."
    )
    assert linhas(tela.mensalidades) == [
        ["Física N2", "R$ 200,00", "23/01/2027", "paga: a próxima abre em 23/12/2026", ""]
    ]
    assert turma_id not in tela.botoes_de_pagamento


def test_r28_com_a_mensalidade_atrasada_ana_ve_ate_quando_pode_pagar(app: App) -> None:
    turma_id = preparar_ana_na_turma(app)
    # Até a segunda 28/12, às 14h: a mensalidade de 23/12 venceu.
    app.relogio.avancar(days=35)

    tela = abrir_turmas_da_ana(app, app.abrir())

    assert linhas(tela.mensalidades)[0][3] == (
        "atrasada: pague até 30/12/2026, às 23h59, para não perder a vaga"
    )
    assert turma_id in tela.botoes_de_pagamento


def test_r28_r55_sem_pagar_ana_perde_a_vaga_em_31_12_e_ve_o_aviso(app: App) -> None:
    preparar_ana_na_turma(app)
    # Até a quinta 31/12, às 14h: na virada para 31/12, a tolerância terminou.
    app.relogio.avancar(days=38)

    tela = abrir_turmas_da_ana(app, app.abrir())

    assert tela.avisos.text() == (
        "Você perdeu a vaga na turma de Física, terças e quintas, das 19h às 20h30, em "
        "31/12/2026, por atraso da mensalidade."
    )
    assert not tela.grupo_das_mensalidades.isVisible()
