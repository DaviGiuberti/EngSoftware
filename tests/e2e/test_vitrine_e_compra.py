"""Aba "Pacotes" do aluno (H14, H15, H16, H35): a vitrine com destaque para o nível dele, a compra,
as aulas, que abrem no navegador, e a aula concluída. O relógio do app começa em 23/11/2026."""

from plataforma.janela_principal import AbasDoAluno, JanelaPrincipal
from plataforma.modules.catalogo.domain.pacote import EstadoPacote
from plataforma.modules.vendas.ui.telas_do_aluno import TelaPacotesDoAluno
from tests.e2e.conftest import SENHA_DOS_ALUNOS, App, linhas


def preparar_vitrine(app: App) -> dict[str, int]:
    """Física com Carlos e três pacotes publicados, do N1, do N2 e do N3, e um rascunho."""
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    publicado = EstadoPacote.PUBLICADO
    return {
        "N3": app.preparar_pacote("Ondas", "Física", 3, "carlos@exemplo.com", 2, publicado),
        "N1": app.preparar_pacote("Cinemática", "Física", 1, "carlos@exemplo.com", 3, publicado),
        "N2": app.preparar_pacote("Dinâmica", "Física", 2, "carlos@exemplo.com", 2, publicado),
        "rascunho": app.preparar_pacote("Rascunho", "Física", 2, "carlos@exemplo.com", 1),
    }


def entrar(app: App, janela: JanelaPrincipal, email: str) -> TelaPacotesDoAluno:
    app.entrar(janela, email, SENHA_DOS_ALUNOS)
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    abas.setCurrentWidget(abas.pacotes)
    return abas.pacotes


def escolher_na_vitrine(tela: TelaPacotesDoAluno, titulo: str) -> None:
    titulos = [linha[1] for linha in linhas(tela.vitrine)]
    tela.vitrine.selectRow(titulos.index(titulo))


def test_r15_r31_ana_no_n2_ve_os_publicados_com_o_n2_em_destaque(app: App) -> None:
    preparar_vitrine(app)
    app.preparar_aluno("ana@exemplo.com", {"Física": 2})

    tela = entrar(app, app.abrir(), "ana@exemplo.com")

    assert linhas(tela.vitrine) == [
        ["★ seu nível", "Dinâmica", "Física", "N2", "2", "R$ 120,00", "—"],
        ["", "Cinemática", "Física", "N1", "3", "R$ 120,00", "—"],
        ["", "Ondas", "Física", "N3", "2", "R$ 120,00", "—"],
    ]


def test_r31_bruno_sem_nivel_ve_todos_sem_destaque(app: App) -> None:
    preparar_vitrine(app)
    app.preparar_aluno("bruno@exemplo.com")

    tela = entrar(app, app.abrir(), "bruno@exemplo.com")

    assert [linha[:2] for linha in linhas(tela.vitrine)] == [
        ["", "Cinemática"],
        ["", "Dinâmica"],
        ["", "Ondas"],
    ]


def test_r12_r31_bruno_compra_sem_nivelamento_e_tem_acesso_por_12_meses(app: App) -> None:
    preparar_vitrine(app)
    app.preparar_aluno("bruno@exemplo.com")
    tela = entrar(app, app.abrir(), "bruno@exemplo.com")

    escolher_na_vitrine(tela, "Ondas")
    app.clicar(tela.botao_comprar)

    assert tela.mensagem.text() == (
        "Você comprou Ondas por R$ 120,00. O acesso vai até 23/11/2027."
    )
    assert linhas(tela.vitrine)[2][6] == "até 23/11/2027"
    assert linhas(tela.comprados) == [["Ondas", "Física", "N3", "0 de 2", "até 23/11/2027"]]


def test_r12_com_acesso_ativo_a_compra_e_recusada(app: App) -> None:
    pacotes = preparar_vitrine(app)
    bruno = app.preparar_aluno("bruno@exemplo.com")
    app.preparar_compra(bruno, pacotes["N1"])
    tela = entrar(app, app.abrir(), "bruno@exemplo.com")

    escolher_na_vitrine(tela, "Cinemática")
    app.clicar(tela.botao_comprar)

    assert tela.mensagem.text() == "Você já tem acesso a este pacote até 23/11/2027."
    assert len(linhas(tela.comprados)) == 1


def test_r61_r62_ana_assiste_no_navegador_e_conclui_a_aula(app: App) -> None:
    pacotes = preparar_vitrine(app)
    ana = app.preparar_aluno("ana@exemplo.com", {"Física": 1})
    app.preparar_compra(ana, pacotes["N1"])
    tela = entrar(app, app.abrir(), "ana@exemplo.com")
    abertos: list[str] = []
    tela.abrir_link = abertos.append
    tela.comprados.selectRow(0)
    tela.aulas.selectRow(1)

    app.clicar(tela.botao_assistir)
    app.clicar(tela.botao_concluir)

    assert abertos == ["https://www.youtube.com/watch?v=aula0000002"]
    assert tela.mensagem.text() == "2ª aula marcada como concluída."
    assert linhas(tela.comprados)[0][3] == "1 de 3"
    assert linhas(tela.aulas)[1] == ["2", "Aula 2", "concluída em 23/11/2026"]


def test_r62_a_aula_concluida_nao_e_marcada_de_novo(app: App) -> None:
    pacotes = preparar_vitrine(app)
    ana = app.preparar_aluno("ana@exemplo.com")
    app.preparar_compra(ana, pacotes["N1"])
    tela = entrar(app, app.abrir(), "ana@exemplo.com")
    tela.comprados.selectRow(0)
    tela.aulas.selectRow(0)
    app.clicar(tela.botao_concluir)

    tela.aulas.selectRow(0)
    app.clicar(tela.botao_concluir)

    assert tela.mensagem.text() == "Você já concluiu a 1ª aula em 23/11/2026."


def test_r12_r61_com_o_acesso_vencido_a_aula_nao_abre(app: App) -> None:
    pacotes = preparar_vitrine(app)
    ana = app.preparar_aluno("ana@exemplo.com")
    app.preparar_compra(ana, pacotes["N1"])
    # Da segunda 23/11/2026 até 24/11/2027: o acesso venceu ontem.
    app.relogio.avancar(days=366)
    tela = entrar(app, app.abrir(), "ana@exemplo.com")
    abertos: list[str] = []
    tela.abrir_link = abertos.append
    tela.comprados.selectRow(0)
    tela.aulas.selectRow(0)

    app.clicar(tela.botao_assistir)

    assert tela.mensagem.text() == "Seu acesso a este pacote venceu em 23/11/2027."
    assert abertos == []
    assert linhas(tela.comprados)[0][4] == "venceu em 23/11/2027"


def test_r12_o_pacote_arquivado_sai_da_vitrine_e_continua_para_quem_comprou(app: App) -> None:
    pacotes = preparar_vitrine(app)
    ana = app.preparar_aluno("ana@exemplo.com")
    app.preparar_compra(ana, pacotes["N1"])
    app.arquivar_pacote(pacotes["N1"])
    tela = entrar(app, app.abrir(), "ana@exemplo.com")
    abertos: list[str] = []
    tela.abrir_link = abertos.append
    tela.comprados.selectRow(0)
    tela.aulas.selectRow(0)

    app.clicar(tela.botao_assistir)

    assert "Cinemática" not in [linha[1] for linha in linhas(tela.vitrine)]
    assert linhas(tela.comprados)[0][0] == "Cinemática"
    assert abertos == ["https://www.youtube.com/watch?v=aula0000001"]


def test_sem_pacotes_a_vitrine_mostra_o_aviso(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_aluno("ana@exemplo.com")

    tela = entrar(app, app.abrir(), "ana@exemplo.com")

    assert tela.mensagem.text() == "Nenhum pacote à venda ainda."
