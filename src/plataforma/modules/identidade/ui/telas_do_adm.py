"""Tela do ADM para cadastrar professores e habilitá-los por matéria (H29, R11)."""

from collections.abc import Sequence

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.modules.identidade.application.casos_de_uso import CasosDeUsoDaIdentidade
from plataforma.modules.identidade.domain.professor import Professor
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.materias.domain.materia import Materia
from plataforma.modules.materias.ui.telas import preencher_com_materias
from plataforma.ui_comum import mostrar_recusa, mostrar_sucesso, titulo


def preencher_com_professores(
    combo: QComboBox, professores: Sequence[Professor], escolhido: int | None = None
) -> None:
    """Põe os professores no combo, pelo e-mail, sem avisar a troca.

    Fica escolhido o professor de id escolhido ou, sem ele, o que já estava escolhido.
    """
    if escolhido is None:
        escolhido = combo.currentData()
    combo.blockSignals(True)
    combo.clear()
    for professor in professores:
        combo.addItem(professor.email, professor.id)
    combo.setCurrentIndex(max(combo.findData(escolhido), 0))
    combo.blockSignals(False)


def descrever_habilitacoes(professor: Professor, materias: Sequence[Materia]) -> str:
    """As matérias do professor, na ordem da lista de matérias: "Física, Matemática"."""
    nomes = [materia.nome for materia in materias if materia.id in professor.materias_habilitadas]
    return ", ".join(nomes) or "nenhuma matéria"


class TelaProfessores(QWidget):
    professores_mudaram = Signal()

    def __init__(
        self,
        usuario: Usuario,
        casos_de_uso: CasosDeUsoDaIdentidade,
        materias: ConsultaDeMaterias,
    ) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_de_uso = casos_de_uso
        self._materias = materias

        self.tabela = QTableWidget(0, 2)
        self.tabela.setHorizontalHeaderLabels(["Professor", "Habilitado em"])
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setStretchLastSection(True)

        self.email = QLineEdit()
        self.email.setPlaceholderText("dora@exemplo.com")
        self.senha = QLineEdit()
        self.senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.senha.setPlaceholderText("pelo menos 8 caracteres")
        self.botao_cadastrar = QPushButton("Cadastrar professor")
        self.professor = QComboBox()
        self.materia = QComboBox()
        self.botao_habilitar = QPushButton("Habilitar")
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)

        formulario_do_cadastro = QFormLayout()
        formulario_do_cadastro.addRow("E-mail", self.email)
        formulario_do_cadastro.addRow("Senha", self.senha)
        novo_professor = QGroupBox("Novo professor")
        coluna_do_cadastro = QVBoxLayout(novo_professor)
        coluna_do_cadastro.addLayout(formulario_do_cadastro)
        coluna_do_cadastro.addWidget(self.botao_cadastrar)

        explicacao = QLabel("Habilitado numa matéria, o professor dá aula em todos os níveis dela.")
        explicacao.setWordWrap(True)
        formulario_da_habilitacao = QFormLayout()
        formulario_da_habilitacao.addRow("Professor", self.professor)
        formulario_da_habilitacao.addRow("Matéria", self.materia)
        habilitacao = QGroupBox("Habilitar professor")
        coluna_da_habilitacao = QVBoxLayout(habilitacao)
        coluna_da_habilitacao.addWidget(explicacao)
        coluna_da_habilitacao.addLayout(formulario_da_habilitacao)
        coluna_da_habilitacao.addWidget(self.botao_habilitar)

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Professores"))
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(novo_professor)
        coluna.addWidget(habilitacao)
        coluna.addWidget(self.mensagem)

        self.botao_cadastrar.clicked.connect(self._cadastrar)
        self.senha.returnPressed.connect(self._cadastrar)
        self.botao_habilitar.clicked.connect(self._habilitar)
        self.recarregar()

    def recarregar(self, professor_escolhido: int | None = None) -> None:
        """Lê de novo as matérias e os professores, como depois de cadastrar uma matéria."""
        match executar("ver professores", self._usuario.email, self._ler):
            case Feito((materias, professores)):
                self._preencher_tabela(professores, materias)
                preencher_com_materias(self.materia, materias)
                preencher_com_professores(self.professor, professores, professor_escolhido)
                # Sem matéria ou sem professor, não há o que habilitar.
                self.botao_habilitar.setEnabled(bool(materias) and bool(professores))
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _ler(self) -> tuple[list[Materia], list[Professor]]:
        return self._materias.listar(), self._casos_de_uso.consulta_de_professores.listar()

    def _preencher_tabela(
        self, professores: Sequence[Professor], materias: Sequence[Materia]
    ) -> None:
        self.tabela.setRowCount(len(professores))
        for linha, professor in enumerate(professores):
            valores = [professor.email, descrever_habilitacoes(professor, materias)]
            for coluna, valor in enumerate(valores):
                self.tabela.setItem(linha, coluna, QTableWidgetItem(valor))

    def _cadastrar(self) -> None:
        email, senha = self.email.text(), self.senha.text()
        resultado = executar(
            "cadastrar professor",
            self._usuario.email,
            lambda: self._casos_de_uso.cadastrar_professor.executar(self._usuario, email, senha),
        )
        match resultado:
            case Feito(professor):
                self.email.clear()
                self.senha.clear()
                # O professor novo já fica escolhido para o ADM habilitá-lo.
                self.recarregar(professor_escolhido=professor.id)
                mostrar_sucesso(
                    self.mensagem, f"Conta de professor criada para {professor.email}."
                )
                self.professores_mudaram.emit()
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _habilitar(self) -> None:
        professor_id = self.professor.currentData()
        materia_id, nome_da_materia = self.materia.currentData(), self.materia.currentText()
        resultado = executar(
            "habilitar professor",
            self._usuario.email,
            lambda: self._casos_de_uso.habilitar_professor.executar(
                self._usuario, professor_id, materia_id
            ),
        )
        match resultado:
            case Feito(professor):
                self.recarregar()
                mostrar_sucesso(
                    self.mensagem,
                    f"{professor.email} pode dar aula de {nome_da_materia}, em todos os níveis.",
                )
                self.professores_mudaram.emit()
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)
