"""Configuração dos testes de ponta a ponta, que abrem as janelas do app com o pytest-qt."""

import os
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import closing, contextmanager
from datetime import date, datetime, time, timedelta
from functools import partial
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QRadioButton,
    QTableWidget,
)
from pytestqt.qtbot import QtBot

from plataforma.banco import PASTA_MIGRACOES, aplicar_migracoes, conectar, transacao
from plataforma.compartilhado.horario import BRASILIA
from plataforma.compartilhado.transacao import Transacao
from plataforma.janela_principal import JanelaPrincipal
from plataforma.main import criar_janela
from plataforma.modules.catalogo.application.casos_de_uso import (
    CasosDeUsoDoCatalogo,
    ConsultaDePacotes,
    montar_casos_de_uso,
)
from plataforma.modules.catalogo.domain.pacote import EstadoPacote
from plataforma.modules.catalogo.infra.repositorio_de_pacotes import RepositorioDePacotesSqlite
from plataforma.modules.identidade.application.casos_de_uso import (
    CadastrarAluno,
    CadastrarProfessor,
    ConsultaDeAlunos,
    ConsultaDeProfessores,
    CriarPrimeiroAdm,
    Entrar,
    HabilitarProfessor,
)
from plataforma.modules.identidade.domain.usuario import Usuario
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
from plataforma.modules.materias.infra.repositorio_de_materias import (
    RepositorioDeMateriasSqlite,
)
from plataforma.modules.nivelamento.application.casos_de_uso import CadastrarQuestao
from plataforma.modules.nivelamento.application.consulta_de_niveis import ConsultaDeNiveis
from plataforma.modules.nivelamento.application.promocao import Promocoes
from plataforma.modules.nivelamento.domain.nivelamento import NivelDoAluno
from plataforma.modules.nivelamento.infra.repositorio_de_nivelamentos import (
    RepositorioDeNivelamentosSqlite,
)
from plataforma.modules.nivelamento.infra.repositorio_de_questoes import (
    RepositorioDeQuestoesSqlite,
)
from plataforma.modules.turmas.application.casos_de_uso import CriarTurma
from plataforma.modules.turmas.application.em_dia import TurmasEmDia
from plataforma.modules.turmas.application.matricula import Matricular
from plataforma.modules.turmas.application.presenca import LancarPresenca
from plataforma.modules.turmas.application.prova_final import LancarNota
from plataforma.modules.turmas.domain.horario import DiaDaSemana
from plataforma.modules.turmas.infra.repositorio_de_turmas import RepositorioDeTurmasSqlite
from plataforma.modules.vendas.application.casos_de_uso import montar_casos_de_uso_de_vendas
from plataforma.modules.vendas.infra.repositorio_de_compras import RepositorioDeComprasSqlite
from tests.integracao.conftest import pagar_mensalidades

# Sem tela: a janela não aparece durante os testes, e o mesmo teste roda na CI.
# Para ver a janela, rode com a variável QT_QPA_PLATFORM=windows.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

EMAIL_DO_ADM = "adm@exemplo.com"
SENHA_DO_ADM = "admin123"
SENHA_DOS_PROFESSORES = "abcd1234"
SENHA_DOS_ALUNOS = "abcd1234"


def escolher(combo: QComboBox, texto: str) -> None:
    """Escolhe no combo o item com esse texto, como o usuário faria."""
    indice = combo.findText(texto)
    assert indice >= 0, f"{texto} não está na lista"
    combo.setCurrentIndex(indice)


def linhas(tabela: QTableWidget) -> list[list[str]]:
    """O texto de cada célula da tabela, linha por linha."""
    return [
        [tabela.item(linha, coluna).text() for coluna in range(tabela.columnCount())]
        for linha in range(tabela.rowCount())
    ]


class RelogioDoApp:
    """Relógio falso que só anda quando o teste manda: o tempo mostrado na tela fica exato.

    Começa na segunda, 23/11/2026, às 14h.
    """

    def __init__(self) -> None:
        self._agora = datetime(2026, 11, 23, 14, 0, tzinfo=BRASILIA)

    def agora(self) -> datetime:
        return self._agora

    def avancar(self, **intervalo: float) -> None:
        self._agora += timedelta(**intervalo)


class App:
    """Abre o app numa pasta de dados temporária e age como o usuário: digita e clica."""

    def __init__(self, qtbot: QtBot, pasta_de_dados: Path) -> None:
        self._qtbot = qtbot
        self.pasta_de_dados = pasta_de_dados
        self.relogio = RelogioDoApp()
        # O qtbot só guarda uma referência fraca da janela. Sem esta lista, uma janela que
        # nenhuma variável do teste segura seria apagada no meio do teste.
        self._janelas: list[JanelaPrincipal] = []

    def abrir(self) -> JanelaPrincipal:
        janela = criar_janela(self.pasta_de_dados, self.relogio)
        self._janelas.append(janela)
        self._qtbot.addWidget(janela)
        with self._qtbot.waitExposed(janela):
            janela.show()
        return janela

    def digitar(self, campo: QLineEdit | QPlainTextEdit, texto: str) -> None:
        """Escreve no campo como se o texto fosse colado.

        O qtbot.keyClicks derruba o processo, sem traceback, com letras acentuadas como o
        "í" de "Física" (QTest do Qt 6.12 no Windows), e o app é todo em português.
        """
        campo.setFocus()
        campo.clear()
        if isinstance(campo, QLineEdit):
            campo.insert(texto)
        else:
            campo.insertPlainText(texto)

    def clicar(self, botao: QAbstractButton) -> None:
        """Clica onde o usuário clicaria.

        Num botão de marcar, isso é a bolinha, à esquerda: quando ele ocupa a largura toda da
        tela, o centro cai fora da área que reage ao clique.

        Antes, o Qt termina o que deixou para o laço de eventos: um botão que acabou de ser
        posto numa tabela só ganha tamanho ali, e sem tamanho ele não reage ao clique. Quem usa
        o app nunca clica antes disso.
        """
        QApplication.processEvents()
        if isinstance(botao, QRadioButton | QCheckBox):
            na_bolinha = QPoint(8, botao.height() // 2)
            self._qtbot.mouseClick(botao, Qt.MouseButton.LeftButton, pos=na_bolinha)
        else:
            self._qtbot.mouseClick(botao, Qt.MouseButton.LeftButton)

    def criar_o_primeiro_adm(self, janela: JanelaPrincipal) -> None:
        tela = janela.tela_primeiro_adm
        self.digitar(tela.email, EMAIL_DO_ADM)
        self.digitar(tela.senha, SENHA_DO_ADM)
        self.clicar(tela.botao_criar)

    def entrar(self, janela: JanelaPrincipal, email: str, senha: str) -> None:
        tela = janela.tela_entrar
        self.digitar(tela.email, email)
        self.digitar(tela.senha, senha)
        self.clicar(tela.botao_entrar)

    def cadastrar_aluno(self, janela: JanelaPrincipal, email: str, senha: str) -> None:
        self.clicar(janela.tela_entrar.botao_cadastro)
        tela = janela.tela_cadastro
        self.digitar(tela.email, email)
        self.digitar(tela.senha, senha)
        self.clicar(tela.botao_cadastrar)

    @contextmanager
    def _no_banco(self) -> Iterator[tuple[sqlite3.Connection, Transacao, Usuario]]:
        """Abre o banco do app antes de abrir a janela, já com o ADM criado."""
        caminho_banco = self.pasta_de_dados / "plataforma.db"
        aplicar_migracoes(caminho_banco, PASTA_MIGRACOES, self.pasta_de_dados / "copias")
        with closing(conectar(caminho_banco)) as conexao:
            em_transacao = partial(transacao, conexao)
            usuarios = RepositorioDeUsuariosSqlite(conexao)
            criar_adm = CriarPrimeiroAdm(usuarios, em_transacao)
            if criar_adm.pendente():
                criar_adm.executar(EMAIL_DO_ADM, SENHA_DO_ADM)
            yield conexao, em_transacao, Entrar(usuarios).executar(EMAIL_DO_ADM, SENHA_DO_ADM)

    @staticmethod
    def _em_dia(conexao: sqlite3.Connection) -> TurmasEmDia:
        """O que põe as turmas em dia, que todo caso de uso das turmas recebe."""
        materias = ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao))
        promocoes = Promocoes(RepositorioDeNivelamentosSqlite(conexao), materias)
        return TurmasEmDia(RepositorioDeTurmasSqlite(conexao), materias, promocoes)

    def preparar_materia(
        self, nome: str, notas_minimas: list[int], quantidade_de_questoes: int
    ) -> None:
        """Cadastra, antes de abrir o app, o ADM e uma matéria com questões de correta na B."""
        with self._no_banco() as (conexao, em_transacao, adm):
            materias = RepositorioDeMateriasSqlite(conexao)
            materia = CadastrarMateria(materias, em_transacao).executar(
                adm, nome, len(notas_minimas) + 1, notas_minimas, 20000
            )
            cadastrar_questao = CadastrarQuestao(
                RepositorioDeQuestoesSqlite(conexao), ConsultaDeMaterias(materias), em_transacao
            )
            for numero in range(1, quantidade_de_questoes + 1):
                cadastrar_questao.executar(
                    adm, materia.id, f"{nome}: questão {numero}?", ["A", "B", "C", "D", "E"], 1
                )

    def preparar_professor(self, email: str, *materias: str) -> None:
        """Cadastra, antes de abrir o app, um professor habilitado nas matérias com esses nomes."""
        with self._no_banco() as (conexao, em_transacao, adm):
            usuarios = RepositorioDeUsuariosSqlite(conexao)
            professor = CadastrarProfessor(usuarios, em_transacao).executar(
                adm, email, SENHA_DOS_PROFESSORES
            )
            consulta = ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao))
            ids = {materia.nome: materia.id for materia in consulta.listar()}
            habilitar = HabilitarProfessor(
                RepositorioDeProfessoresSqlite(conexao), consulta, em_transacao
            )
            for nome in materias:
                habilitar.executar(adm, professor.id, ids[nome])

    def preparar_turma(
        self,
        materia: str,
        nivel: int,
        email_do_professor: str,
        dias: Sequence[DiaDaSemana],
        inicio: time,
        fim: time,
    ) -> int:
        """Cria a turma antes de abrir o app, na hora em que o relógio do app está.

        Devolve o id da turma.
        """
        with self._no_banco() as (conexao, em_transacao, adm):
            materias = ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao))
            professores = ConsultaDeProfessores(RepositorioDeProfessoresSqlite(conexao))
            materia_id = next(m.id for m in materias.listar() if m.nome == materia)
            professor_id = next(
                p.id for p in professores.listar() if p.email == email_do_professor
            )
            criar_turma = CriarTurma(
                RepositorioDeTurmasSqlite(conexao),
                materias,
                professores,
                self.relogio,
                em_transacao,
                self._em_dia(conexao),
            )
            turma = criar_turma.executar(adm, materia_id, nivel, professor_id, dias, inicio, fim)
            return turma.id

    def preparar_aluno(self, email: str, niveis: dict[str, int] | None = None) -> Usuario:
        """Cadastra, antes de abrir o app, um aluno com nível nas matérias com esses nomes, como
        se ele tivesse feito o nivelamento."""
        with self._no_banco() as (conexao, em_transacao, _):
            usuarios = RepositorioDeUsuariosSqlite(conexao)
            aluno = CadastrarAluno(usuarios, em_transacao).executar(email, SENHA_DOS_ALUNOS)
            materias = ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao))
            ids = {materia.nome: materia.id for materia in materias.listar()}
            nivelamentos = RepositorioDeNivelamentosSqlite(conexao)
            for nome, nivel in (niveis or {}).items():
                nivelamentos.salvar_nivel(aluno.id, NivelDoAluno(ids[nome], nivel))
            return aluno

    def preparar_matricula(self, aluno: Usuario, turma_id: int) -> None:
        """Matricula o aluno na turma antes de abrir o app, na hora do relógio do app."""
        with self._no_banco() as (conexao, em_transacao, _):
            matricular = Matricular(
                RepositorioDeTurmasSqlite(conexao),
                ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao)),
                ConsultaDeProfessores(RepositorioDeProfessoresSqlite(conexao)),
                ConsultaDeNiveis(RepositorioDeNivelamentosSqlite(conexao)),
                self.relogio,
                em_transacao,
                self._em_dia(conexao),
            )
            matricular.executar(aluno, turma_id)

    def preparar_pacote(
        self,
        titulo: str,
        materia: str,
        nivel: int,
        email_do_professor: str,
        aulas: int = 0,
        estado: EstadoPacote = EstadoPacote.RASCUNHO,
    ) -> int:
        """Cria, antes de abrir o app, o pacote do professor com as aulas "Aula 1", "Aula 2"... e
        o leva até o estado pedido. O publicado custa R$ 120 (R59), e o arquivado também.

        Devolve o id do pacote.
        """
        with self._no_banco() as (conexao, em_transacao, adm):
            materias = ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao))
            professores = ConsultaDeProfessores(RepositorioDeProfessoresSqlite(conexao))
            casos = self._catalogo(conexao, em_transacao)
            materia_id = next(m.id for m in materias.listar() if m.nome == materia)
            professor = next(p for p in professores.listar() if p.email == email_do_professor)
            pacote = casos.criar_pacote.executar(professor.usuario, titulo, materia_id, nivel)
            for numero in range(1, aulas + 1):
                casos.adicionar_aula.executar(
                    professor.usuario, pacote.id, f"Aula {numero}", f"youtu.be/aula{numero:07d}"
                )
            if estado == EstadoPacote.RASCUNHO:
                return pacote.id
            casos.enviar_para_revisao.executar(professor.usuario, pacote.id)
            if estado == EstadoPacote.EM_REVISAO:
                return pacote.id
            casos.publicar.executar(adm, pacote.id, 12000)
            if estado == EstadoPacote.ARQUIVADO:
                casos.arquivar.executar(adm, pacote.id)
            return pacote.id

    def arquivar_pacote(self, pacote_id: int) -> None:
        """O ADM arquiva o pacote publicado antes de abrir o app."""
        with self._no_banco() as (conexao, em_transacao, adm):
            self._catalogo(conexao, em_transacao).arquivar.executar(adm, pacote_id)

    def preparar_compra(self, aluno: Usuario, pacote_id: int) -> None:
        """O aluno compra o pacote antes de abrir o app, na hora do relógio do app."""
        with self._no_banco() as (conexao, em_transacao, _):
            vendas = montar_casos_de_uso_de_vendas(
                RepositorioDeComprasSqlite(conexao),
                ConsultaDePacotes(RepositorioDePacotesSqlite(conexao)),
                self.relogio,
                em_transacao,
            )
            vendas.comprar.executar(aluno, pacote_id)

    @staticmethod
    def _catalogo(conexao: sqlite3.Connection, em_transacao: Transacao) -> CasosDeUsoDoCatalogo:
        return montar_casos_de_uso(
            RepositorioDePacotesSqlite(conexao),
            ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao)),
            ConsultaDeProfessores(RepositorioDeProfessoresSqlite(conexao)),
            em_transacao,
        )

    def preparar_mensalidades(self, aluno: Usuario, turma_id: int, quantas: int = 12) -> None:
        """Grava, antes de abrir o app, as próximas mensalidades do aluno como pagas em dia, para
        ele não perder a vaga por atraso (R28) nos testes que avançam meses."""
        with self._no_banco() as (conexao, _, _):
            pagar_mensalidades(conexao, aluno.id, turma_id, quantas)

    def preparar_presenca(
        self, turma_id: int, data_da_aula: date, ausentes: Sequence[Usuario] = ()
    ) -> None:
        """Lança, antes de abrir o app, a presença de uma aula pelo ADM, que lança em qualquer
        turma (R10). A aula precisa ter começado no relógio do app."""
        with self._no_banco() as (conexao, em_transacao, adm):
            lancar = LancarPresenca(*self._das_aulas(conexao, em_transacao))
            lancar.executar(adm, turma_id, data_da_aula, {aluno.id for aluno in ausentes})

    def preparar_nota(self, turma_id: int, nivel: int, aluno: Usuario, nota: str) -> None:
        """Lança, antes de abrir o app, a nota da prova final pelo ADM, que lança em qualquer
        turma (R10). A etapa do nível precisa ter terminado no relógio do app."""
        with self._no_banco() as (conexao, em_transacao, adm):
            lancar = LancarNota(*self._das_aulas(conexao, em_transacao))
            lancar.executar(adm, turma_id, nivel, aluno.id, nota)

    def _das_aulas(
        self, conexao: sqlite3.Connection, em_transacao: Transacao
    ) -> tuple[
        RepositorioDeTurmasSqlite,
        ConsultaDeMaterias,
        ConsultaDeProfessores,
        ConsultaDeAlunos,
        RelogioDoApp,
        Transacao,
        TurmasEmDia,
    ]:
        """As dependências dos casos de uso das aulas e da prova final."""
        return (
            RepositorioDeTurmasSqlite(conexao),
            ConsultaDeMaterias(RepositorioDeMateriasSqlite(conexao)),
            ConsultaDeProfessores(RepositorioDeProfessoresSqlite(conexao)),
            ConsultaDeAlunos(RepositorioDeUsuariosSqlite(conexao)),
            self.relogio,
            em_transacao,
            self._em_dia(conexao),
        )

    def texto_do_log(self) -> str:
        return (self.pasta_de_dados / "logs" / "plataforma.log").read_text(encoding="utf-8")


@pytest.fixture
def app(qtbot: QtBot, tmp_path: Path) -> App:
    return App(qtbot, tmp_path)
