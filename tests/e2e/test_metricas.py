"""Aba "Métricas" do ADM (H36): a M1, a M2 e a M3 do mês escolhido (R64 a R67). O relógio do app
começa na segunda, 23/11/2026, às 14h, e os nivelamentos são desse dia."""

from plataforma.janela_principal import AreaDoAdm, JanelaPrincipal
from plataforma.modules.catalogo.domain.pacote import EstadoPacote
from plataforma.modules.metricas.ui.telas import TelaMetricas
from tests.e2e.conftest import EMAIL_DO_ADM, SENHA_DO_ADM, App, escolher, linhas


def entrar_como_adm(app: App, janela: JanelaPrincipal) -> TelaMetricas:
    app.entrar(janela, EMAIL_DO_ADM, SENHA_DO_ADM)
    area = janela.tela_inicio.area
    assert isinstance(area, AreaDoAdm)
    area.setCurrentWidget(area.tela_metricas)
    return area.tela_metricas


def test_sem_nivelamentos_no_mes_as_metricas_ficam_sem_valor(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)

    tela = entrar_como_adm(app, app.abrir())

    assert (tela.mes.currentText(), tela.ano.value()) == ("novembro", 2026)
    assert linhas(tela.tabela) == [
        [
            "M1 · taxa de progressão",
            "—",
            "30% ou mais em 6 meses",
            "Nenhum nivelamento concluído no mês.",
        ],
        [
            "M2 · continuidade na trilha",
            "—",
            "50% ou mais na 4ª semana",
            "Nenhum nivelado do mês tem 4 semanas ainda.",
        ],
        [
            "M3 · tempo até estudar no nível certo",
            "—",
            "mediana de até 3 dias",
            "Nenhum nivelado do mês estudou no nível recebido ainda.",
        ],
    ]


def test_m1_m2_m3_de_4_alunos_nivelados_em_novembro(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")
    pacote = app.preparar_pacote(
        "Dinâmica", "Física", 2, "carlos@exemplo.com", 1, EstadoPacote.PUBLICADO
    )
    ana, bruno, *_ = [
        app.preparar_aluno(f"{nome}@exemplo.com", {"Física": 2})
        for nome in ("ana", "bruno", "carla", "davi")
    ]
    for aluno in (ana, bruno):
        app.preparar_compra(aluno, pacote)
    for nome in ("ana", "bruno", "carla", "davi"):
        app.preparar_nivelamento(f"{nome}@exemplo.com", "Física", 2)
    # A Ana estuda no N2 no 2º dia depois do nivelamento, e o Bruno, na 4ª semana, no 22º.
    app.relogio.avancar(days=2)
    app.preparar_aula_concluida(ana, pacote)
    app.relogio.avancar(days=20)
    app.preparar_aula_concluida(bruno, pacote)
    # No 30º dia, a Ana é promovida.
    app.relogio.avancar(days=8)
    app.preparar_promocao(ana, "Física")

    tela = entrar_como_adm(app, app.abrir())
    escolher(tela.mes, "novembro")
    tela.ano.setValue(2026)
    app.clicar(tela.botao_ver)

    assert [linha[1] for linha in linhas(tela.tabela)] == ["25%", "25%", "12 dias"]
    assert [linha[3] for linha in linhas(tela.tabela)] == [
        "1 de 4 nivelados promovidos em até 6 meses; 3 ainda dentro dos 6 meses.",
        "1 de 4 nivelados há pelo menos 4 semanas estudaram na 4ª semana.",
        "Mediana de 2 alunos que já estudaram no nível recebido.",
    ]


def test_r64_outro_mes_nao_tem_os_nivelamentos_de_novembro(app: App) -> None:
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_aluno("ana@exemplo.com")
    app.preparar_nivelamento("ana@exemplo.com", "Física", 2)

    tela = entrar_como_adm(app, app.abrir())
    escolher(tela.mes, "dezembro")
    app.clicar(tela.botao_ver)

    assert linhas(tela.tabela)[0][1:4:2] == ["—", "Nenhum nivelamento concluído no mês."]
    assert tela.mensagem.text() == "Métricas dos nivelamentos concluídos em dezembro de 2026."
