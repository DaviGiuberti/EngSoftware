"""Janela principal: troca entre as telas e mostra na barra de status se o banco respondeu."""

from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from plataforma.modules.identidade.application.casos_de_uso import CasosDeUsoDaIdentidade
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.identidade.ui.telas import (
    NOME_DO_PERFIL,
    TelaCadastro,
    TelaEntrar,
    TelaPrimeiroAdm,
)


class TelaInicio(QWidget):
    """O que o usuário vê depois de entrar. As fatias seguintes trazem as telas de cada perfil."""

    saiu = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.boas_vindas = QLabel()
        self.botao_sair = QPushButton("Sair")
        self.botao_sair.clicked.connect(self._sair)
        topo = QHBoxLayout()
        topo.addWidget(self.boas_vindas)
        topo.addStretch()
        topo.addWidget(self.botao_sair)
        coluna = QVBoxLayout(self)
        coluna.addLayout(topo)
        coluna.addStretch()

    def mostrar(self, usuario: Usuario) -> None:
        self.boas_vindas.setText(
            f"Você entrou como {usuario.email} ({NOME_DO_PERFIL[usuario.perfil]})."
        )

    def _sair(self) -> None:
        self.saiu.emit()


class JanelaPrincipal(QMainWindow):
    def __init__(
        self,
        banco_ok: bool,
        identidade: CasosDeUsoDaIdentidade,
        ao_fechar: Callable[[], None],
    ) -> None:
        super().__init__()
        self.setWindowTitle("Plataforma de Ensino")
        self.resize(720, 480)
        self._ao_fechar = ao_fechar

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
        self.tela_inicio.saiu.connect(self._abrir_entrar)

        if identidade.criar_primeiro_adm.pendente():
            self.telas.setCurrentWidget(self.tela_primeiro_adm)
        else:
            self._abrir_entrar()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._ao_fechar()
        super().closeEvent(event)

    def _entrou(self, usuario: Usuario) -> None:
        self.tela_inicio.mostrar(usuario)
        self.telas.setCurrentWidget(self.tela_inicio)

    def _abrir_cadastro(self) -> None:
        self.telas.setCurrentWidget(self.tela_cadastro)

    def _abrir_entrar(self) -> None:
        self.tela_entrar.limpar()
        self.telas.setCurrentWidget(self.tela_entrar)
