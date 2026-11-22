"""Pacotes gravados com o banco SQLite (H25, H26, H34, H35): R15, R38, R56, R57, R58, R59,
RNF05, RNF07 e RNF08."""

import sqlite3
from dataclasses import dataclass

import pytest

from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.catalogo.application.casos_de_uso import (
    CasosDeUsoDoCatalogo,
    ConsultaDePacotes,
    ResumoDoPacote,
    montar_casos_de_uso,
)
from plataforma.modules.catalogo.domain.pacote import (
    AulaFixa,
    AulaGravada,
    EstadoErrado,
    EstadoPacote,
    LinkInvalido,
    NivelForaDaMateria,
    Pacote,
    PacoteNaoEditavel,
    PacoteNaoEncontrado,
    PacoteSemAulas,
    PrecoInvalido,
)
from plataforma.modules.catalogo.infra.repositorio_de_pacotes import RepositorioDePacotesSqlite
from plataforma.modules.identidade.application.casos_de_uso import (
    CadastrarProfessor,
    ConsultaDeProfessores,
    HabilitarProfessor,
)
from plataforma.modules.identidade.domain.autorizacao import AcessoNegado
from plataforma.modules.identidade.domain.professor import SemHabilitacao
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.identidade.infra.repositorio_de_professores import (
    RepositorioDeProfessoresSqlite,
)
from plataforma.modules.identidade.infra.repositorio_de_usuarios import (
    RepositorioDeUsuariosSqlite,
)
from plataforma.modules.materias.application.casos_de_uso import (
    CadastrarMateria,
    ConsultaDeMaterias,
)
from plataforma.modules.materias.domain.materia import Materia
from plataforma.modules.materias.infra.repositorio_de_materias import (
    RepositorioDeMateriasSqlite,
)

ADM = Usuario(id=1000, email="adm@exemplo.com", perfil=Perfil.ADM)
ANA = Usuario(id=2000, email="ana@exemplo.com", perfil=Perfil.ALUNO)
LINK_1 = "https://www.youtube.com/watch?v=aaaaaaaaaa1"
LINK_2 = "https://www.youtube.com/watch?v=aaaaaaaaaa2"
LINK_3 = "https://www.youtube.com/watch?v=aaaaaaaaaa3"


@dataclass(frozen=True)
class Escola:
    """Física e Matemática, Carlos habilitado em Física e Dora em Física e Matemática."""

    casos: CasosDeUsoDoCatalogo
    consulta: ConsultaDePacotes
    fisica: Materia
    matematica: Materia
    carlos: Usuario
    dora: Usuario


@pytest.fixture
def escola(conexao: sqlite3.Connection, em_transacao: Transacao) -> Escola:
    usuarios = RepositorioDeUsuariosSqlite(conexao)
    repositorio_de_professores = RepositorioDeProfessoresSqlite(conexao)
    materias = ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao))
    cadastrar_materia = CadastrarMateria(RepositorioDeMateriasSqlite(conexao), em_transacao)
    fisica = cadastrar_materia.executar(ADM, "Física", 3, [40, 70], 20000)
    matematica = cadastrar_materia.executar(ADM, "Matemática", 5, [20, 40, 60, 80], 25000)
    cadastrar_professor = CadastrarProfessor(usuarios, em_transacao)
    carlos = cadastrar_professor.executar(ADM, "carlos@exemplo.com", "abcd1234")
    dora = cadastrar_professor.executar(ADM, "dora@exemplo.com", "abcd1234")
    habilitar = HabilitarProfessor(repositorio_de_professores, materias, em_transacao)
    habilitar.executar(ADM, carlos.id, fisica.id)
    habilitar.executar(ADM, dora.id, fisica.id)
    habilitar.executar(ADM, dora.id, matematica.id)
    pacotes = RepositorioDePacotesSqlite(conexao)
    professores = ConsultaDeProfessores(repositorio_de_professores)
    return Escola(
        casos=montar_casos_de_uso(pacotes, materias, professores, em_transacao),
        consulta=ConsultaDePacotes(pacotes),
        fisica=fisica,
        matematica=matematica,
        carlos=carlos,
        dora=dora,
    )


def cinematica(escola: Escola, aulas: int = 0) -> Pacote:
    """O pacote "Cinemática", de Física, do N1, criado por Carlos, em rascunho."""
    casos = escola.casos
    pacote = casos.criar_pacote.executar(escola.carlos, "Cinemática", escola.fisica.id, 1)
    for numero, link in zip(range(1, aulas + 1), (LINK_1, LINK_2, LINK_3), strict=False):
        pacote = casos.adicionar_aula.executar(escola.carlos, pacote.id, f"Aula {numero}", link)
    return pacote


def em_revisao(escola: Escola, aulas: int = 1) -> Pacote:
    pacote = cinematica(escola, aulas)
    return escola.casos.enviar_para_revisao.executar(escola.carlos, pacote.id)


def publicado(escola: Escola, aulas: int = 1, preco: int = 12000) -> Pacote:
    pacote = em_revisao(escola, aulas)
    return escola.casos.publicar.executar(ADM, pacote.id, preco)


def arquivado(escola: Escola) -> Pacote:
    pacote = publicado(escola)
    return escola.casos.arquivar.executar(ADM, pacote.id)


# H25: criar pacote e enviar para revisão


def test_r15_pacote_novo_comeca_em_rascunho(escola: Escola) -> None:
    pacote = escola.casos.criar_pacote.executar(
        escola.carlos, "Cinemática", escola.fisica.id, 1
    )

    assert escola.consulta.obter(pacote.id) == Pacote(
        id=pacote.id,
        titulo="Cinemática",
        materia_id=escola.fisica.id,
        nivel=1,
        professor_id=escola.carlos.id,
        estado=EstadoPacote.RASCUNHO,
    )


def test_r15_r57_enviar_para_revisao(escola: Escola) -> None:
    pacote = cinematica(escola, aulas=1)

    escola.casos.enviar_para_revisao.executar(escola.carlos, pacote.id)

    assert escola.consulta.obter(pacote.id).estado == EstadoPacote.EM_REVISAO


def test_r57_pacote_sem_aula_nao_vai_para_revisao(escola: Escola) -> None:
    pacote = cinematica(escola)

    with pytest.raises(PacoteSemAulas):
        escola.casos.enviar_para_revisao.executar(escola.carlos, pacote.id)

    assert escola.consulta.obter(pacote.id).estado == EstadoPacote.RASCUNHO


def test_r15_o_professor_nao_define_preco(escola: Escola) -> None:
    pacote = cinematica(escola, aulas=1)

    with pytest.raises(AcessoNegado, match="Só o ADM pode mudar o preço do pacote."):
        escola.casos.mudar_preco.executar(escola.carlos, pacote.id, 12000)

    assert escola.consulta.obter(pacote.id).preco_em_centavos is None


def test_r15_o_professor_nao_publica(escola: Escola) -> None:
    pacote = em_revisao(escola)

    with pytest.raises(AcessoNegado, match="Só o ADM pode publicar pacote."):
        escola.casos.publicar.executar(escola.carlos, pacote.id, 12000)

    assert escola.consulta.obter(pacote.id).estado == EstadoPacote.EM_REVISAO


def test_r56_so_na_materia_em_que_o_professor_esta_habilitado(escola: Escola) -> None:
    with pytest.raises(
        SemHabilitacao, match="carlos@exemplo.com não tem habilitação em Matemática."
    ):
        escola.casos.criar_pacote.executar(
            escola.carlos, "Funções", escola.matematica.id, 1
        )

    assert escola.casos.ver_meus_pacotes.executar(escola.carlos).pacotes == []


def test_r56_o_pacote_e_de_um_nivel_da_materia(escola: Escola) -> None:
    with pytest.raises(NivelForaDaMateria, match="Física tem os níveis N1 a N3."):
        escola.casos.criar_pacote.executar(escola.carlos, "Cinemática", escola.fisica.id, 4)


def test_rnf07_so_o_professor_cria_pacote(escola: Escola) -> None:
    with pytest.raises(AcessoNegado, match="Só o professor pode criar pacote."):
        escola.casos.criar_pacote.executar(ADM, "Cinemática", escola.fisica.id, 1)


# H26: editar pacote publicado


def test_r15_edicao_sem_nova_revisao(escola: Escola) -> None:
    pacote = publicado(escola, aulas=1)

    escola.casos.adicionar_aula.executar(escola.carlos, pacote.id, "Aceleração", LINK_2)

    gravado = escola.consulta.obter(pacote.id)
    assert gravado.estado == EstadoPacote.PUBLICADO
    assert gravado.aulas == (
        AulaGravada(1, "Aula 1", LINK_1),
        AulaGravada(2, "Aceleração", LINK_2),
    )
    assert [p.aulas for p in escola.consulta.publicados()] == [gravado.aulas]


def test_r15_o_preco_continua_com_o_adm(escola: Escola) -> None:
    pacote = publicado(escola, preco=12000)

    with pytest.raises(AcessoNegado, match="Só o ADM pode mudar o preço do pacote."):
        escola.casos.mudar_preco.executar(escola.carlos, pacote.id, 9000)

    assert escola.consulta.obter(pacote.id).preco_em_centavos == 12000


def test_r58_o_pacote_publicado_nao_perde_aulas(escola: Escola) -> None:
    pacote = publicado(escola, aulas=3)

    with pytest.raises(AulaFixa):
        escola.casos.remover_aula.executar(escola.carlos, pacote.id, 2)

    assert len(escola.consulta.obter(pacote.id).aulas) == 3


def test_r58_a_aula_precisa_ser_um_video_do_youtube(escola: Escola) -> None:
    pacote = cinematica(escola)

    with pytest.raises(LinkInvalido):
        escola.casos.adicionar_aula.executar(
            escola.carlos, pacote.id, "Velocidade", "https://vimeo.com/123"
        )

    assert escola.consulta.obter(pacote.id).aulas == ()


def test_r57_em_revisao_o_professor_nao_edita(escola: Escola) -> None:
    pacote = em_revisao(escola)

    with pytest.raises(PacoteNaoEditavel):
        escola.casos.adicionar_aula.executar(escola.carlos, pacote.id, "Aceleração", LINK_2)

    assert len(escola.consulta.obter(pacote.id).aulas) == 1


def test_r58_no_rascunho_o_professor_corrige_e_remove_aulas_e_muda_o_titulo(
    escola: Escola,
) -> None:
    pacote = cinematica(escola, aulas=3)
    casos = escola.casos

    casos.corrigir_aula.executar(escola.carlos, pacote.id, 3, "Queda livre", LINK_1)
    casos.remover_aula.executar(escola.carlos, pacote.id, 1)
    casos.mudar_titulo.executar(escola.carlos, pacote.id, "Cinemática básica")

    gravado = escola.consulta.obter(pacote.id)
    assert gravado.titulo == "Cinemática básica"
    assert gravado.aulas == (
        AulaGravada(1, "Aula 2", LINK_2),
        AulaGravada(2, "Queda livre", LINK_1),
    )


def test_r56_so_o_professor_que_criou_o_pacote_o_edita(escola: Escola) -> None:
    pacote = publicado(escola)

    with pytest.raises(
        AcessoNegado, match="Só o professor que criou o pacote pode editá-lo."
    ):
        escola.casos.adicionar_aula.executar(escola.dora, pacote.id, "Aceleração", LINK_2)
    with pytest.raises(AcessoNegado):
        escola.casos.mudar_titulo.executar(escola.dora, pacote.id, "Da Dora")

    assert escola.consulta.obter(pacote.id).titulo == "Cinemática"


def test_r56_cada_professor_ve_so_os_pacotes_dele_e_cria_so_nas_suas_materias(
    escola: Escola,
) -> None:
    cinematica(escola)
    escola.casos.criar_pacote.executar(escola.dora, "Funções", escola.matematica.id, 2)

    do_carlos = escola.casos.ver_meus_pacotes.executar(escola.carlos)
    da_dora = escola.casos.ver_meus_pacotes.executar(escola.dora)

    assert [r.pacote.titulo for r in do_carlos.pacotes] == ["Cinemática"]
    assert [m.nome for m in do_carlos.materias] == ["Física"]
    assert [r.pacote.titulo for r in da_dora.pacotes] == ["Funções"]
    assert [m.nome for m in da_dora.materias] == ["Física", "Matemática"]


# H34: revisar e publicar pacote


def test_r15_o_adm_define_o_preco_e_publica(escola: Escola) -> None:
    pacote = em_revisao(escola)

    escola.casos.publicar.executar(ADM, pacote.id, 12000)

    [na_vitrine] = escola.consulta.publicados()
    assert (na_vitrine.id, na_vitrine.estado, na_vitrine.preco_em_centavos) == (
        pacote.id,
        EstadoPacote.PUBLICADO,
        12000,
    )


def test_r38_o_adm_devolve_e_carlos_edita_e_envia_de_novo(escola: Escola) -> None:
    pacote = em_revisao(escola)
    casos = escola.casos

    casos.devolver.executar(ADM, pacote.id)

    assert escola.consulta.obter(pacote.id).estado == EstadoPacote.RASCUNHO
    casos.adicionar_aula.executar(escola.carlos, pacote.id, "Aceleração", LINK_2)
    casos.enviar_para_revisao.executar(escola.carlos, pacote.id)
    assert escola.consulta.obter(pacote.id).estado == EstadoPacote.EM_REVISAO
    assert len(escola.consulta.obter(pacote.id).aulas) == 2


def test_r15_so_pacote_em_revisao_e_publicado(escola: Escola) -> None:
    pacote = cinematica(escola, aulas=1)

    with pytest.raises(EstadoErrado, match="Só o pacote em revisão é publicado."):
        escola.casos.publicar.executar(ADM, pacote.id, 12000)

    assert escola.consulta.obter(pacote.id).estado == EstadoPacote.RASCUNHO
    assert escola.consulta.publicados() == []


def test_r15_r59_o_adm_altera_o_preco(escola: Escola) -> None:
    pacote = publicado(escola, preco=12000)

    escola.casos.mudar_preco.executar(ADM, pacote.id, 10000)

    assert escola.consulta.obter(pacote.id).preco_em_centavos == 10000


def test_r59_o_preco_e_maior_que_zero(escola: Escola) -> None:
    pacote = em_revisao(escola)

    with pytest.raises(PrecoInvalido):
        escola.casos.publicar.executar(ADM, pacote.id, 0)

    assert escola.consulta.obter(pacote.id).estado == EstadoPacote.EM_REVISAO


def test_rnf07_o_aluno_nao_publica_nem_devolve(escola: Escola) -> None:
    pacote = em_revisao(escola)

    with pytest.raises(AcessoNegado, match="Só o ADM pode publicar pacote."):
        escola.casos.publicar.executar(ANA, pacote.id, 12000)
    with pytest.raises(AcessoNegado, match="Só o ADM pode devolver pacote."):
        escola.casos.devolver.executar(ANA, pacote.id)
    with pytest.raises(AcessoNegado, match="Só o ADM pode ver todos os pacotes."):
        escola.casos.ver_pacotes.executar(ANA)


def test_o_adm_ve_todos_os_pacotes_com_a_materia_e_o_professor(escola: Escola) -> None:
    primeiro = cinematica(escola)
    segundo = escola.casos.criar_pacote.executar(
        escola.dora, "Funções", escola.matematica.id, 2
    )

    assert escola.casos.ver_pacotes.executar(ADM) == [
        ResumoDoPacote(primeiro, "Física", "carlos@exemplo.com"),
        ResumoDoPacote(segundo, "Matemática", "dora@exemplo.com"),
    ]


# H35: arquivar e publicar de novo


def test_r15_pacote_arquivado_sai_da_vitrine(escola: Escola) -> None:
    pacote = publicado(escola)

    escola.casos.arquivar.executar(ADM, pacote.id)

    assert escola.consulta.obter(pacote.id).estado == EstadoPacote.ARQUIVADO
    assert escola.consulta.publicados() == []


def test_r15_r59_o_adm_publica_de_novo_o_arquivado_com_o_preco_que_tinha(
    escola: Escola,
) -> None:
    pacote = arquivado(escola)

    escola.casos.publicar_de_novo.executar(ADM, pacote.id)

    [na_vitrine] = escola.consulta.publicados()
    assert (na_vitrine.id, na_vitrine.preco_em_centavos) == (pacote.id, 12000)


def test_r59_o_adm_muda_o_preco_do_arquivado(escola: Escola) -> None:
    pacote = arquivado(escola)

    escola.casos.mudar_preco.executar(ADM, pacote.id, 9000)
    escola.casos.publicar_de_novo.executar(ADM, pacote.id)

    assert escola.consulta.obter(pacote.id).preco_em_centavos == 9000


def test_r57_o_pacote_arquivado_nao_e_editado(escola: Escola) -> None:
    pacote = arquivado(escola)

    with pytest.raises(PacoteNaoEditavel, match="O pacote arquivado não pode ser editado."):
        escola.casos.adicionar_aula.executar(escola.carlos, pacote.id, "Aceleração", LINK_2)


def test_rnf07_o_professor_nao_arquiva(escola: Escola) -> None:
    pacote = publicado(escola)

    with pytest.raises(AcessoNegado, match="Só o ADM pode arquivar pacote."):
        escola.casos.arquivar.executar(escola.carlos, pacote.id)
    with pytest.raises(AcessoNegado, match="Só o ADM pode publicar pacote de novo."):
        escola.casos.publicar_de_novo.executar(escola.carlos, pacote.id)


# Banco


def test_pacote_que_nao_existe_e_recusado(escola: Escola) -> None:
    with pytest.raises(PacoteNaoEncontrado, match="Pacote não encontrado."):
        escola.casos.enviar_para_revisao.executar(escola.carlos, 999)


def test_rnf08_titulo_com_aspas_e_ponto_e_virgula_volta_igual(escola: Escola) -> None:
    titulo = "Física'); DROP TABLE pacote; --"

    pacote = escola.casos.criar_pacote.executar(escola.carlos, titulo, escola.fisica.id, 1)
    escola.casos.adicionar_aula.executar(escola.carlos, pacote.id, titulo, LINK_1)

    gravado = escola.consulta.obter(pacote.id)
    assert (gravado.titulo, gravado.aulas[0].titulo) == (titulo, titulo)


def test_rnf05_erro_ao_gravar_as_aulas_nao_muda_o_pacote(
    escola: Escola, conexao: sqlite3.Connection
) -> None:
    pacote = cinematica(escola, aulas=1)
    # O pacote é gravado antes das aulas. O trigger faz a gravação das aulas falhar.
    conexao.execute(
        "CREATE TRIGGER falha_na_aula BEFORE UPDATE ON aula_gravada "
        "BEGIN SELECT RAISE(ABORT, 'falha forçada no teste'); END"
    )

    with pytest.raises(sqlite3.DatabaseError, match="falha forçada no teste"):
        escola.casos.corrigir_aula.executar(escola.carlos, pacote.id, 1, "Nova", LINK_2)
    with pytest.raises(sqlite3.DatabaseError):
        escola.casos.mudar_titulo.executar(escola.carlos, pacote.id, "Outro título")

    gravado = escola.consulta.obter(pacote.id)
    assert (gravado.titulo, gravado.aulas[0].titulo) == ("Cinemática", "Aula 1")
