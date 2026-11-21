"""Telas do ADM no nivelamento: as questões (H28) e as exceções (H33)."""

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
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.materias.ui.telas import preencher_com_materias
from plataforma.modules.nivelamento.application.casos_de_uso import CasosDeUsoDoNivelamento
from plataforma.modules.nivelamento.domain.questao import LETRAS_DAS_ALTERNATIVAS
from plataforma.modules.nivelamento.ui.telas_do_aluno import formatar_tempo
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
                preencher_com_materias(self.materia, materias)
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


class TelaExcecoes(QWidget):
    """H33: o ADM dá mais tempo a um aluno ou libera que ele refaça o nivelamento."""

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

        self.email = QLineEdit()
        self.email.setPlaceholderText("ana@exemplo.com")
        self.materia = QComboBox()
        self.minutos = QSpinBox()
        self.minutos.setRange(1, 240)
        self.minutos.setValue(10)
        self.minutos.setSuffix(" min")
        self.botao_mais_tempo = QPushButton("Dar mais tempo")
        self.botao_refazer = QPushButton("Liberar refazer")
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)
        explicacao = QLabel(
            "Para casos excepcionais, como um problema técnico durante o teste. Mais tempo só "
            "vale para quem está fazendo o nivelamento. Refazer vale para uma tentativa, e o "
            "nível só muda se o resultado for maior."
        )
        explicacao.setWordWrap(True)

        formulario = QFormLayout()
        formulario.addRow("E-mail do aluno", self.email)
        formulario.addRow("Matéria", self.materia)
        formulario.addRow("Minutos a mais", self.minutos)
        botoes = QHBoxLayout()
        botoes.addWidget(self.botao_mais_tempo)
        botoes.addWidget(self.botao_refazer)
        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Exceções do nivelamento"))
        coluna.addWidget(explicacao)
        coluna.addLayout(formulario)
        coluna.addLayout(botoes)
        coluna.addWidget(self.mensagem)
        coluna.addStretch()

        self.botao_mais_tempo.clicked.connect(self._dar_mais_tempo)
        self.botao_refazer.clicked.connect(self._liberar_refazer)
        self.recarregar_materias()

    def recarregar_materias(self) -> None:
        match executar("ver matérias", self._usuario.email, self._materias.listar):
            case Feito(materias):
                preencher_com_materias(self.materia, materias)
                # Sem matéria no combo, não há o que liberar nem a quem dar tempo.
                self.botao_mais_tempo.setEnabled(bool(materias))
                self.botao_refazer.setEnabled(bool(materias))
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _dar_mais_tempo(self) -> None:
        email = self.email.text().strip()
        materia_id, nome = self.materia.currentData(), self.materia.currentText()
        minutos = self.minutos.value()
        resultado = executar(
            "dar mais tempo no nivelamento",
            self._usuario.email,
            lambda: self._casos_de_uso.dar_mais_tempo.executar(
                self._usuario, email, materia_id, minutos
            ),
        )
        match resultado:
            case Feito(restante):
                mostrar_sucesso(
                    self.mensagem,
                    f"{email} passa a ter {formatar_tempo(restante)} no nivelamento de {nome}.",
                )
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _liberar_refazer(self) -> None:
        email = self.email.text().strip()
        materia_id, nome = self.materia.currentData(), self.materia.currentText()
        resultado = executar(
            "liberar refazer o nivelamento",
            self._usuario.email,
            lambda: self._casos_de_uso.liberar_refazer.executar(self._usuario, email, materia_id),
        )
        match resultado:
            case Feito(_):
                mostrar_sucesso(
                    self.mensagem, f"{email} pode refazer o nivelamento de {nome} uma vez."
                )
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)
