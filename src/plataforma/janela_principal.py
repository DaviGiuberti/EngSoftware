"""Janela principal: troca entre as telas e mostra na barra de status se o banco respondeu."""

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import executar
from plataforma.modules.identidade.application.casos_de_uso import CasosDeUsoDaIdentidade
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.identidade.ui.telas import (
    NOME_DO_PERFIL,
    TelaCadastro,
    TelaEntrar,
    TelaPrimeiroAdm,
)
from plataforma.modules.identidade.ui.telas_do_adm import TelaProfessores
from plataforma.modules.materias.application.casos_de_uso import CasosDeUsoDeMaterias
from plataforma.modules.materias.ui.telas import TelaMaterias
from plataforma.modules.nivelamento.application.casos_de_uso import CasosDeUsoDoNivelamento
from plataforma.modules.nivelamento.ui.telas import TelaExcecoes, TelaQuestoes
from plataforma.modules.nivelamento.ui.telas_do_aluno import AreaDoAluno, TelaMeusCertificados
from plataforma.modules.turmas.application.casos_de_uso import CasosDeUsoDeTurmas
from plataforma.modules.turmas.application.matricula import CasosDeUsoDaMatricula
from plataforma.modules.turmas.application.presenca import CasosDeUsoDasAulas
from plataforma.modules.turmas.application.prova_final import CasosDeUsoDaProvaFinal
from plataforma.modules.turmas.ui.telas import TelaTurmas
from plataforma.modules.turmas.ui.telas_do_aluno import TelaTurmasDoAluno
from plataforma.modules.turmas.ui.telas_do_professor import TelaMinhasTurmas, TelaPresencaENotas


@dataclass(frozen=True)
class CasosDeUso:
    """Os casos de uso de todos os módulos, montados pelo main.py."""

    identidade: CasosDeUsoDaIdentidade
    materias: CasosDeUsoDeMaterias
    nivelamento: CasosDeUsoDoNivelamento
    turmas: CasosDeUsoDeTurmas
    matricula: CasosDeUsoDaMatricula
    aulas: CasosDeUsoDasAulas
    prova_final: CasosDeUsoDaProvaFinal


def por_as_turmas_em_dia(usuario: Usuario, turmas: CasosDeUsoDeTurmas) -> None:
    """Aplica o que o tempo decidiu nas turmas, como a promoção, antes de mostrar uma tela que
    depende disso sem passar pelas turmas, como "Meus níveis" (R49)."""
    executar("pôr as turmas em dia", usuario.email, turmas.atualizar.executar)


class AbasDoAluno(QTabWidget):
    """Abas do aluno: o nível em cada matéria, com o nivelamento, as turmas do nível dele e os
    certificados."""

    def __init__(self, usuario: Usuario, casos_de_uso: CasosDeUso) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_das_turmas = casos_de_uso.turmas
        self.nivelamento = AreaDoAluno(usuario, casos_de_uso.nivelamento)
        self.turmas = TelaTurmasDoAluno(usuario, casos_de_uso.matricula)
        self.certificados = TelaMeusCertificados(usuario, casos_de_uso.nivelamento)
        self.addTab(self.nivelamento, "Meus níveis")
        self.addTab(self.turmas, "Turmas")
        self.addTab(self.certificados, "Meus certificados")
        self.turmas.avisos_mudaram.connect(self._avisar_no_titulo)
        self.currentChanged.connect(self._ao_trocar_de_aba)
        # A aba Turmas leu as turmas ao ser criada, antes de o sinal estar ligado.
        self._avisar_no_titulo(self.turmas.vagas_oferecidas)

    def ao_sair(self) -> None:
        self.nivelamento.ao_sair()

    def _ao_trocar_de_aba(self, _indice: int) -> None:
        # O nivelamento pode ter mudado o nível do aluno: a aba Turmas lê tudo de novo.
        if self.currentWidget() is self.turmas:
            self.turmas.recarregar()
        # A promoção pode ter passado a valer (R49): os níveis são lidos de novo.
        elif self.currentWidget() is self.nivelamento:
            por_as_turmas_em_dia(self._usuario, self._casos_das_turmas)
            self.nivelamento.tela_meus_niveis.recarregar()
        # A promoção também emite o certificado (R33).
        elif self.currentWidget() is self.certificados:
            por_as_turmas_em_dia(self._usuario, self._casos_das_turmas)
            self.certificados.recarregar()

    def _avisar_no_titulo(self, vagas_oferecidas: int) -> None:
        """H06: o aluno vê a vaga oferecida sem precisar abrir a aba Turmas."""
        if vagas_oferecidas == 0:
            titulo = "Turmas"
        elif vagas_oferecidas == 1:
            titulo = "Turmas · 1 vaga para você"
        else:
            titulo = f"Turmas · {vagas_oferecidas} vagas para você"
        self.setTabText(self.indexOf(self.turmas), titulo)


class AreaDoAdm(QTabWidget):
    """Abas do ADM: as matérias, as questões do nivelamento, os professores, as turmas, a
    presença e as notas de qualquer turma e as exceções do nivelamento."""

    def __init__(self, usuario: Usuario, casos_de_uso: CasosDeUso) -> None:
        super().__init__()
        consulta_de_materias = casos_de_uso.materias.consulta
        self.tela_materias = TelaMaterias(usuario, casos_de_uso.materias)
        self.tela_questoes = TelaQuestoes(
            usuario, consulta_de_materias, casos_de_uso.nivelamento
        )
        self.tela_professores = TelaProfessores(
            usuario, casos_de_uso.identidade, consulta_de_materias
        )
        self.tela_turmas = TelaTurmas(
            usuario,
            casos_de_uso.turmas,
            consulta_de_materias,
            casos_de_uso.identidade.consulta_de_professores,
        )
        self.tela_presenca_e_notas = TelaPresencaENotas(
            usuario, casos_de_uso.turmas, casos_de_uso.aulas, casos_de_uso.prova_final
        )
        self.tela_excecoes = TelaExcecoes(
            usuario, consulta_de_materias, casos_de_uso.nivelamento
        )
        self.addTab(self.tela_materias, "Matérias")
        self.addTab(self.tela_questoes, "Questões do nivelamento")
        self.addTab(self.tela_professores, "Professores")
        self.addTab(self.tela_turmas, "Turmas")
        self.addTab(self.tela_presenca_e_notas, "Presença e notas")
        self.addTab(self.tela_excecoes, "Exceções do nivelamento")
        self.tela_materias.materias_mudaram.connect(self.tela_questoes.recarregar_materias)
        self.tela_materias.materias_mudaram.connect(self.tela_professores.recarregar)
        self.tela_materias.materias_mudaram.connect(self.tela_turmas.recarregar)
        self.tela_materias.materias_mudaram.connect(self.tela_excecoes.recarregar_materias)
        self.tela_professores.professores_mudaram.connect(self.tela_turmas.recarregar)
        self.currentChanged.connect(self._ao_trocar_de_aba)

    def _ao_trocar_de_aba(self, _indice: int) -> None:
        # As turmas podem ter mudado na aba Turmas: a presença e as notas leem tudo de novo.
        if self.currentWidget() is self.tela_presenca_e_notas:
            self.tela_presenca_e_notas.recarregar()


class TelaInicio(QWidget):
    """O que o usuário vê depois de entrar: quem entrou, o botão de sair e a área do perfil."""

    saiu = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.boas_vindas = QLabel()
        self.botao_sair = QPushButton("Sair")
        self.botao_sair.clicked.connect(self._sair)
        self.area = QWidget()
        topo = QHBoxLayout()
        topo.addWidget(self.boas_vindas)
        topo.addStretch()
        topo.addWidget(self.botao_sair)
        self._coluna = QVBoxLayout(self)
        self._coluna.addLayout(topo)
        self._coluna.addWidget(self.area, 1)

    def mostrar(self, usuario: Usuario, area: QWidget) -> None:
        self.boas_vindas.setText(
            f"Você entrou como {usuario.email} ({NOME_DO_PERFIL[usuario.perfil]})."
        )
        self._trocar_area(area)

    def limpar(self) -> None:
        """Ao sair, a área do usuário anterior é descartada."""
        self.boas_vindas.clear()
        self._trocar_area(QWidget())

    def _trocar_area(self, area: QWidget) -> None:
        self._coluna.replaceWidget(self.area, area)
        # O deleteLater só apaga quando o Qt volta ao laço de eventos. Sem o hide, a área do
        # usuário anterior continuaria desenhada por baixo da nova até lá.
        self.area.hide()
        self.area.deleteLater()
        self.area = area

    def _sair(self) -> None:
        self.saiu.emit()


class JanelaPrincipal(QMainWindow):
    def __init__(
        self,
        banco_ok: bool,
        casos_de_uso: CasosDeUso,
        ao_fechar: Callable[[], None],
    ) -> None:
        super().__init__()
        self.setWindowTitle("Plataforma de Ensino")
        self.resize(900, 640)
        self._casos_de_uso = casos_de_uso
        self._ao_fechar = ao_fechar
        identidade = casos_de_uso.identidade

        self.tela_primeiro_adm = TelaPrimeiroAdm(identidade.criar_primeiro_adm)
        self.tela_entrar = TelaEntrar(identidade.entrar)
        self.tela_cadastro = TelaCadastro(identidade.cadastrar_aluno)
        self.tela_inicio = TelaInicio()
        self.telas = QStackedWidget()
        self.telas.addWidget(self.tela_primeiro_adm)
        self.telas.addWidget(self.tela_entrar)
        self.telas.addWidget(self.tela_cadastro)
        self.telas.addWidget(self.tela_inicio)
        self.setCentralWidget(self.telas)

        self.rotulo_banco = QLabel("Banco: ok" if banco_ok else "Banco: erro")
        self.statusBar().addPermanentWidget(self.rotulo_banco)

        self.tela_primeiro_adm.entrou.connect(self._entrou)
        self.tela_entrar.entrou.connect(self._entrou)
        self.tela_cadastro.entrou.connect(self._entrou)
        self.tela_entrar.pediu_cadastro.connect(self._abrir_cadastro)
        self.tela_cadastro.voltou.connect(self._abrir_entrar)
        self.tela_inicio.saiu.connect(self._sair)

        if identidade.criar_primeiro_adm.pendente():
            self.telas.setCurrentWidget(self.tela_primeiro_adm)
        else:
            self._abrir_entrar()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._encerrar_area()
        self._ao_fechar()
        super().closeEvent(event)

    def _entrou(self, usuario: Usuario) -> None:
        # O nível do aluno pode ter mudado desde a última vez (R49): "Meus níveis" já abre certo.
        por_as_turmas_em_dia(usuario, self._casos_de_uso.turmas)
        self.tela_inicio.mostrar(usuario, self._area_do_perfil(usuario))
        self.telas.setCurrentWidget(self.tela_inicio)

    def _area_do_perfil(self, usuario: Usuario) -> QWidget:
        if usuario.perfil == Perfil.ADM:
            return AreaDoAdm(usuario, self._casos_de_uso)
        if usuario.perfil == Perfil.ALUNO:
            return AbasDoAluno(usuario, self._casos_de_uso)
        casos = self._casos_de_uso
        return TelaMinhasTurmas(usuario, casos.turmas, casos.aulas, casos.prova_final)

    def _encerrar_area(self) -> None:
        """Quem sai no meio do nivelamento tem o tempo parado antes de a conexão fechar."""
        area = self.tela_inicio.area
        if isinstance(area, AbasDoAluno):
            area.ao_sair()

    def _sair(self) -> None:
        self._encerrar_area()
        self.tela_inicio.limpar()
        self._abrir_entrar()

    def _abrir_cadastro(self) -> None:
        self.telas.setCurrentWidget(self.tela_cadastro)

    def _abrir_entrar(self) -> None:
        self.tela_entrar.limpar()
        self.telas.setCurrentWidget(self.tela_entrar)
