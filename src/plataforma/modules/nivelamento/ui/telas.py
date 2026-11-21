"""Tela do ADM para cadastrar e ver as questões do nivelamento (H28)."""

from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.nivelamento.application.casos_de_uso import CasosDeUsoDoNivelamento
from plataforma.modules.nivelamento.domain.questao import LETRAS_DAS_ALTERNATIVAS
from plataforma.ui_comum import mostrar_aviso, mostrar_recusa, mostrar_sucesso, titulo


class TelaQuestoes(QWidget):
    def __init__(
        self,
        usuario: Usuario,
        materias: ConsultaDeMaterias,
        casos_de_uso: CasosDeUsoDoNivelamento,
    ) -> None:
        super().__init__()
        self._usuario = usuario
        self._materias = materias
        self._casos_de_uso = casos_de_uso

        self.materia = QComboBox()
        self.lista = QListWidget()
        self.lista.setWordWrap(True)
        self.enunciado = QPlainTextEdit()
        self.enunciado.setPlaceholderText("Enunciado da questão")
        self.enunciado.setFixedHeight(70)
        self.alternativas = [QLineEdit() for _ in LETRAS_DAS_ALTERNATIVAS]
        self.corretas = [QRadioButton("correta") for _ in LETRAS_DAS_ALTERNATIVAS]
        self._grupo_das_corretas = QButtonGroup(self)
        self.botao_cadastrar = QPushButton("Cadastrar questão")
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)

        escolha_da_materia = QFormLayout()
        escolha_da_materia.addRow("Matéria", self.materia)
        alternativas = QFormLayout()
        for indice, (letra, campo, correta) in enumerate(
            zip(LETRAS_DAS_ALTERNATIVAS, self.alternativas, self.corretas, strict=True)
        ):
            self._grupo_das_corretas.addButton(correta, indice)
            linha = QHBoxLayout()
            linha.addWidget(campo)
            linha.addWidget(correta)
            alternativas.addRow(letra, linha)
        nova_questao = QGroupBox("Nova questão")
        coluna_do_formulario = QVBoxLayout(nova_questao)
        coluna_do_formulario.addWidget(self.enunciado)
        coluna_do_formulario.addLayout(alternativas)
        coluna_do_formulario.addWidget(self.botao_cadastrar)
        coluna_do_formulario.addWidget(self.mensagem)

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Questões do nivelamento"))
        coluna.addLayout(escolha_da_materia)
        coluna.addWidget(self.lista, 1)
        coluna.addWidget(nova_questao)

        self.materia.currentIndexChanged.connect(self._mostrar_questoes)
        self.botao_cadastrar.clicked.connect(self._cadastrar)
        self.recarregar_materias()

    def recarregar_materias(self) -> None:
        """Atualiza a lista de matérias, mantendo a escolhida se ela ainda existir."""
        match executar("ver matérias", self._usuario.email, self._materias.listar):
            case Feito(materias):
                escolhida = self.materia.currentData()
                self.materia.blockSignals(True)
                self.materia.clear()
                for materia in materias:
                    self.materia.addItem(materia.nome, materia.id)
                self.materia.setCurrentIndex(max(self.materia.findData(escolhida), 0))
                self.materia.blockSignals(False)
                self.botao_cadastrar.setEnabled(bool(materias))
                if materias:
                    self.mensagem.clear()
                else:
                    mostrar_aviso(self.mensagem, "Cadastre uma matéria antes das questões.")
                self._mostrar_questoes()
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _mostrar_questoes(self) -> None:
        self.lista.clear()
        materia_id = self.materia.currentData()
        if materia_id is None:
            return
        resultado = executar(
            "ver questões do nivelamento",
            self._usuario.email,
            lambda: self._casos_de_uso.listar_questoes.executar(self._usuario, materia_id),
        )
        match resultado:
            case Feito(questoes):
                for numero, questao in enumerate(questoes, start=1):
                    self.lista.addItem(
                        f"{numero}. {questao.enunciado} (correta: {questao.letra_da_correta})"
                    )
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _cadastrar(self) -> None:
        materia_id = self.materia.currentData()
        nome_da_materia = self.materia.currentText()
        enunciado = self.enunciado.toPlainText()
        textos = [campo.text() for campo in self.alternativas]
        marcada = self._grupo_das_corretas.checkedId()
        indice_da_correta = None if marcada == -1 else marcada
        resultado = executar(
            "cadastrar questão",
            self._usuario.email,
            lambda: self._casos_de_uso.cadastrar_questao.executar(
                self._usuario, materia_id, enunciado, textos, indice_da_correta
            ),
        )
        match resultado:
            case Feito(_):
                mostrar_sucesso(
                    self.mensagem, f"Questão cadastrada no nivelamento de {nome_da_materia}."
                )
                self._limpar_formulario()
                self._mostrar_questoes()
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _limpar_formulario(self) -> None:
        self.enunciado.clear()
        for campo in self.alternativas:
            campo.clear()
        # Num grupo exclusivo, o Qt não deixa desmarcar o botão marcado sem isso.
        self._grupo_das_corretas.setExclusive(False)
        for correta in self.corretas:
            correta.setChecked(False)
        self._grupo_das_corretas.setExclusive(True)
