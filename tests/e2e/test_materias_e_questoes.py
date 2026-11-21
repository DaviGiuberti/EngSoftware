"""Telas do ADM (H27 e H28): cadastrar matérias e as questões do nivelamento."""

from PySide6.QtWidgets import QTableWidget

from plataforma.janela_principal import AreaDoAdm
from plataforma.modules.materias.ui.telas import TelaMaterias
from tests.e2e.conftest import App

ENUNCIADO = "Um carro anda 100 m em 25 s. Qual é a velocidade média?"
ALTERNATIVAS = ["2 m/s", "4 m/s", "6 m/s", "8 m/s", "10 m/s"]


def entrar_como_adm(app: App) -> AreaDoAdm:
    janela = app.abrir()
    app.criar_o_primeiro_adm(janela)
    area = janela.tela_inicio.area
    assert isinstance(area, AreaDoAdm)
    return area


def cadastrar_materia(
    app: App,
    tela: TelaMaterias,
    nome: str,
    niveis: int,
    notas_minimas: list[int],
    mensalidade_em_reais: float,
) -> None:
    app.digitar(tela.nome, nome)
    tela.niveis.setValue(niveis)
    for campo, nota_minima in zip(tela.notas_minimas, notas_minimas, strict=True):
        campo.setValue(nota_minima)
    tela.mensalidade.setValue(mensalidade_em_reais)
    app.clicar(tela.botao_cadastrar)


def linhas(tabela: QTableWidget) -> list[list[str]]:
    return [
        [tabela.item(linha, coluna).text() for coluna in range(tabela.columnCount())]
        for linha in range(tabela.rowCount())
    ]


def test_r40_r27_o_adm_cadastra_fisica_e_ve_as_faixas_e_a_mensalidade(app: App) -> None:
    tela = entrar_como_adm(app).tela_materias

    cadastrar_materia(app, tela, "Física", 3, [40, 70], 200.00)

    assert tela.mensagem.text() == "Matéria Física cadastrada."
    assert linhas(tela.tabela) == [
        ["Física", "3", "0–39% N1 · 40–69% N2 · 70–100% N3", "R$ 200,00"]
    ]


def test_r01_matematica_com_5_niveis_fica_com_as_faixas_do_n1_ao_n5(app: App) -> None:
    tela = entrar_como_adm(app).tela_materias

    cadastrar_materia(app, tela, "Matemática", 5, [20, 40, 60, 80], 250.00)

    assert linhas(tela.tabela) == [
        [
            "Matemática",
            "5",
            "0–19% N1 · 20–39% N2 · 40–59% N3 · 60–79% N4 · 80–100% N5",
            "R$ 250,00",
        ]
    ]


def test_r40_a_tela_pede_a_nota_minima_de_cada_nivel_a_partir_do_n2(app: App) -> None:
    tela = entrar_como_adm(app).tela_materias

    tela.niveis.setValue(5)

    assert len(tela.notas_minimas) == 4
    tela.niveis.setValue(2)
    assert len(tela.notas_minimas) == 1


def test_r40_nota_minima_fora_de_ordem_mostra_a_recusa_e_nao_cadastra(app: App) -> None:
    tela = entrar_como_adm(app).tela_materias

    cadastrar_materia(app, tela, "Física", 3, [70, 40], 200.00)

    assert tela.mensagem.text() == "A nota mínima do N3 precisa ser maior que a do N2."
    assert linhas(tela.tabela) == []


def test_sem_materia_a_aba_de_questoes_pede_uma_materia_antes(app: App) -> None:
    tela = entrar_como_adm(app).tela_questoes

    assert tela.mensagem.text() == "Cadastre uma matéria antes das questões."
    assert not tela.botao_cadastrar.isEnabled()


def test_o_adm_cadastra_uma_questao_de_fisica_e_ela_aparece_na_lista(app: App) -> None:
    area = entrar_como_adm(app)
    cadastrar_materia(app, area.tela_materias, "Física", 3, [40, 70], 200.00)
    tela = area.tela_questoes
    area.setCurrentWidget(tela)
    assert tela.materia.currentText() == "Física"

    app.digitar(tela.enunciado, ENUNCIADO)
    for campo, texto in zip(tela.alternativas, ALTERNATIVAS, strict=True):
        app.digitar(campo, texto)
    app.clicar(tela.corretas[1])
    app.clicar(tela.botao_cadastrar)

    assert tela.mensagem.text() == "Questão cadastrada no nivelamento de Física."
    assert [tela.lista.item(i).text() for i in range(tela.lista.count())] == [
        f"1. {ENUNCIADO} (correta: B)"
    ]
    assert tela.enunciado.toPlainText() == ""


def test_r41_questao_com_alternativa_em_branco_mostra_a_recusa(app: App) -> None:
    area = entrar_como_adm(app)
    cadastrar_materia(app, area.tela_materias, "Física", 3, [40, 70], 200.00)
    tela = area.tela_questoes
    area.setCurrentWidget(tela)

    app.digitar(tela.enunciado, ENUNCIADO)
    for campo, texto in zip(tela.alternativas[:4], ALTERNATIVAS[:4], strict=True):
        app.digitar(campo, texto)
    app.clicar(tela.corretas[1])
    app.clicar(tela.botao_cadastrar)

    assert tela.mensagem.text() == "A questão precisa ter 5 alternativas, de A a E."
    assert tela.lista.count() == 0


def test_o_aluno_nao_ve_as_telas_do_adm(app: App) -> None:
    janela = app.abrir()
    app.criar_o_primeiro_adm(janela)
    app.clicar(janela.tela_inicio.botao_sair)
    app.clicar(janela.tela_entrar.botao_cadastro)
    app.digitar(janela.tela_cadastro.email, "ana@exemplo.com")
    app.digitar(janela.tela_cadastro.senha, "abcd1234")

    app.clicar(janela.tela_cadastro.botao_cadastrar)

    assert janela.telas.currentWidget() is janela.tela_inicio
    assert not isinstance(janela.tela_inicio.area, AreaDoAdm)
