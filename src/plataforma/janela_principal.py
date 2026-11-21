"""Janela principal: troca entre as telas e mostra na barra de status se o banco respondeu."""

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
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

from plataforma.modules.identidade.application.casos_de_uso import CasosDeUsoDaIdentidade
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.identidade.ui.telas import (
    NOME_DO_PERFIL,
    TelaCadastro,
    TelaEntrar,
    TelaPrimeiroAdm,
)
from plataforma.modules.materias.application.casos_de_uso import CasosDeUsoDeMaterias
from plataforma.modules.materias.ui.telas import TelaMaterias
from plataforma.modules.nivelamento.application.casos_de_uso import CasosDeUsoDoNivelamento
from plataforma.modules.nivelamento.ui.telas import TelaQuestoes

AVISO_DO_PERFIL = {
    Perfil.ALUNO: "Em breve, aqui: o seu nível em cada matéria e o nivelamento.",
    Perfil.PROFESSOR: "Em breve, aqui: as suas turmas.",
}


@dataclass(frozen=True)
class CasosDeUso:
    """Os casos de uso de todos os módulos, montados pelo main.py."""

    identidade: CasosDeUsoDaIdentidade
    materias: CasosDeUsoDeMaterias
    nivelamento: CasosDeUsoDoNivelamento


class AreaDoAdm(QTabWidget):
    """Abas do ADM: as matérias e as questões do nivelamento."""

    def __init__(self, usuario: Usuario, casos_de_uso: CasosDeUso) -> None:
        super().__init__()
        self.tela_materias = TelaMaterias(usuario, casos_de_uso.materias)
        self.tela_questoes = TelaQuestoes(
            usuario, casos_de_uso.materias.consulta, casos_de_uso.nivelamento
        )
        self.addTab(self.tela_materias, "Matérias")
        self.addTab(self.tela_questoes, "Questões do nivelamento")
        self.tela_materias.materias_mudaram.connect(self.tela_questoes.recarregar_materias)


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
        self._ao_fechar()
        super().closeEvent(event)

    def _entrou(self, usuario: Usuario) -> None:
        self.tela_inicio.mostrar(usuario, self._area_do_perfil(usuario))
        self.telas.setCurrentWidget(self.tela_inicio)

    def _area_do_perfil(self, usuario: Usuario) -> QWidget:
        if usuario.perfil == Perfil.ADM:
            return AreaDoAdm(usuario, self._casos_de_uso)
        aviso = QLabel(AVISO_DO_PERFIL[usuario.perfil])
        aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return aviso

    def _sair(self) -> None:
        self.tela_inicio.limpar()
        self._abrir_entrar()

    def _abrir_cadastro(self) -> None:
        self.telas.setCurrentWidget(self.tela_cadastro)

    def _abrir_entrar(self) -> None:
        self.tela_entrar.limpar()
        self.telas.setCurrentWidget(self.tela_entrar)
