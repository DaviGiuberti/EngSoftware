"""Telas dos pacotes gravados (H25, H26, H34, H35): o professor cria, edita e envia para revisão
em "Meus pacotes", e o ADM publica com o preço, devolve, arquiva e publica de novo em "Pacotes"."""

from plataforma.janela_principal import AbasDoProfessor, AreaDoAdm, JanelaPrincipal
from plataforma.modules.catalogo.domain.pacote import EstadoPacote
from plataforma.modules.catalogo.ui.telas_do_adm import TelaPacotes
from plataforma.modules.catalogo.ui.telas_do_professor import TelaMeusPacotes
from tests.e2e.conftest import (
    EMAIL_DO_ADM,
    SENHA_DO_ADM,
    SENHA_DOS_PROFESSORES,
    App,
    escolher,
    linhas,
)

LINK = "https://youtu.be/dQw4w9WgXcQ"
LINK_GRAVADO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def preparar_escola(app: App) -> None:
    """Física e Matemática, Carlos habilitado só em Física."""
    app.preparar_materia("Física", [40, 70], 0)
    app.preparar_materia("Matemática", [20, 40, 60, 80], 0)
    app.preparar_professor("carlos@exemplo.com", "Física")


def entrar_como_carlos(app: App, janela: JanelaPrincipal) -> TelaMeusPacotes:
    app.entrar(janela, "carlos@exemplo.com", SENHA_DOS_PROFESSORES)
    abas = janela.tela_inicio.area
    assert isinstance(abas, AbasDoProfessor)
    abas.setCurrentWidget(abas.pacotes)
    return abas.pacotes


def entrar_como_adm(app: App, janela: JanelaPrincipal) -> TelaPacotes:
    app.entrar(janela, EMAIL_DO_ADM, SENHA_DO_ADM)
    area = janela.tela_inicio.area
    assert isinstance(area, AreaDoAdm)
    area.setCurrentWidget(area.tela_pacotes)
    area.tela_pacotes.tabela.selectRow(0)
    return area.tela_pacotes


def test_r15_carlos_cria_o_pacote_cinematica_em_rascunho(app: App) -> None:
    preparar_escola(app)
    tela = entrar_como_carlos(app, app.abrir())

    app.digitar(tela.titulo, "Cinemática")
    escolher(tela.materia, "Física")
    escolher(tela.nivel, "N1")
    app.clicar(tela.botao_criar)

    assert tela.mensagem.text() == "Pacote Cinemática criado em rascunho."
    assert linhas(tela.tabela) == [["Cinemática", "Física", "N1", "0", "em rascunho", "—"]]


def test_r56_carlos_so_cria_pacote_de_fisica(app: App) -> None:
    preparar_escola(app)
    tela = entrar_como_carlos(app, app.abrir())

    assert [tela.materia.itemText(i) for i in range(tela.materia.count())] == ["Física"]
    assert [tela.nivel.itemText(i) for i in range(tela.nivel.count())] == ["N1", "N2", "N3"]


def test_r15_r57_carlos_adiciona_uma_aula_e_envia_para_revisao(app: App) -> None:
    preparar_escola(app)
    app.preparar_pacote("Cinemática", "Física", 1, "carlos@exemplo.com")
    tela = entrar_como_carlos(app, app.abrir())
    tela.tabela.selectRow(0)

    app.digitar(tela.titulo_da_aula, "Velocidade média")
    app.digitar(tela.link_da_aula, LINK)
    app.clicar(tela.botao_adicionar_aula)

    assert tela.mensagem.text() == "1ª aula adicionada."
    assert linhas(tela.aulas) == [["1", "Velocidade média", LINK_GRAVADO]]
    app.clicar(tela.botao_enviar)
    assert tela.mensagem.text() == "Cinemática enviado para revisão. O ADM publica ou devolve."
    assert linhas(tela.tabela)[0][4] == "em revisão"


def test_r58_link_que_nao_e_do_youtube_mostra_a_recusa(app: App) -> None:
    preparar_escola(app)
    app.preparar_pacote("Cinemática", "Física", 1, "carlos@exemplo.com")
    tela = entrar_como_carlos(app, app.abrir())
    tela.tabela.selectRow(0)

    app.digitar(tela.titulo_da_aula, "Velocidade média")
    app.digitar(tela.link_da_aula, "https://vimeo.com/123")
    app.clicar(tela.botao_adicionar_aula)

    assert tela.mensagem.text().startswith("O link precisa ser de um vídeo do YouTube")
    assert linhas(tela.aulas) == []


def test_r57_sem_aula_o_pacote_nao_vai_para_revisao(app: App) -> None:
    preparar_escola(app)
    app.preparar_pacote("Cinemática", "Física", 1, "carlos@exemplo.com")
    tela = entrar_como_carlos(app, app.abrir())
    tela.tabela.selectRow(0)

    app.clicar(tela.botao_enviar)

    assert tela.mensagem.text() == (
        "Adicione pelo menos 1 aula antes de enviar o pacote para revisão."
    )
    assert linhas(tela.tabela)[0][4] == "em rascunho"


def test_r58_no_rascunho_carlos_corrige_e_remove_a_aula_escolhida(app: App) -> None:
    preparar_escola(app)
    app.preparar_pacote("Cinemática", "Física", 1, "carlos@exemplo.com", aulas=2)
    tela = entrar_como_carlos(app, app.abrir())
    tela.tabela.selectRow(0)

    tela.aulas.selectRow(1)
    assert tela.titulo_da_aula.text() == "Aula 2"
    app.digitar(tela.titulo_da_aula, "Aceleração")
    app.clicar(tela.botao_corrigir_aula)
    assert tela.mensagem.text() == "2ª aula corrigida."
    tela.aulas.selectRow(0)
    app.clicar(tela.botao_remover_aula)

    assert tela.mensagem.text() == "1ª aula removida."
    assert [linha[:2] for linha in linhas(tela.aulas)] == [["1", "Aceleração"]]


def test_r15_r58_no_publicado_carlos_muda_o_titulo_mas_nao_remove_aula(app: App) -> None:
    preparar_escola(app)
    app.preparar_pacote(
        "Cinemática", "Física", 1, "carlos@exemplo.com", aulas=2, estado=EstadoPacote.PUBLICADO
    )
    tela = entrar_como_carlos(app, app.abrir())
    tela.tabela.selectRow(0)

    app.digitar(tela.titulo_escolhido, "Cinemática básica")
    app.clicar(tela.botao_mudar_titulo)
    assert tela.mensagem.text() == "Título mudado para Cinemática básica."
    tela.aulas.selectRow(0)
    app.clicar(tela.botao_remover_aula)

    assert tela.mensagem.text().startswith("O pacote já foi publicado")
    assert linhas(tela.tabela) == [
        ["Cinemática básica", "Física", "N1", "2", "publicado", "R$ 120,00"]
    ]


def test_r15_o_adm_define_o_preco_de_r_120_e_publica(app: App) -> None:
    preparar_escola(app)
    app.preparar_pacote(
        "Cinemática", "Física", 1, "carlos@exemplo.com", aulas=1, estado=EstadoPacote.EM_REVISAO
    )
    tela = entrar_como_adm(app, app.abrir())
    assert linhas(tela.aulas) == [["1", "Aula 1", "https://www.youtube.com/watch?v=aula0000001"]]

    tela.preco.setValue(120.00)
    app.clicar(tela.botao_publicar)

    assert tela.mensagem.text() == "Cinemática publicado por R$ 120,00."
    assert linhas(tela.tabela) == [
        ["Cinemática", "Física", "N1", "carlos@exemplo.com", "1", "publicado", "R$ 120,00"]
    ]


def test_r38_o_adm_devolve_o_pacote_para_rascunho(app: App) -> None:
    preparar_escola(app)
    app.preparar_pacote(
        "Cinemática", "Física", 1, "carlos@exemplo.com", aulas=1, estado=EstadoPacote.EM_REVISAO
    )
    tela = entrar_como_adm(app, app.abrir())

    app.clicar(tela.botao_devolver)

    assert tela.mensagem.text() == "Cinemática devolvido ao professor, em rascunho."
    assert linhas(tela.tabela)[0][5] == "em rascunho"


def test_r15_o_adm_nao_publica_um_rascunho(app: App) -> None:
    preparar_escola(app)
    app.preparar_pacote("Cinemática", "Física", 1, "carlos@exemplo.com", aulas=1)
    tela = entrar_como_adm(app, app.abrir())

    tela.preco.setValue(120.00)
    app.clicar(tela.botao_publicar)

    assert tela.mensagem.text() == "Só o pacote em revisão é publicado. Este está em rascunho."
    assert linhas(tela.tabela)[0][5:] == ["em rascunho", "—"]


def test_r15_r59_o_adm_muda_o_preco_arquiva_e_publica_de_novo(app: App) -> None:
    preparar_escola(app)
    app.preparar_pacote(
        "Cinemática", "Física", 1, "carlos@exemplo.com", aulas=1, estado=EstadoPacote.PUBLICADO
    )
    tela = entrar_como_adm(app, app.abrir())
    assert tela.preco.value() == 120.00

    tela.preco.setValue(100.00)
    app.clicar(tela.botao_mudar_preco)
    assert tela.mensagem.text() == "Cinemática passa a custar R$ 100,00."
    app.clicar(tela.botao_arquivar)
    assert tela.mensagem.text() == (
        "Cinemática arquivado: saiu da vitrine, e quem comprou mantém o acesso."
    )
    assert linhas(tela.tabela)[0][5:] == ["arquivado", "R$ 100,00"]
    app.clicar(tela.botao_publicar_de_novo)

    assert tela.mensagem.text() == "Cinemática publicado de novo por R$ 100,00."
    assert linhas(tela.tabela)[0][5:] == ["publicado", "R$ 100,00"]


def test_sem_pacotes_o_adm_ve_o_aviso(app: App) -> None:
    preparar_escola(app)
    janela = app.abrir()

    tela = entrar_como_adm(app, janela)

    assert tela.mensagem.text() == (
        "Nenhum pacote ainda. Os professores criam os pacotes e os enviam para revisão."
    )
