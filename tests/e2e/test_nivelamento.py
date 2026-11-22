"""Telas do nivelamento (H01, H02, H03, H33): o aluno faz o teste e vê o nível, e o ADM abre
exceções."""

from PySide6.QtWidgets import QPushButton

from plataforma.janela_principal import AbasDoAluno, AreaDoAdm, JanelaPrincipal
from plataforma.modules.nivelamento.ui.telas_do_aluno import (
    AreaDoAluno,
    TelaDoNivelamento,
    TelaMeusNiveis,
)
from tests.e2e.conftest import App

# As questões preparadas têm a correta na B.
CORRETA = 1
ERRADA = 0


def entrar_como_ana(app: App, janela: JanelaPrincipal) -> AreaDoAluno:
    """Cadastra a Ana e devolve a aba "Meus níveis" da área dela."""
    app.cadastrar_aluno(janela, "ana@exemplo.com", "abcd1234")
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    return abas.nivelamento


def linhas(tela: TelaMeusNiveis) -> list[tuple[str, str, str]]:
    """Cada matéria como o aluno vê: nome, nível e o botão ou aviso da última coluna."""
    tabela = tela.tabela
    resultado = []
    for linha in range(tabela.rowCount()):
        botao = tabela.cellWidget(linha, 2)
        item = tabela.item(linha, 2)
        acao = botao.text() if isinstance(botao, QPushButton) else item.text() if item else ""
        resultado.append((tabela.item(linha, 0).text(), tabela.item(linha, 1).text(), acao))
    return resultado


def responder(app: App, teste: TelaDoNivelamento, posicoes: list[int]) -> None:
    """Marca uma alternativa em cada questão, a partir da atual, passando para a próxima."""
    for indice, posicao in enumerate(posicoes):
        app.clicar(teste.alternativas[posicao])
        if indice < len(posicoes) - 1:
            app.clicar(teste.botao_proxima)


def test_h03_o_aluno_ve_cada_materia_sem_nivel_e_a_opcao_de_fazer_o_nivelamento(
    app: App,
) -> None:
    app.preparar_materia("Física", [40, 70], 5)
    app.preparar_materia("Química", [40, 70], 0)

    area = entrar_como_ana(app, app.abrir())

    assert linhas(area.tela_meus_niveis) == [
        ("Física", "sem nível", "Fazer nivelamento"),
        ("Química", "sem nível", "Nivelamento ainda não disponível"),
    ]


def test_h01_o_aluno_faz_o_nivelamento_de_fisica_e_fica_no_n2(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 5)
    area = entrar_como_ana(app, app.abrir())

    app.clicar(area.tela_meus_niveis.botoes["Física"])
    teste = area.tela_do_nivelamento
    assert area.currentWidget() is teste
    assert teste.tempo.text() == "Tempo restante: 60:00"
    responder(app, teste, [CORRETA, CORRETA, ERRADA, ERRADA, ERRADA])
    app.clicar(teste.botao_entregar)

    assert teste.resultado.text() == (
        "Nivelamento de Física concluído. Nota: 40%. Seu nível em Física: N2."
    )
    app.clicar(teste.botao_voltar)
    assert linhas(area.tela_meus_niveis) == [("Física", "N2", "")]


def test_h02_o_aluno_sai_no_meio_e_continua_de_onde_parou(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 5)
    area = entrar_como_ana(app, app.abrir())
    app.clicar(area.tela_meus_niveis.botoes["Física"])
    teste = area.tela_do_nivelamento
    responder(app, teste, [CORRETA, ERRADA])

    app.clicar(teste.botao_sair)

    assert area.currentWidget() is area.tela_meus_niveis
    assert linhas(area.tela_meus_niveis) == [("Física", "sem nível", "Continuar nivelamento")]
    app.clicar(area.tela_meus_niveis.botoes["Física"])
    assert teste.progresso.text() == "Questão 3 de 5 · 2 respondidas"
    app.clicar(teste.botao_anterior)
    assert teste.alternativas[ERRADA].isChecked()


def test_h33_o_adm_da_mais_tempo_a_quem_esta_fazendo_o_nivelamento(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 5)
    janela = app.abrir()
    area = entrar_como_ana(app, janela)
    app.clicar(area.tela_meus_niveis.botoes["Física"])
    app.clicar(area.tela_do_nivelamento.botao_sair)
    app.clicar(janela.tela_inicio.botao_sair)
    app.entrar(janela, "adm@exemplo.com", "admin123")
    adm = janela.tela_inicio.area
    assert isinstance(adm, AreaDoAdm)
    excecoes = adm.tela_excecoes
    adm.setCurrentWidget(excecoes)
    app.digitar(excecoes.email, "ana@exemplo.com")
    excecoes.minutos.setValue(20)

    app.clicar(excecoes.botao_mais_tempo)

    assert excecoes.mensagem.text() == (
        "ana@exemplo.com passa a ter 80:00 no nivelamento de Física."
    )
    # Ana ainda está no primeiro nivelamento, então ainda não tem nível para refazer.
    app.clicar(excecoes.botao_refazer)
    assert excecoes.mensagem.text() == "Este aluno ainda não fez o nivelamento de Física."


def test_h33_o_adm_libera_refazer_e_o_aluno_ve_a_opcao_no_perfil(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 5)
    janela = app.abrir()
    area = entrar_como_ana(app, janela)
    app.clicar(area.tela_meus_niveis.botoes["Física"])
    app.clicar(area.tela_do_nivelamento.botao_entregar)
    app.clicar(area.tela_do_nivelamento.botao_voltar)
    app.clicar(janela.tela_inicio.botao_sair)
    app.entrar(janela, "adm@exemplo.com", "admin123")
    adm = janela.tela_inicio.area
    assert isinstance(adm, AreaDoAdm)
    adm.setCurrentWidget(adm.tela_excecoes)
    app.digitar(adm.tela_excecoes.email, "ana@exemplo.com")

    app.clicar(adm.tela_excecoes.botao_refazer)

    assert adm.tela_excecoes.mensagem.text() == (
        "ana@exemplo.com pode refazer o nivelamento de Física uma vez."
    )
    app.clicar(janela.tela_inicio.botao_sair)
    app.entrar(janela, "ana@exemplo.com", "abcd1234")
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoAluno)
    assert linhas(abas.nivelamento.tela_meus_niveis) == [("Física", "N1", "Refazer nivelamento")]
    # As abas do ADM que saiu não podem continuar desenhadas por baixo da tela da Ana.
    areas_do_adm = janela.tela_inicio.findChildren(AreaDoAdm)
    assert [area for area in areas_do_adm if area.isVisible()] == []
