"""Telas do fim da etapa (H23, H24, H32, H10, H20, H08, H03): o professor e o ADM lançam e corrigem
a nota da prova final e a presença, a turma passa para o nível seguinte, e o aluno vê o resultado
e o nível novo. O relógio do app começa na segunda, 23/11/2026, às 14h. A turma de Física, de
terça e quinta das 19h às 20h30, tem a 1ª aula na terça 24/11 e a 24ª na quinta 11/02/2027: a
etapa termina às 20h30 desse dia, e a seguinte começa na terça 16/02/2027."""

from datetime import date, time

from PySide6.QtWidgets import QPushButton

from plataforma.janela_principal import (
    AbasDoAluno,
    AbasDoProfessor,
    AreaDoAdm,
    JanelaPrincipal,
)
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.turmas.domain.horario import DiaDaSemana
from plataforma.modules.turmas.ui.telas_do_professor import (
    TelaDasAulas,
    TelaMinhasTurmas,
    TelaPresencaENotas,
)
from tests.e2e.conftest import (
    EMAIL_DO_ADM,
    SENHA_DO_ADM,
    SENHA_DOS_ALUNOS,
    SENHA_DOS_PROFESSORES,
    App,
    escolher,
    linhas,
)

PRIMEIRA_AULA = date(2026, 11, 24)
ETAPA_DO_N2 = "N2 · terminou em 11/02/2027"


def preparar_turma_com_ana_e_bruno(app: App, nivel: int = 2) -> tuple[int, Usuario, Usuario]:
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
    bruno = app.preparar_aluno("bruno@exemplo.com", {"Física": nivel})
    app.preparar_matricula(ana, turma_id)
    app.preparar_matricula(bruno, turma_id)
    # Com as mensalidades pagas, eles não perdem a vaga por atraso até o fim da etapa (R28).
    app.preparar_mensalidades(ana, turma_id)
    app.preparar_mensalidades(bruno, turma_id)
    return turma_id, ana, bruno


def ir_para_sexta_12_02_as_10h(app: App) -> None:
    """Do relógio inicial, na segunda 23/11/2026 às 14h, até o dia seguinte ao fim da etapa."""
    app.relogio.avancar(days=80, hours=20)


def entrar_como_carlos(app: App, janela: JanelaPrincipal) -> TelaMinhasTurmas:
    """Entra como o professor e escolhe a turma dele na tabela."""
    app.entrar(janela, "carlos@exemplo.com", SENHA_DOS_PROFESSORES)
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoProfessor)
    tela = abas.turmas
    assert isinstance(tela, TelaMinhasTurmas)
    tela.tabela.selectRow(0)
    return tela


def entrar_como_adm_em_presenca_e_notas(app: App, janela: JanelaPrincipal) -> TelaPresencaENotas:
    """Entra como o ADM, abre a aba "Presença e notas" e escolhe a turma do Carlos."""
    app.entrar(janela, EMAIL_DO_ADM, SENHA_DO_ADM)
    area = janela.tela_inicio.area
    assert isinstance(area, AreaDoAdm)
    area.setCurrentWidget(area.tela_presenca_e_notas)
    tela = area.tela_presenca_e_notas
    tela.tabela.selectRow(0)
    return tela


def abrir_a_prova_final_do_n2(tela: TelaDasAulas) -> None:
    escolher(tela.etapa, ETAPA_DO_N2)
    tela.abas_da_etapa.setCurrentWidget(tela.pagina_da_prova_final)


def dar_nota(app: App, tela: TelaDasAulas, aluno: Usuario, nota: str) -> None:
    """Clica no botão da nota do aluno, digita a nota e salva."""
    app.clicar(tela.botoes_de_nota[aluno.id])
    app.digitar(tela.campo_da_nota, nota)
    app.clicar(tela.botao_salvar_nota)


def test_r20_carlos_lanca_a_nota_8_de_ana_na_prova_final_do_n2(app: App) -> None:
    _, ana, _ = preparar_turma_com_ana_e_bruno(app)
    ir_para_sexta_12_02_as_10h(app)
    tela = entrar_como_carlos(app, app.abrir())
    assert [tela.etapa.itemText(i) for i in range(tela.etapa.count())] == [
        ETAPA_DO_N2,
        "N3 · etapa atual",
    ]
    abrir_a_prova_final_do_n2(tela)
    assert linhas(tela.notas)[0][:4] == [
        "ana@exemplo.com",
        "0 faltas",
        "—",
        "pendente: falta a nota",
    ]
    app.clicar(tela.botoes_de_nota[ana.id])
    assert tela.titulo_da_nota.text() == "Nota de ana@exemplo.com na prova final do N2."
    app.digitar(tela.campo_da_nota, "8")

    app.clicar(tela.botao_salvar_nota)

    assert tela.mensagem.text() == "Nota de ana@exemplo.com lançada: 8."
    assert linhas(tela.notas)[0][:4] == [
        "ana@exemplo.com",
        "0 faltas",
        "8",
        "aprovado: vale em 15/02/2027, às 10h",
    ]
    assert tela.botoes_de_nota[ana.id].text() == "Corrigir nota"
    assert not tela.grupo_da_nota.isVisible()
    # R48: a etapa que terminou não tem mais aula para marcar como não realizada.
    assert tela.botoes_de_nao_realizada == {}


def test_r17_antes_do_fim_da_etapa_a_prova_final_diz_quando_a_nota_sera_lancada(app: App) -> None:
    preparar_turma_com_ana_e_bruno(app)
    tela = entrar_como_carlos(app, app.abrir())

    tela.abas_da_etapa.setCurrentWidget(tela.pagina_da_prova_final)

    assert tela.aviso_da_prova_final.text() == (
        "A nota da prova final é lançada no fim da etapa, depois da 24ª aula: em 11/02/2027, "
        "às 20h30."
    )
    assert tela.notas.rowCount() == 0


def test_r22_depois_de_72_horas_carlos_nao_corrige_a_nota_e_so_o_adm_pode(app: App) -> None:
    turma_id, ana, _ = preparar_turma_com_ana_e_bruno(app)
    ir_para_sexta_12_02_as_10h(app)
    app.preparar_nota(turma_id, 2, ana, "6")
    # Até a segunda 15/02, às 10h01: o prazo de correção terminou às 10h.
    app.relogio.avancar(days=3, minutes=1)
    tela = entrar_como_carlos(app, app.abrir())
    abrir_a_prova_final_do_n2(tela)

    dar_nota(app, tela, ana, "7")

    assert tela.mensagem.text() == (
        "O prazo de correção terminou em 15/02/2027, às 10h, 72 horas depois do lançamento: "
        "agora só o ADM pode corrigir."
    )
    assert linhas(tela.notas)[0][2] == "6"


def test_r22_carlos_corrige_a_falta_de_bruno_dentro_das_72_horas(app: App) -> None:
    turma_id, _, bruno = preparar_turma_com_ana_e_bruno(app)
    # Até a terça 24/11, às 21h: a 1ª aula já começou, e Bruno ficou com falta.
    app.relogio.avancar(days=1, hours=7)
    app.preparar_presenca(turma_id, PRIMEIRA_AULA, [bruno])
    tela = entrar_como_carlos(app, app.abrir())
    app.clicar(tela.botoes_de_correcao[PRIMEIRA_AULA])
    assert tela.titulo_da_presenca.text() == (
        "Correção da presença da 1ª aula, 24/11/2026, às 19h. Desmarque quem faltou."
    )
    assert {caixa.text(): caixa.isChecked() for caixa in tela.presencas.values()} == {
        "ana@exemplo.com": True,
        "bruno@exemplo.com": False,
    }
    app.clicar(tela.presencas[bruno.id])

    app.clicar(tela.botao_corrigir)

    assert tela.mensagem.text() == "Presença da 1ª aula corrigida: 0 faltas."
    assert linhas(tela.aulas)[0][2] == "presença lançada: 0 faltas"
    assert not tela.grupo_da_presenca.isVisible()


def test_r23_o_adm_lanca_a_nota_de_ana_na_aba_presenca_e_notas(app: App) -> None:
    _, ana, _ = preparar_turma_com_ana_e_bruno(app)
    ir_para_sexta_12_02_as_10h(app)
    tela = entrar_como_adm_em_presenca_e_notas(app, app.abrir())
    assert linhas(tela.tabela) == [
        [
            "Física",
            "N3",
            "carlos@exemplo.com",
            "terças e quintas, das 19h às 20h30",
            "1ª aula em 16/02/2027, às 19h",
        ]
    ]
    abrir_a_prova_final_do_n2(tela)

    dar_nota(app, tela, ana, "8")

    assert tela.mensagem.text() == "Nota de ana@exemplo.com lançada: 8."
    # Marcar aula como não realizada é só do professor (H22).
    assert tela.botoes_de_nao_realizada == {}


def test_r22_r52_o_adm_corrige_a_nota_de_ana_que_saiu_reprovada_e_ela_ve_o_n3(app: App) -> None:
    turma_id, ana, _ = preparar_turma_com_ana_e_bruno(app)
    ir_para_sexta_12_02_as_10h(app)
    app.preparar_nota(turma_id, 2, ana, "6")
    # Até a sexta 19/02, às 10h: Ana saiu da turma, reprovada, na segunda 15/02 às 10h.
    app.relogio.avancar(days=7)
    janela = app.abrir()
    tela = entrar_como_adm_em_presenca_e_notas(app, janela)
    abrir_a_prova_final_do_n2(tela)
    assert linhas(tela.notas)[0][2:4] == ["6", "reprovado"]

    dar_nota(app, tela, ana, "7")

    assert tela.mensagem.text() == "Nota de ana@exemplo.com corrigida para 7."
    assert linhas(tela.notas)[0][2:4] == ["7", "aprovado"]
    app.clicar(janela.tela_inicio.botao_sair)
    app.entrar(janela, "ana@exemplo.com", SENHA_DOS_ALUNOS)
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    tabela = abas.nivelamento.tela_meus_niveis.tabela
    assert [tabela.item(0, coluna).text() for coluna in range(2)] == ["Física", "N3"]


def test_r25_o_adm_nao_encerra_a_turma(app: App) -> None:
    preparar_turma_com_ana_e_bruno(app)
    janela = app.abrir()
    app.entrar(janela, EMAIL_DO_ADM, SENHA_DO_ADM)
    area = janela.tela_inicio.area
    assert isinstance(area, AreaDoAdm)
    area.setCurrentWidget(area.tela_turmas)
    tela = area.tela_turmas
    tela.tabela.selectRow(0)

    app.clicar(tela.botao_encerrar)

    assert tela.mensagem.text() == (
        "A turma não pode ser encerrada: ela encerra sozinha no fim da etapa do N3, o nível "
        "máximo."
    )


def test_r04_r26_no_fim_da_etapa_carlos_ve_a_turma_no_n3_com_a_1a_aula_em_16_02(app: App) -> None:
    preparar_turma_com_ana_e_bruno(app)
    ir_para_sexta_12_02_as_10h(app)

    tela = entrar_como_carlos(app, app.abrir())

    assert linhas(tela.tabela) == [
        ["Física", "N3", "terças e quintas, das 19h às 20h30", "1ª aula em 16/02/2027, às 19h"]
    ]


def test_r49_ana_ve_a_nota_e_quando_vale_o_resultado_em_minhas_etapas(app: App) -> None:
    turma_id, ana, _ = preparar_turma_com_ana_e_bruno(app)
    ir_para_sexta_12_02_as_10h(app)
    app.preparar_nota(turma_id, 2, ana, "8")
    janela = app.abrir()

    app.entrar(janela, "ana@exemplo.com", SENHA_DOS_ALUNOS)

    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    abas.setCurrentWidget(abas.turmas)
    assert linhas(abas.turmas.etapas) == [
        [
            "Física N3",
            "antes da 1ª aula",
            "0 de 6 faltas permitidas",
            "N2: nota 8, aprovado. Vale em 15/02/2027, às 10h.",
        ]
    ]


def test_r09_ana_aprovada_no_n3_ve_a_trilha_de_fisica_concluida(app: App) -> None:
    turma_id, ana, _ = preparar_turma_com_ana_e_bruno(app, nivel=3)
    ir_para_sexta_12_02_as_10h(app)
    app.preparar_nota(turma_id, 3, ana, "8")
    # Até a segunda 15/02, às 10h: o resultado vale, e a trilha de Física fica concluída.
    app.relogio.avancar(days=3)
    janela = app.abrir()

    app.entrar(janela, "ana@exemplo.com", SENHA_DOS_ALUNOS)

    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    tabela = abas.nivelamento.tela_meus_niveis.tabela
    assert [tabela.item(0, coluna).text() for coluna in range(3)] == [
        "Física",
        "N3",
        "Trilha concluída",
    ]
    assert not isinstance(tabela.cellWidget(0, 2), QPushButton)
