"""Métricas com o banco SQLite (H36): os nivelamentos e as promoções do nivelamento, as presenças
das turmas e as aulas concluídas do catálogo, lidos pelas consultas públicas (ADR 0002). R64, R65,
R66, R67 e RNF07.

Os dados são gravados pelos repositórios de cada módulo, como os casos de uso gravariam: o teste
confere o que as métricas leem do banco, não as regras de quem os grava.
"""

import sqlite3
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta

import pytest

from plataforma.compartilhado.horario import BRASILIA
from plataforma.modules.catalogo.application.aulas_do_aluno import ConsultaDeAulasConcluidas
from plataforma.modules.catalogo.domain.aulas_do_aluno import AulaConcluida
from plataforma.modules.catalogo.domain.pacote import AulaGravada, EstadoPacote, PacoteNovo
from plataforma.modules.catalogo.infra.repositorio_de_aulas_concluidas import (
    RepositorioDeAulasConcluidasSqlite,
)
from plataforma.modules.catalogo.infra.repositorio_de_pacotes import RepositorioDePacotesSqlite
from plataforma.modules.identidade.domain.autorizacao import AcessoNegado
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.metricas.application.casos_de_uso import VerMetricas
from plataforma.modules.metricas.domain.metricas import (
    ContinuidadeNaTrilha,
    TaxaDeProgressao,
    TempoAteNivelCerto,
)
from plataforma.modules.nivelamento.application.historico import HistoricoDoNivelamento
from plataforma.modules.nivelamento.domain.nivelamento import Conclusao
from plataforma.modules.nivelamento.domain.promocao import Promocao
from plataforma.modules.nivelamento.infra.repositorio_de_nivelamentos import (
    RepositorioDeNivelamentosSqlite,
)
from plataforma.modules.turmas.application.consulta_de_presencas import ConsultaDePresencas
from plataforma.modules.turmas.domain.horario import DiaDaSemana, novo_horario
from plataforma.modules.turmas.domain.presenca import Presenca
from plataforma.modules.turmas.domain.turma import TurmaNova
from plataforma.modules.turmas.infra.repositorio_de_turmas import RepositorioDeTurmasSqlite
from tests.integracao.conftest import RelogioDeTeste

ADM = Usuario(id=1000, email="adm@exemplo.com", perfil=Perfil.ADM)
ANA = Usuario(id=2, email="ana@exemplo.com", perfil=Perfil.ALUNO)
CARLOS = 500
FISICA, MATEMATICA = 1, 2
DEZ_DE_MARCO = datetime(2027, 3, 10, 10, 0, tzinfo=BRASILIA)


def dia(numero: int) -> date:
    """O dia de número n depois de 10/03/2027, que é o dia 0."""
    return DEZ_DE_MARCO.date() + timedelta(days=numero)


@dataclass(frozen=True)
class Dados:
    """Grava os dados de cada módulo direto pelos repositórios e lê as métricas."""

    nivelamentos: RepositorioDeNivelamentosSqlite
    turmas: RepositorioDeTurmasSqlite
    pacotes: RepositorioDePacotesSqlite
    concluidas: RepositorioDeAulasConcluidasSqlite
    relogio: RelogioDeTeste
    metricas: VerMetricas

    def nivelar(
        self, aluno_id: int, nivel: int = 2, em: datetime = DEZ_DE_MARCO, materia: int = FISICA
    ) -> None:
        nivelamento = self.nivelamentos.criar(aluno_id, materia, em - timedelta(minutes=30))
        concluido = replace(nivelamento, conclusao=Conclusao(em, nota=50, nivel=nivel))
        self.nivelamentos.salvar(concluido)

    def promover(self, aluno_id: int, em: datetime, materia: int = FISICA) -> None:
        self.nivelamentos.adicionar_promocao(aluno_id, Promocao(materia, 2, 3, em))

    def presenca(self, aluno_id: int, data: date, nivel: int = 2, presente: bool = True) -> None:
        """Uma aula de uma turma de Física nesse nível, só com esse aluno."""
        horario = novo_horario([DiaDaSemana(data.weekday())], time(19), time(20, 30))
        inicio = datetime.combine(data, time(19), BRASILIA)
        turma = self.turmas.adicionar(TurmaNova(FISICA, nivel, CARLOS, horario, inicio))
        self.turmas.lancar_presenca(
            turma.id, nivel, data, [Presenca(aluno_id, data, presente)], inicio, CARLOS
        )

    def aula_concluida(self, aluno_id: int, data: date, nivel: int = 2) -> None:
        """Uma aula concluída de um pacote publicado de Física nesse nível."""
        pacote = self.pacotes.adicionar(PacoteNovo("Pacote", FISICA, nivel, CARLOS))
        aula = AulaGravada(1, "Aula 1", "https://www.youtube.com/watch?v=aula0000001")
        publicado = replace(
            pacote, estado=EstadoPacote.PUBLICADO, aulas=(aula,), preco_em_centavos=12000
        )
        self.pacotes.salvar(publicado)
        quando = datetime.combine(data, time(20), BRASILIA)
        self.concluidas.adicionar(aluno_id, AulaConcluida(pacote.id, 1, quando))

    def ir_para(self, quando: datetime) -> None:
        self.relogio.avancar(seconds=(quando - self.relogio.agora()).total_seconds())


@pytest.fixture
def dados(conexao: sqlite3.Connection) -> Dados:
    nivelamentos = RepositorioDeNivelamentosSqlite(conexao)
    turmas = RepositorioDeTurmasSqlite(conexao)
    concluidas = RepositorioDeAulasConcluidasSqlite(conexao)
    relogio = RelogioDeTeste(datetime(2027, 12, 1, 9, 0, tzinfo=BRASILIA))
    return Dados(
        nivelamentos=nivelamentos,
        turmas=turmas,
        pacotes=RepositorioDePacotesSqlite(conexao),
        concluidas=concluidas,
        relogio=relogio,
        metricas=VerMetricas(
            HistoricoDoNivelamento(nivelamentos),
            ConsultaDePresencas(turmas),
            ConsultaDeAulasConcluidas(concluidas),
            relogio,
        ),
    )


def test_m1_r64_r65_3_de_10_nivelados_de_marco_promovidos_em_ate_6_meses(dados: Dados) -> None:
    for aluno in range(1, 11):
        dados.nivelar(aluno)
    for aluno in (1, 2, 3):
        dados.promover(aluno, datetime(2027, 8, 20, 21, 0, tzinfo=BRASILIA))
    dados.promover(4, datetime(2027, 9, 11, 21, 0, tzinfo=BRASILIA))

    metricas = dados.metricas.executar(ADM, 2027, 3)

    assert metricas.m1 == TaxaDeProgressao(promovidos=3, nivelados=10, ainda_no_prazo=0)
    assert metricas.m1.porcentagem == 30


def test_m2_r66_5_de_10_com_presenca_ou_aula_concluida_na_4a_semana(dados: Dados) -> None:
    for aluno in range(1, 11):
        dados.nivelar(aluno)
    for aluno in (1, 2, 3):
        dados.presenca(aluno, dia(21))
    dados.aula_concluida(4, dia(25))
    dados.aula_concluida(5, dia(27))
    # A falta não é atividade de estudo, e o dia 28 já é a 5ª semana.
    dados.presenca(6, dia(22), presente=False)
    dados.presenca(7, dia(28))
    dados.ir_para(datetime(2027, 4, 7, 9, 0, tzinfo=BRASILIA))

    metricas = dados.metricas.executar(ADM, 2027, 3)

    assert metricas.m2 == ContinuidadeNaTrilha(com_atividade=5, elegiveis=10)
    assert metricas.m2.porcentagem == 50


def test_m3_r67_primeira_atividade_no_nivel_em_1_2_e_6_dias_da_2_dias(dados: Dados) -> None:
    for aluno in (1, 2, 3, 4):
        dados.nivelar(aluno, nivel=2)
    dados.presenca(1, dia(1))
    dados.aula_concluida(2, dia(2))
    dados.presenca(3, dia(6))
    dados.presenca(3, dia(9))
    # O aluno 4 ficou no N2, mas só concluiu aulas de um pacote do N1: não entra na M3.
    dados.aula_concluida(4, dia(1), nivel=1)

    metricas = dados.metricas.executar(ADM, 2027, 3)

    assert metricas.m3 == TempoAteNivelCerto(dias=(1, 2, 6))
    assert metricas.m3.mediana == 2


def test_r64_o_nivelamento_refeito_nao_conta_como_novo(dados: Dados) -> None:
    dados.nivelar(1, nivel=1, em=DEZ_DE_MARCO)
    dados.nivelar(1, nivel=2, em=datetime(2027, 4, 15, 10, 0, tzinfo=BRASILIA))
    dados.nivelar(1, nivel=3, em=datetime(2027, 4, 20, 10, 0, tzinfo=BRASILIA), materia=MATEMATICA)

    de_marco = dados.metricas.executar(ADM, 2027, 3)
    de_abril = dados.metricas.executar(ADM, 2027, 4)

    assert (de_marco.m1.nivelados, de_abril.m1.nivelados) == (1, 1)


def test_r64_o_periodo_e_o_mes_escolhido(dados: Dados) -> None:
    dados.nivelar(1)
    dados.nivelar(2, em=datetime(2027, 4, 1, 10, 0, tzinfo=BRASILIA))

    metricas = dados.metricas.executar(ADM, 2027, 4)

    assert (metricas.ano, metricas.mes, metricas.m1.nivelados) == (2027, 4, 1)


def test_o_mes_que_abre_e_o_do_relogio(dados: Dados) -> None:
    assert dados.metricas.mes_de_agora() == (2027, 12)


def test_rnf07_so_o_adm_ve_as_metricas(dados: Dados) -> None:
    with pytest.raises(AcessoNegado, match="Só o ADM pode ver as métricas."):
        dados.metricas.executar(ANA, 2027, 3)
