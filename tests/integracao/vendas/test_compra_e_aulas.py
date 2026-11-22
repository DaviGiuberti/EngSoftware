"""Vitrine, compra e aulas gravadas com o banco SQLite (H14, H15, H16, H34, H35): R12, R15, R31,
R32, R59, R60, R61, R62 e RNF07."""

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.catalogo.application.aulas_do_aluno import (
    CasosDeUsoDoAluno,
    montar_casos_de_uso_do_aluno,
)
from plataforma.modules.catalogo.application.casos_de_uso import (
    CasosDeUsoDoCatalogo,
    ConsultaDePacotes,
    montar_casos_de_uso,
)
from plataforma.modules.catalogo.domain.aulas_do_aluno import (
    AcessoAoPacote,
    AulaJaConcluida,
    SemAcesso,
)
from plataforma.modules.catalogo.domain.pacote import Pacote
from plataforma.modules.catalogo.infra.repositorio_de_aulas_concluidas import (
    RepositorioDeAulasConcluidasSqlite,
)
from plataforma.modules.catalogo.infra.repositorio_de_pacotes import RepositorioDePacotesSqlite
from plataforma.modules.identidade.application.casos_de_uso import (
    CadastrarAluno,
    CadastrarProfessor,
    ConsultaDeProfessores,
    HabilitarProfessor,
)
from plataforma.modules.identidade.domain.autorizacao import AcessoNegado
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
from plataforma.modules.nivelamento.application.consulta_de_niveis import ConsultaDeNiveis
from plataforma.modules.nivelamento.domain.nivelamento import NivelDoAluno
from plataforma.modules.nivelamento.infra.repositorio_de_nivelamentos import (
    RepositorioDeNivelamentosSqlite,
)
from plataforma.modules.vendas.application.casos_de_uso import (
    CasosDeUsoDeVendas,
    ConsultaDeAcessos,
    montar_casos_de_uso_de_vendas,
)
from plataforma.modules.vendas.domain.compra import AcessoAtivo, ForaDeVenda
from plataforma.modules.vendas.infra.repositorio_de_compras import RepositorioDeComprasSqlite
from tests.integracao.conftest import RelogioDeTeste

ADM = Usuario(id=1000, email="adm@exemplo.com", perfil=Perfil.ADM)


def em(dia: int, mes: int, ano: int = 2027, hora: int = 15, minuto: int = 0) -> datetime:
    return datetime(ano, mes, dia, hora, minuto, tzinfo=BRASILIA)


@dataclass(frozen=True)
class Escola:
    """Física, Carlos habilitado nela, Ana e Bruno, e o relógio em 10/03/2027 às 15h."""

    catalogo: CasosDeUsoDoCatalogo
    aluno: CasosDeUsoDoAluno
    vendas: CasosDeUsoDeVendas
    consulta: ConsultaDePacotes
    niveis: ConsultaDeNiveis
    nivelamentos: RepositorioDeNivelamentosSqlite
    relogio: RelogioDeTeste
    fisica: Materia
    carlos: Usuario
    ana: Usuario
    bruno: Usuario

    def ir_para(self, quando: datetime) -> None:
        self.relogio.avancar(seconds=(quando - self.relogio.agora()).total_seconds())

    def pacote(self, titulo: str, nivel: int, aulas: int = 1, preco: int = 12000) -> Pacote:
        """Um pacote de Física do Carlos, publicado pelo ADM."""
        criado = self.catalogo.criar_pacote.executar(self.carlos, titulo, self.fisica.id, nivel)
        for numero in range(1, aulas + 1):
            self.catalogo.adicionar_aula.executar(
                self.carlos, criado.id, f"Aula {numero}", f"youtu.be/aula{numero:07d}"
            )
        self.catalogo.enviar_para_revisao.executar(self.carlos, criado.id)
        return self.catalogo.publicar.executar(ADM, criado.id, preco)

    def dar_nivel(self, aluno: Usuario, nivel: int) -> None:
        """Como se o aluno tivesse feito o nivelamento de Física."""
        self.nivelamentos.salvar_nivel(aluno.id, NivelDoAluno(self.fisica.id, nivel))


@pytest.fixture
def escola(conexao: sqlite3.Connection, em_transacao: Transacao) -> Escola:
    usuarios = RepositorioDeUsuariosSqlite(conexao)
    repositorio_de_professores = RepositorioDeProfessoresSqlite(conexao)
    materias = ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao))
    fisica = CadastrarMateria(RepositorioDeMateriasSqlite(conexao), em_transacao).executar(
        ADM, "Física", 3, [40, 70], 20000
    )
    carlos = CadastrarProfessor(usuarios, em_transacao).executar(
        ADM, "carlos@exemplo.com", "abcd1234"
    )
    HabilitarProfessor(repositorio_de_professores, materias, em_transacao).executar(
        ADM, carlos.id, fisica.id
    )
    cadastrar_aluno = CadastrarAluno(usuarios, em_transacao)
    ana = cadastrar_aluno.executar("ana@exemplo.com", "abcd1234")
    bruno = cadastrar_aluno.executar("bruno@exemplo.com", "abcd1234")
    relogio = RelogioDeTeste(em(10, 3))
    pacotes = RepositorioDePacotesSqlite(conexao)
    professores = ConsultaDeProfessores(repositorio_de_professores)
    consulta = ConsultaDePacotes(pacotes)
    compras = RepositorioDeComprasSqlite(conexao)
    nivelamentos = RepositorioDeNivelamentosSqlite(conexao)
    niveis = ConsultaDeNiveis(nivelamentos)
    return Escola(
        catalogo=montar_casos_de_uso(pacotes, materias, professores, em_transacao),
        aluno=montar_casos_de_uso_do_aluno(
            pacotes,
            RepositorioDeAulasConcluidasSqlite(conexao),
            materias,
            professores,
            niveis,
            ConsultaDeAcessos(compras),
            relogio,
            em_transacao,
        ),
        vendas=montar_casos_de_uso_de_vendas(compras, consulta, relogio, em_transacao),
        consulta=consulta,
        niveis=niveis,
        nivelamentos=nivelamentos,
        relogio=relogio,
        fisica=fisica,
        carlos=carlos,
        ana=ana,
        bruno=bruno,
    )


def titulos_da_vitrine(escola: Escola, aluno: Usuario) -> list[tuple[str, bool]]:
    return [
        (item.resumo.pacote.titulo, item.destaque)
        for item in escola.aluno.ver_vitrine.executar(aluno)
    ]


# H14: ver a vitrine de pacotes


def test_r15_so_pacotes_publicados_aparecem(escola: Escola) -> None:
    escola.catalogo.criar_pacote.executar(escola.carlos, "Rascunho", escola.fisica.id, 1)
    em_revisao = escola.catalogo.criar_pacote.executar(
        escola.carlos, "Em revisão", escola.fisica.id, 1
    )
    escola.catalogo.adicionar_aula.executar(
        escola.carlos, em_revisao.id, "Aula", "youtu.be/aula0000001"
    )
    escola.catalogo.enviar_para_revisao.executar(escola.carlos, em_revisao.id)
    escola.pacote("Publicado", 1)
    arquivado = escola.pacote("Arquivado", 1)
    escola.catalogo.arquivar.executar(ADM, arquivado.id)

    assert titulos_da_vitrine(escola, escola.ana) == [("Publicado", False)]


def test_r31_todos_os_niveis_aparecem_com_destaque_para_o_n2_da_ana(escola: Escola) -> None:
    escola.dar_nivel(escola.ana, 2)
    escola.pacote("Física N3", 3)
    escola.pacote("Física N1", 1)
    escola.pacote("Física N2", 2)

    assert titulos_da_vitrine(escola, escola.ana) == [
        ("Física N2", True),
        ("Física N1", False),
        ("Física N3", False),
    ]


def test_r31_aluno_sem_nivel_ve_todos_os_pacotes_sem_destaque(escola: Escola) -> None:
    escola.pacote("Física N1", 1)
    escola.pacote("Física N2", 2)

    assert titulos_da_vitrine(escola, escola.bruno) == [
        ("Física N1", False),
        ("Física N2", False),
    ]


def test_a_vitrine_mostra_o_acesso_de_quem_comprou(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1)
    escola.vendas.comprar.executar(escola.ana, pacote.id)

    [da_ana] = escola.aluno.ver_vitrine.executar(escola.ana)
    [do_bruno] = escola.aluno.ver_vitrine.executar(escola.bruno)

    assert da_ana.acesso == AcessoAoPacote(date(2028, 3, 10), ativo=True)
    assert do_bruno.acesso is None


# H15: comprar um pacote


def test_r31_compra_sem_nivelamento_da_acesso_ate_10_03_2028(escola: Escola) -> None:
    pacote = escola.pacote("Física N3", 3)

    feita = escola.vendas.comprar.executar(escola.bruno, pacote.id)

    assert feita.acesso_ate == date(2028, 3, 10)
    assert feita.compra.valor_em_centavos == 12000
    assert feita.compra.comprada_em == em(10, 3)


def test_r12_compra_bloqueada_com_acesso_ativo(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1)
    escola.vendas.comprar.executar(escola.ana, pacote.id)
    escola.ir_para(em(10, 3, 2028, 23, 59))

    with pytest.raises(AcessoAtivo, match="Você já tem acesso a este pacote até 10/03/2028."):
        escola.vendas.comprar.executar(escola.ana, pacote.id)


def test_r12_nova_compra_depois_que_o_acesso_vence(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1)
    escola.vendas.comprar.executar(escola.ana, pacote.id)
    escola.ir_para(em(15, 3, 2028))

    feita = escola.vendas.comprar.executar(escola.ana, pacote.id)

    assert feita.acesso_ate == date(2029, 3, 15)
    [na_vitrine] = escola.aluno.ver_vitrine.executar(escola.ana)
    assert na_vitrine.acesso == AcessoAoPacote(date(2029, 3, 15), ativo=True)


def test_r15_pacote_arquivado_nao_e_vendido(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1)
    escola.catalogo.arquivar.executar(ADM, pacote.id)

    with pytest.raises(ForaDeVenda, match="Este pacote não está à venda."):
        escola.vendas.comprar.executar(escola.ana, pacote.id)


def test_r60_compra_em_29_02_2028_da_acesso_ate_28_02_2029(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1)
    escola.ir_para(em(29, 2, 2028))

    feita = escola.vendas.comprar.executar(escola.ana, pacote.id)

    assert feita.acesso_ate == date(2029, 2, 28)


def test_r15_r59_o_adm_muda_o_preco_e_as_compras_seguintes_custam_r_100(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1, preco=12000)
    antes = escola.vendas.comprar.executar(escola.ana, pacote.id)

    escola.catalogo.mudar_preco.executar(ADM, pacote.id, 10000)
    depois = escola.vendas.comprar.executar(escola.bruno, pacote.id)

    assert (antes.compra.valor_em_centavos, depois.compra.valor_em_centavos) == (12000, 10000)


def test_rnf07_so_o_aluno_compra(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1)

    with pytest.raises(AcessoNegado, match="Só o aluno pode comprar pacote."):
        escola.vendas.comprar.executar(escola.carlos, pacote.id)


# H16: assistir e concluir aulas gravadas


def test_r12_r62_com_acesso_ana_conclui_a_3a_aula_e_ve_1_de_10(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1, aulas=10)
    escola.vendas.comprar.executar(escola.ana, pacote.id)
    escola.ir_para(em(12, 3, hora=20))

    escola.aluno.concluir_aula.executar(escola.ana, pacote.id, 3)

    [comprado] = escola.aluno.ver_pacotes_comprados.executar(escola.ana)
    assert comprado.progresso == (1, 10)
    assert comprado.concluidas == {3: em(12, 3, hora=20)}


def test_r61_com_acesso_ana_assiste_a_aula_pelo_link_do_youtube(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1, aulas=2)
    escola.vendas.comprar.executar(escola.ana, pacote.id)

    link = escola.aluno.assistir.executar(escola.ana, pacote.id, 2)

    assert link == "https://www.youtube.com/watch?v=aula0000002"


def test_r12_r61_acesso_vencido_ontem_bloqueia_a_aula(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1)
    escola.vendas.comprar.executar(escola.ana, pacote.id)
    escola.ir_para(em(11, 3, 2028, 10))

    with pytest.raises(SemAcesso, match="Seu acesso a este pacote venceu em 10/03/2028."):
        escola.aluno.assistir.executar(escola.ana, pacote.id, 1)
    with pytest.raises(SemAcesso):
        escola.aluno.concluir_aula.executar(escola.ana, pacote.id, 1)


def test_r61_sem_compra_o_aluno_nao_assiste(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1)

    with pytest.raises(SemAcesso, match="Você não tem acesso a este pacote."):
        escola.aluno.assistir.executar(escola.bruno, pacote.id, 1)


def test_r12_pacote_arquivado_continua_acessivel_a_quem_comprou(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1)
    escola.vendas.comprar.executar(escola.ana, pacote.id)
    escola.ir_para(em(10, 6))
    escola.catalogo.arquivar.executar(ADM, pacote.id)

    link = escola.aluno.assistir.executar(escola.ana, pacote.id, 1)

    assert link == "https://www.youtube.com/watch?v=aula0000001"
    [comprado] = escola.aluno.ver_pacotes_comprados.executar(escola.ana)
    assert comprado.resumo.pacote.titulo == "Cinemática"


def test_r12_quem_comprou_mantem_o_acesso_ate_10_03_2028_depois_do_arquivamento(
    escola: Escola,
) -> None:
    pacote = escola.pacote("Cinemática", 1)
    escola.vendas.comprar.executar(escola.ana, pacote.id)

    escola.ir_para(em(1, 6))
    escola.catalogo.arquivar.executar(ADM, pacote.id)

    [comprado] = escola.aluno.ver_pacotes_comprados.executar(escola.ana)
    assert comprado.acesso == AcessoAoPacote(date(2028, 3, 10), ativo=True)
    escola.ir_para(em(10, 3, 2028, 23, 59))
    escola.aluno.assistir.executar(escola.ana, pacote.id, 1)


def test_r32_concluir_um_pacote_nao_promove(escola: Escola) -> None:
    escola.dar_nivel(escola.ana, 1)
    pacote = escola.pacote("Cinemática", 1, aulas=3)
    escola.vendas.comprar.executar(escola.ana, pacote.id)

    for numero in (1, 2, 3):
        escola.aluno.concluir_aula.executar(escola.ana, pacote.id, numero)

    [comprado] = escola.aluno.ver_pacotes_comprados.executar(escola.ana)
    assert comprado.progresso == (3, 3)
    assert escola.niveis.nivel_do_aluno(escola.ana.id, escola.fisica.id) == 1


def test_r62_a_aula_concluida_nao_e_marcada_de_novo(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1, aulas=3)
    escola.vendas.comprar.executar(escola.ana, pacote.id)
    escola.ir_para(em(12, 3))
    escola.aluno.concluir_aula.executar(escola.ana, pacote.id, 3)
    escola.ir_para(em(13, 3))

    with pytest.raises(AulaJaConcluida, match="Você já concluiu a 3ª aula em 12/03/2027."):
        escola.aluno.concluir_aula.executar(escola.ana, pacote.id, 3)

    [comprado] = escola.aluno.ver_pacotes_comprados.executar(escola.ana)
    assert comprado.concluidas == {3: em(12, 3)}


def test_r15_a_aula_nova_do_publicado_ja_aparece_para_quem_tem_acesso(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1, aulas=1)
    escola.vendas.comprar.executar(escola.ana, pacote.id)

    escola.catalogo.adicionar_aula.executar(
        escola.carlos, pacote.id, "Aula nova", "youtu.be/aula0000009"
    )

    [comprado] = escola.aluno.ver_pacotes_comprados.executar(escola.ana)
    assert comprado.progresso == (0, 2)
    assert escola.aluno.assistir.executar(escola.ana, pacote.id, 2).endswith("aula0000009")


def test_cada_aluno_ve_so_os_pacotes_que_comprou(escola: Escola) -> None:
    primeiro = escola.pacote("Cinemática", 1)
    escola.pacote("Dinâmica", 1)
    escola.vendas.comprar.executar(escola.ana, primeiro.id)

    da_ana = escola.aluno.ver_pacotes_comprados.executar(escola.ana)

    assert [c.resumo.pacote.titulo for c in da_ana] == ["Cinemática"]
    assert escola.aluno.ver_pacotes_comprados.executar(escola.bruno) == []


def test_rnf07_so_o_aluno_ve_a_vitrine_e_conclui_aulas(escola: Escola) -> None:
    pacote = escola.pacote("Cinemática", 1)

    with pytest.raises(AcessoNegado, match="Só o aluno pode ver a vitrine de pacotes."):
        escola.aluno.ver_vitrine.executar(ADM)
    with pytest.raises(AcessoNegado, match="Só o aluno pode concluir aula gravada."):
        escola.aluno.concluir_aula.executar(escola.carlos, pacote.id, 1)
