"""Reembolso na aba "Pacotes" do aluno (H17): até as 23h59 do 7º dia depois da compra (R13), ele
encerra o acesso, apaga as aulas concluídas e tira o pacote de "Meus pacotes" (R63). O relógio do
app começa na segunda, 23/11/2026, às 14h."""

from plataforma.janela_principal import AbasDoAluno, JanelaPrincipal
from plataforma.modules.catalogo.domain.pacote import EstadoPacote
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.vendas.ui.telas_do_aluno import TelaPacotesDoAluno
from tests.e2e.conftest import SENHA_DOS_ALUNOS, App, linhas


def preparar_compra_da_ana(app: App) -> tuple[Usuario, int]:
    """Física, Carlos e o pacote Cinemática, de 2 aulas, comprado pela Ana em 23/11/2026."""
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    pacote_id = app.preparar_pacote(
        "Cinemática", "Física", 1, "carlos@exemplo.com", 2, EstadoPacote.PUBLICADO
    )
    ana = app.preparar_aluno("ana@exemplo.com")
    app.preparar_compra(ana, pacote_id)
    return ana, pacote_id


def entrar_como_ana(app: App, janela: JanelaPrincipal) -> TelaPacotesDoAluno:
    app.entrar(janela, "ana@exemplo.com", SENHA_DOS_ALUNOS)
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    abas.setCurrentWidget(abas.pacotes)
    abas.pacotes.comprados.selectRow(0)
    return abas.pacotes


def test_r13_r63_ana_pede_reembolso_e_o_pacote_sai_de_meus_pacotes(app: App) -> None:
    preparar_compra_da_ana(app)
    # Até 30/11/2026 às 23h59, o 7º dia depois da compra.
    app.relogio.avancar(days=7, hours=9, minutes=59)
    tela = entrar_como_ana(app, app.abrir())
    tela.aulas.selectRow(0)
    app.clicar(tela.botao_concluir)

    app.clicar(tela.botao_reembolso)

    assert tela.mensagem.text() == (
        "Reembolso de Cinemática aceito: R$ 120,00 devolvidos. O acesso foi encerrado."
    )
    assert linhas(tela.comprados) == []
    assert linhas(tela.vitrine)[0][6] == "—"


def test_r13_depois_do_7o_dia_o_reembolso_e_recusado(app: App) -> None:
    preparar_compra_da_ana(app)
    # 01/12/2026 à 0h: o 8º dia depois da compra.
    app.relogio.avancar(days=7, hours=10)
    tela = entrar_como_ana(app, app.abrir())

    app.clicar(tela.botao_reembolso)

    assert tela.mensagem.text() == (
        "O reembolso só pode ser pedido até as 23h59 de 30/11/2026, o 7º dia depois da compra."
    )
    assert linhas(tela.comprados)[0][4] == "até 23/11/2027"


def test_r13_a_recompra_depois_do_reembolso_nao_tem_reembolso(app: App) -> None:
    ana, pacote_id = preparar_compra_da_ana(app)
    app.preparar_reembolso(ana, pacote_id)
    app.relogio.avancar(days=1)
    app.preparar_compra(ana, pacote_id)
    tela = entrar_como_ana(app, app.abrir())

    app.clicar(tela.botao_reembolso)

    assert tela.mensagem.text() == (
        "Esta compra foi feita depois de um reembolso do mesmo pacote e não dá direito a "
        "reembolso."
    )
    assert linhas(tela.comprados)[0][0] == "Cinemática"
