"""Tela do ADM para cadastrar e ver as matérias (H27)."""

from collections.abc import Sequence

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.compartilhado.dinheiro import formatar_reais
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.materias.application.casos_de_uso import CasosDeUsoDeMaterias
from plataforma.modules.materias.domain.materia import Materia, nome_do_nivel
from plataforma.ui_comum import mostrar_recusa, mostrar_sucesso, titulo

NIVEIS_AO_ABRIR = 3
MAXIMO_DE_NIVEIS_NA_TELA = 10


def preencher_com_materias(combo: QComboBox, materias: Sequence[Materia]) -> None:
    """Põe as matérias no combo e mantém a escolhida, se ela ainda existir, sem avisar a troca."""
    escolhida = combo.currentData()
    combo.blockSignals(True)
    combo.clear()
    for materia in materias:
        combo.addItem(materia.nome, materia.id)
    combo.setCurrentIndex(max(combo.findData(escolhida), 0))
    combo.blockSignals(False)


def descrever_faixas(materia: Materia) -> str:
    """As faixas como o ADM as vê: "0–39% N1 · 40–69% N2 · 70–100% N3"."""
    return " · ".join(
        f"{faixa.nota_minima}–{faixa.nota_maxima}% {nome_do_nivel(faixa.nivel)}"
        for faixa in materia.faixas
    )


class TelaMaterias(QWidget):
    materias_mudaram = Signal()

    def __init__(self, usuario: Usuario, casos_de_uso: CasosDeUsoDeMaterias) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_de_uso = casos_de_uso

        self.tabela = QTableWidget(0, 4)
        self.tabela.setHorizontalHeaderLabels(
            ["Matéria", "Níveis", "Faixas do nivelamento", "Mensalidade"]
        )
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setStretchLastSection(True)

        self.nome = QLineEdit()
        self.niveis = QSpinBox()
        self.niveis.setRange(1, MAXIMO_DE_NIVEIS_NA_TELA)
        self.niveis.setValue(NIVEIS_AO_ABRIR)
        self.mensalidade = QDoubleSpinBox()
        self.mensalidade.setPrefix("R$ ")
        self.mensalidade.setDecimals(2)
        self.mensalidade.setRange(0, 100_000)
        self.notas_minimas: list[QSpinBox] = []
        self._campos_das_notas = QFormLayout()
        self.botao_cadastrar = QPushButton("Cadastrar matéria")
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)

        formulario = QFormLayout()
        formulario.addRow("Nome", self.nome)
        formulario.addRow("Níveis", self.niveis)
        formulario.addRow("Mensalidade", self.mensalidade)
        explicacao = QLabel(
            "Faixas do nivelamento: o N1 começa em 0%. Diga a partir de que nota começa cada "
            "nível seguinte; cada faixa vai até a próxima, e a última vai até 100%."
        )
        explicacao.setWordWrap(True)
        nova_materia = QGroupBox("Nova matéria")
        coluna_do_formulario = QVBoxLayout(nova_materia)
        coluna_do_formulario.addLayout(formulario)
        coluna_do_formulario.addWidget(explicacao)
        coluna_do_formulario.addLayout(self._campos_das_notas)
        coluna_do_formulario.addWidget(self.botao_cadastrar)
        coluna_do_formulario.addWidget(self.mensagem)

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Matérias"))
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(nova_materia)

        self.niveis.valueChanged.connect(self._montar_campos_das_notas)
        self.botao_cadastrar.clicked.connect(self._cadastrar)
        self._montar_campos_das_notas(self.niveis.value())
        self.recarregar()

    def recarregar(self) -> None:
        match executar("ver matérias", self._usuario.email, self._casos_de_uso.consulta.listar):
            case Feito(materias):
                self._preencher_tabela(materias)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _preencher_tabela(self, materias: list[Materia]) -> None:
        self.tabela.setRowCount(len(materias))
        for linha, materia in enumerate(materias):
            valores = [
                materia.nome,
                str(materia.nivel_maximo),
                descrever_faixas(materia),
                formatar_reais(materia.mensalidade_em_centavos),
            ]
            for coluna, valor in enumerate(valores):
                self.tabela.setItem(linha, coluna, QTableWidgetItem(valor))

    def _montar_campos_das_notas(self, niveis: int) -> None:
        """Um campo de nota mínima para cada nível a partir do N2, já com faixas iguais."""
        while self._campos_das_notas.rowCount():
            self._campos_das_notas.removeRow(0)
        self.notas_minimas = []
        for nivel in range(2, niveis + 1):
            campo = QSpinBox()
            campo.setRange(1, 100)
            campo.setSuffix("%")
            campo.setValue(round(100 * (nivel - 1) / niveis))
            self._campos_das_notas.addRow(f"{nome_do_nivel(nivel)} começa em", campo)
            self.notas_minimas.append(campo)

    def _cadastrar(self) -> None:
        nome = self.nome.text()
        niveis = self.niveis.value()
        notas_minimas = [campo.value() for campo in self.notas_minimas]
        mensalidade_em_centavos = round(self.mensalidade.value() * 100)
        resultado = executar(
            "cadastrar matéria",
            self._usuario.email,
            lambda: self._casos_de_uso.cadastrar_materia.executar(
                self._usuario, nome, niveis, notas_minimas, mensalidade_em_centavos
            ),
        )
        match resultado:
            case Feito(materia):
                mostrar_sucesso(self.mensagem, f"Matéria {materia.nome} cadastrada.")
                self._limpar_formulario()
                self.recarregar()
                self.materias_mudaram.emit()
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _limpar_formulario(self) -> None:
        self.nome.clear()
        self.mensalidade.setValue(0)
        self.niveis.setValue(NIVEIS_AO_ABRIR)
        self._montar_campos_das_notas(NIVEIS_AO_ABRIR)
