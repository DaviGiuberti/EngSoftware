"""Tela do ADM para cadastrar professores e habilitá-los por matéria (H29, R11)."""

from PySide6.QtWidgets import QComboBox, QTableWidget

from plataforma.janela_principal import AreaDoAdm, JanelaPrincipal
from plataforma.modules.identidade.ui.telas_do_adm import TelaProfessores
from tests.e2e.conftest import EMAIL_DO_ADM, SENHA_DO_ADM, App


def abrir_professores(app: App) -> tuple[JanelaPrincipal, AreaDoAdm, TelaProfessores]:
    """Abre o app, entra como ADM e vai para a aba de professores."""
    janela = app.abrir()
    if janela.telas.currentWidget() is janela.tela_primeiro_adm:
        app.criar_o_primeiro_adm(janela)
    else:
        app.entrar(janela, EMAIL_DO_ADM, SENHA_DO_ADM)
    area = janela.tela_inicio.area
    assert isinstance(area, AreaDoAdm)
    area.setCurrentWidget(area.tela_professores)
    return janela, area, area.tela_professores


def cadastrar_professor(app: App, tela: TelaProfessores, email: str, senha: str) -> None:
    app.digitar(tela.email, email)
    app.digitar(tela.senha, senha)
    app.clicar(tela.botao_cadastrar)


def escolher(combo: QComboBox, texto: str) -> None:
    indice = combo.findText(texto)
    assert indice >= 0, f"{texto} não está na lista"
    combo.setCurrentIndex(indice)


def linhas(tabela: QTableWidget) -> list[list[str]]:
    return [
        [tabela.item(linha, coluna).text() for coluna in range(tabela.columnCount())]
        for linha in range(tabela.rowCount())
    ]


def test_o_adm_cadastra_dora_e_ela_entra_com_o_perfil_de_professor(app: App) -> None:
    janela, _, tela = abrir_professores(app)

    cadastrar_professor(app, tela, "dora@exemplo.com", "abcd1234")

    assert tela.mensagem.text() == "Conta de professor criada para dora@exemplo.com."
    assert linhas(tela.tabela) == [["dora@exemplo.com", "nenhuma matéria"]]
    assert tela.senha.text() == ""
    app.clicar(janela.tela_inicio.botao_sair)
    app.entrar(janela, "dora@exemplo.com", "abcd1234")
    assert janela.tela_inicio.boas_vindas.text() == (
        "Você entrou como dora@exemplo.com (professor)."
    )


def test_rnf06_senha_curta_do_professor_mostra_a_recusa(app: App) -> None:
    _, _, tela = abrir_professores(app)

    cadastrar_professor(app, tela, "dora@exemplo.com", "abc1234")

    assert tela.mensagem.text() == "A senha precisa ter pelo menos 8 caracteres."
    assert linhas(tela.tabela) == []


def test_r11_o_adm_habilita_carlos_em_fisica_e_ve_a_habilitacao_na_tabela(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_materia("Matemática", [20, 40, 60, 80], 0)
    _, _, tela = abrir_professores(app)
    cadastrar_professor(app, tela, "carlos@exemplo.com", "abcd1234")
    escolher(tela.materia, "Física")

    app.clicar(tela.botao_habilitar)

    assert tela.mensagem.text() == (
        "carlos@exemplo.com pode dar aula de Física, em todos os níveis."
    )
    assert linhas(tela.tabela) == [["carlos@exemplo.com", "Física"]]
    app.clicar(tela.botao_habilitar)
    assert tela.mensagem.text() == "carlos@exemplo.com já tem habilitação em Física."


def test_a_materia_cadastrada_na_aba_de_materias_ja_aparece_para_habilitar(app: App) -> None:
    _, area, tela = abrir_professores(app)
    assert not tela.botao_habilitar.isEnabled()
    materias = area.tela_materias
    app.digitar(materias.nome, "Física")
    materias.mensalidade.setValue(200.00)

    app.clicar(materias.botao_cadastrar)
    cadastrar_professor(app, tela, "carlos@exemplo.com", "abcd1234")

    assert [tela.materia.itemText(i) for i in range(tela.materia.count())] == ["Física"]
    assert tela.professor.currentText() == "carlos@exemplo.com"
    assert tela.botao_habilitar.isEnabled()
