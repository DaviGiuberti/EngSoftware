"""Pacote gravado (H25, H26, H34, H35): o fluxo rascunho → em revisão → publicado → arquivado
(R15), a devolução (R38), a matéria e o nível fixos (R56), a revisão com pelo menos 1 aula e sem
edição (R57), as aulas do YouTube que o publicado não perde (R58) e o preço (R59)."""

import pytest

from plataforma.modules.catalogo.domain.pacote import (
    AulaFixa,
    AulaGravada,
    AulaNaoEncontrada,
    AulaNova,
    EstadoErrado,
    EstadoPacote,
    LinkInvalido,
    NivelForaDaMateria,
    Pacote,
    PacoteNaoEditavel,
    PacoteNovo,
    PacoteSemAulas,
    PrecoAntesDePublicar,
    PrecoInvalido,
    TituloVazio,
    adicionar_aula,
    arquivar,
    corrigir_aula,
    devolver,
    enviar_para_revisao,
    mudar_preco,
    mudar_titulo,
    nova_aula,
    novo_pacote,
    publicar,
    publicar_de_novo,
    remover_aula,
)

FISICA = 1
CARLOS = 10
LINK_1 = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
LINK_2 = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
LINK_3 = "https://www.youtube.com/watch?v=bbbbbbbbbbb"
AULA_1 = AulaGravada(1, "Velocidade média", LINK_1)
AULA_2 = AulaGravada(2, "Aceleração", LINK_2)
AULA_3 = AulaGravada(3, "Queda livre", LINK_3)

RASCUNHO = Pacote(
    id=1,
    titulo="Cinemática",
    materia_id=FISICA,
    nivel=1,
    professor_id=CARLOS,
    estado=EstadoPacote.RASCUNHO,
)
COM_1_AULA = Pacote(1, "Cinemática", FISICA, 1, CARLOS, EstadoPacote.RASCUNHO, (AULA_1,))
EM_REVISAO = Pacote(1, "Cinemática", FISICA, 1, CARLOS, EstadoPacote.EM_REVISAO, (AULA_1,))
PUBLICADO = Pacote(
    1, "Cinemática", FISICA, 1, CARLOS, EstadoPacote.PUBLICADO, (AULA_1, AULA_2, AULA_3), 12000
)
ARQUIVADO = Pacote(
    1, "Cinemática", FISICA, 1, CARLOS, EstadoPacote.ARQUIVADO, (AULA_1, AULA_2, AULA_3), 12000
)


def test_r15_pacote_novo_comeca_em_rascunho_sem_aulas_e_sem_preco() -> None:
    novo = novo_pacote("  Cinemática ", FISICA, 1, 3, "Física", CARLOS)

    assert novo == PacoteNovo("Cinemática", FISICA, 1, CARLOS)
    assert novo.estado == EstadoPacote.RASCUNHO


def test_pacote_sem_titulo_e_recusado() -> None:
    with pytest.raises(TituloVazio, match="Informe o título do pacote."):
        novo_pacote("  ", FISICA, 1, 3, "Física", CARLOS)


def test_r56_o_pacote_e_de_um_dos_niveis_da_materia() -> None:
    with pytest.raises(NivelForaDaMateria, match="Física tem os níveis N1 a N3."):
        novo_pacote("Cinemática", FISICA, 4, 3, "Física", CARLOS)
    with pytest.raises(NivelForaDaMateria, match="Lógica só tem o nível N1."):
        novo_pacote("Cinemática", FISICA, 0, 1, "Lógica", CARLOS)


def test_r15_r57_enviar_para_revisao_com_1_aula() -> None:
    assert enviar_para_revisao(COM_1_AULA) == EM_REVISAO


def test_r57_pacote_sem_aula_nao_vai_para_revisao() -> None:
    with pytest.raises(
        PacoteSemAulas, match="Adicione pelo menos 1 aula antes de enviar o pacote para revisão."
    ):
        enviar_para_revisao(RASCUNHO)


def test_r15_so_o_rascunho_vai_para_revisao() -> None:
    with pytest.raises(
        EstadoErrado, match="Só o pacote em rascunho é enviado para revisão. Este está publicado."
    ):
        enviar_para_revisao(PUBLICADO)


def test_r15_r59_o_adm_define_o_preco_de_r_120_e_publica() -> None:
    publicado = publicar(EM_REVISAO, 12000)

    assert publicado.estado == EstadoPacote.PUBLICADO
    assert publicado.preco_em_centavos == 12000


def test_r15_so_pacote_em_revisao_e_publicado() -> None:
    with pytest.raises(
        EstadoErrado, match="Só o pacote em revisão é publicado. Este está em rascunho."
    ):
        publicar(COM_1_AULA, 12000)


def test_r59_o_preco_e_maior_que_zero() -> None:
    with pytest.raises(PrecoInvalido, match="O preço precisa ser maior que zero."):
        publicar(EM_REVISAO, 0)


def test_r38_o_adm_devolve_e_o_pacote_volta_para_rascunho() -> None:
    devolvido = devolver(EM_REVISAO)

    assert devolvido == COM_1_AULA
    assert adicionar_aula(devolvido, nova_aula("Aceleração", LINK_2)).aulas == (AULA_1, AULA_2)


def test_r38_so_pacote_em_revisao_e_devolvido() -> None:
    with pytest.raises(
        EstadoErrado, match="Só o pacote em revisão é devolvido. Este está publicado."
    ):
        devolver(PUBLICADO)


def test_r15_r59_o_adm_muda_o_preco_do_publicado_e_do_arquivado() -> None:
    assert mudar_preco(PUBLICADO, 10000).preco_em_centavos == 10000
    assert mudar_preco(ARQUIVADO, 10000).preco_em_centavos == 10000


def test_r59_o_preco_e_definido_ao_publicar() -> None:
    with pytest.raises(
        PrecoAntesDePublicar, match="O preço é definido ao publicar o pacote. Este está em revisão."
    ):
        mudar_preco(EM_REVISAO, 10000)


def test_r59_o_novo_preco_tambem_e_maior_que_zero() -> None:
    with pytest.raises(PrecoInvalido):
        mudar_preco(PUBLICADO, -100)


def test_r15_o_adm_arquiva_o_pacote_publicado() -> None:
    assert arquivar(PUBLICADO) == ARQUIVADO


def test_r15_so_o_publicado_e_arquivado() -> None:
    with pytest.raises(
        EstadoErrado, match="Só o pacote publicado é arquivado. Este está em revisão."
    ):
        arquivar(EM_REVISAO)


def test_r15_r59_o_arquivado_e_publicado_de_novo_com_o_preco_que_tinha() -> None:
    assert publicar_de_novo(ARQUIVADO) == PUBLICADO


def test_r15_so_o_arquivado_e_publicado_de_novo() -> None:
    with pytest.raises(
        EstadoErrado, match="Só o pacote arquivado é publicado de novo. Este está publicado."
    ):
        publicar_de_novo(PUBLICADO)


def test_r58_a_aula_e_um_video_do_youtube() -> None:
    assert nova_aula(" Velocidade média ", f" {LINK_1} ") == AulaNova("Velocidade média", LINK_1)


@pytest.mark.parametrize(
    "link",
    [
        "https://youtu.be/dQw4w9WgXcQ",
        "http://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ&t=30s",
        "https://www.youtube.com/watch?list=abc&v=dQw4w9WgXcQ",
        "youtu.be/dQw4w9WgXcQ?si=xyz",
    ],
)
def test_r58_os_jeitos_de_copiar_o_link_viram_o_mesmo_video(link: str) -> None:
    assert nova_aula("Velocidade média", link).link == LINK_1


@pytest.mark.parametrize(
    "link",
    [
        "https://vimeo.com/123",
        "https://www.youtube.com/watch?v=curto",
        "https://www.youtube.com/channel/dQw4w9WgXcQ",
        "https://youtu.be/",
        "https://youtube.com.golpe.com/watch?v=dQw4w9WgXcQ",
        "",
    ],
)
def test_r58_link_que_nao_e_video_do_youtube_e_recusado(link: str) -> None:
    with pytest.raises(
        LinkInvalido,
        match=r"O link precisa ser de um vídeo do YouTube, como https://www.youtube.com/watch\?v=",
    ):
        nova_aula("Velocidade média", link)


def test_aula_sem_titulo_e_recusada() -> None:
    with pytest.raises(TituloVazio, match="Informe o título da aula."):
        nova_aula(" ", LINK_1)


def test_r58_no_rascunho_o_professor_adiciona_corrige_e_remove_aulas() -> None:
    com_duas = adicionar_aula(COM_1_AULA, nova_aula("Aceleração", LINK_2))
    corrigido = corrigir_aula(com_duas, 1, nova_aula("Velocidade", LINK_3))
    removido = remover_aula(corrigido, 1)

    assert com_duas.aulas == (AULA_1, AULA_2)
    assert corrigido.aulas == (AulaGravada(1, "Velocidade", LINK_3), AULA_2)
    assert removido.aulas == (AulaGravada(1, "Aceleração", LINK_2),)


def test_r15_r58_no_publicado_o_professor_adiciona_e_corrige_sem_nova_revisao() -> None:
    com_quatro = adicionar_aula(PUBLICADO, nova_aula("Lançamento", LINK_1))
    corrigido = corrigir_aula(com_quatro, 2, nova_aula("Aceleração média", LINK_2))
    renomeado = mudar_titulo(corrigido, "Cinemática básica")

    assert com_quatro.estado == EstadoPacote.PUBLICADO
    assert [aula.numero for aula in com_quatro.aulas] == [1, 2, 3, 4]
    assert corrigido.aulas[1] == AulaGravada(2, "Aceleração média", LINK_2)
    assert (renomeado.titulo, renomeado.estado) == ("Cinemática básica", EstadoPacote.PUBLICADO)


def test_r58_o_pacote_publicado_nao_perde_aulas() -> None:
    with pytest.raises(
        AulaFixa,
        match="O pacote já foi publicado: as aulas não podem ser removidas, porque quem "
        "comprou perderia a aula.",
    ):
        remover_aula(PUBLICADO, 2)


def test_r57_em_revisao_o_professor_nao_edita() -> None:
    mensagem = "O pacote em revisão não pode ser editado: espere o ADM publicar ou devolver."
    with pytest.raises(PacoteNaoEditavel, match=mensagem):
        adicionar_aula(EM_REVISAO, nova_aula("Aceleração", LINK_2))
    with pytest.raises(PacoteNaoEditavel, match=mensagem):
        mudar_titulo(EM_REVISAO, "Cinemática básica")
    with pytest.raises(PacoteNaoEditavel, match=mensagem):
        corrigir_aula(EM_REVISAO, 1, nova_aula("Aceleração", LINK_2))
    with pytest.raises(PacoteNaoEditavel, match=mensagem):
        remover_aula(EM_REVISAO, 1)


def test_r57_o_pacote_arquivado_nao_e_editado() -> None:
    with pytest.raises(PacoteNaoEditavel, match="O pacote arquivado não pode ser editado."):
        adicionar_aula(ARQUIVADO, nova_aula("Lançamento", LINK_1))


def test_titulo_vazio_na_edicao_e_recusado() -> None:
    with pytest.raises(TituloVazio, match="Informe o título do pacote."):
        mudar_titulo(COM_1_AULA, "")


def test_aula_que_nao_existe_e_recusada() -> None:
    with pytest.raises(AulaNaoEncontrada, match="O pacote não tem a 2ª aula."):
        corrigir_aula(COM_1_AULA, 2, nova_aula("Aceleração", LINK_2))
    with pytest.raises(AulaNaoEncontrada, match="O pacote não tem a 0ª aula."):
        remover_aula(COM_1_AULA, 0)
