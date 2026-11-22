"""Tela do ADM para criar turmas, trocar o professor e pedir a mudança de horário (H30, H31) ou o
encerramento da turma, que é recusado: ela encerra sozinha depois do nível máximo (H10)."""

from datetime import time

from PySide6.QtCore import QTime
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.modules.identidade.application.casos_de_uso import ConsultaDeProfessores
from plataforma.modules.identidade.domain.professor import Professor
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.identidade.ui.telas_do_adm import preencher_com_professores
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.materias.domain.materia import Materia, nome_do_nivel
from plataforma.modules.materias.ui.telas import preencher_com_materias
from plataforma.modules.turmas.application.casos_de_uso import (
    CasosDeUsoDeTurmas,
    ResumoDaTurma,
)
from plataforma.modules.turmas.domain.horario import (
    DiaDaSemana,
    Horario,
    descrever_horario,
    formatar_data_e_hora,
)
from plataforma.modules.turmas.ui.comum import descrever_etapa, nome_da_turma
from plataforma.ui_comum import mostrar_aviso, mostrar_recusa, mostrar_sucesso, titulo

DIA_ABREVIADO = {
    DiaDaSemana.SEGUNDA: "seg",
    DiaDaSemana.TERCA: "ter",
    DiaDaSemana.QUARTA: "qua",
    DiaDaSemana.QUINTA: "qui",
    DiaDaSemana.SEXTA: "sex",
    DiaDaSemana.SABADO: "sáb",
    DiaDaSemana.DOMINGO: "dom",
}
NENHUMA_ESCOLHIDA = "Escolha uma turma na tabela."


def _hora(hora: QTime) -> time:
    return time(hora.hour(), hora.minute())


class CamposDoHorario(QWidget):
    """Os dias da semana das aulas e as horas de início e de fim, iguais em todos os dias."""

    def __init__(self) -> None:
        super().__init__()
        self.dias = {dia: QCheckBox(DIA_ABREVIADO[dia]) for dia in DiaDaSemana}
        self.inicio = QTimeEdit(QTime(19, 0))
        self.fim = QTimeEdit(QTime(20, 30))
        for campo in (self.inicio, self.fim):
            campo.setDisplayFormat("HH:mm")
        linha = QHBoxLayout(self)
        linha.setContentsMargins(0, 0, 0, 0)
        for caixa in self.dias.values():
            linha.addWidget(caixa)
        linha.addSpacing(12)
        linha.addWidget(QLabel("das"))
        linha.addWidget(self.inicio)
        linha.addWidget(QLabel("às"))
        linha.addWidget(self.fim)
        linha.addStretch()

    def dias_marcados(self) -> list[DiaDaSemana]:
        return [dia for dia, caixa in self.dias.items() if caixa.isChecked()]

    def hora_de_inicio(self) -> time:
        return _hora(self.inicio.time())

    def hora_de_fim(self) -> time:
        return _hora(self.fim.time())

    def mostrar(self, horario: Horario) -> None:
        for dia, caixa in self.dias.items():
            caixa.setChecked(dia in horario.dias)
        self.inicio.setTime(QTime(horario.inicio.hour, horario.inicio.minute))
        self.fim.setTime(QTime(horario.fim.hour, horario.fim.minute))


class TelaTurmas(QWidget):
    def __init__(
        self,
        usuario: Usuario,
        casos_de_uso: CasosDeUsoDeTurmas,
        materias: ConsultaDeMaterias,
        professores: ConsultaDeProfessores,
    ) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_de_uso = casos_de_uso
        self._materias = materias
        self._professores = professores
        self._resumos: list[ResumoDaTurma] = []
        self._materias_lidas: dict[int, Materia] = {}
        self._escolhida: ResumoDaTurma | None = None

        self.tabela = QTableWidget(0, 6)
        self.tabela.setHorizontalHeaderLabels(
            ["Matéria", "Nível", "Professor", "Dias e horário", "Etapa", "Vagas livres"]
        )
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela.verticalHeader().setVisible(False)
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setStretchLastSection(True)

        self.materia = QComboBox()
        self.nivel = QComboBox()
        self.professor = QComboBox()
        self.horario_da_nova = CamposDoHorario()
        self.botao_criar = QPushButton("Criar turma")
        formulario_da_nova = QFormLayout()
        formulario_da_nova.addRow("Matéria", self.materia)
        formulario_da_nova.addRow("Nível inicial", self.nivel)
        formulario_da_nova.addRow("Professor", self.professor)
        formulario_da_nova.addRow("Dias e horário", self.horario_da_nova)
        explicacao = QLabel(
            "O professor precisa estar habilitado na matéria e livre no horário. A 1ª aula é no "
            "primeiro dia da turma depois de hoje, e o horário não muda depois."
        )
        explicacao.setWordWrap(True)
        nova_turma = QGroupBox("Nova turma")
        coluna_da_nova = QVBoxLayout(nova_turma)
        coluna_da_nova.addWidget(explicacao)
        coluna_da_nova.addLayout(formulario_da_nova)
        coluna_da_nova.addWidget(self.botao_criar)

        self.escolhida = QLabel(NENHUMA_ESCOLHIDA)
        self.novo_professor = QComboBox()
        self.botao_trocar = QPushButton("Trocar professor")
        self.horario_da_escolhida = CamposDoHorario()
        self.botao_mudar_horario = QPushButton("Mudar horário")
        self.botao_encerrar = QPushButton("Encerrar turma")
        linha_do_professor = QHBoxLayout()
        linha_do_professor.addWidget(self.novo_professor, 1)
        linha_do_professor.addWidget(self.botao_trocar)
        linha_do_horario = QHBoxLayout()
        linha_do_horario.addWidget(self.horario_da_escolhida, 1)
        linha_do_horario.addWidget(self.botao_mudar_horario)
        linha_do_encerramento = QHBoxLayout()
        linha_do_encerramento.addStretch()
        linha_do_encerramento.addWidget(self.botao_encerrar)
        formulario_da_escolhida = QFormLayout()
        formulario_da_escolhida.addRow("Novo professor", linha_do_professor)
        formulario_da_escolhida.addRow("Dias e horário", linha_do_horario)
        self._grupo_da_escolhida = QGroupBox("Turma escolhida")
        coluna_da_escolhida = QVBoxLayout(self._grupo_da_escolhida)
        coluna_da_escolhida.addWidget(self.escolhida)
        coluna_da_escolhida.addLayout(formulario_da_escolhida)
        coluna_da_escolhida.addLayout(linha_do_encerramento)

        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Turmas"))
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(nova_turma)
        coluna.addWidget(self._grupo_da_escolhida)
        coluna.addWidget(self.mensagem)

        self.materia.currentIndexChanged.connect(self._mostrar_niveis)
        self.tabela.itemSelectionChanged.connect(self._escolher)
        self.botao_criar.clicked.connect(self._criar)
        self.botao_trocar.clicked.connect(self._trocar)
        self.botao_mudar_horario.clicked.connect(self._mudar_horario)
        self.botao_encerrar.clicked.connect(self._encerrar)
        self.recarregar()

    def recarregar(self) -> None:
        """Lê de novo as turmas, as matérias e os professores, mantendo a turma escolhida."""
        match executar("ver turmas", self._usuario.email, self._ler):
            case Feito((resumos, materias, professores)):
                self._materias_lidas = {materia.id: materia for materia in materias}
                preencher_com_materias(self.materia, materias)
                self._mostrar_niveis()
                preencher_com_professores(self.professor, professores)
                preencher_com_professores(self.novo_professor, professores)
                # Sem matéria ou sem professor, não há como criar turma.
                self.botao_criar.setEnabled(bool(materias) and bool(professores))
                self._preencher_tabela(resumos)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _ler(self) -> tuple[list[ResumoDaTurma], list[Materia], list[Professor]]:
        return (
            self._casos_de_uso.ver_turmas.executar(self._usuario),
            self._materias.listar(),
            self._professores.listar(),
        )

    def _mostrar_niveis(self) -> None:
        """O nível inicial pode ser qualquer nível da matéria escolhida (R24)."""
        escolhido = self.nivel.currentData()
        self.nivel.clear()
        materia = self._materias_lidas.get(self.materia.currentData())
        if materia is None:
            return
        for nivel in range(1, materia.nivel_maximo + 1):
            self.nivel.addItem(nome_do_nivel(nivel), nivel)
        self.nivel.setCurrentIndex(max(self.nivel.findData(escolhido), 0))

    def _preencher_tabela(self, resumos: list[ResumoDaTurma]) -> None:
        escolhida_antes = self._escolhida.id if self._escolhida else None
        self.tabela.blockSignals(True)
        self.tabela.clearSelection()
        self.tabela.setRowCount(len(resumos))
        for linha, resumo in enumerate(resumos):
            valores = [
                resumo.nome_da_materia,
                nome_do_nivel(resumo.nivel),
                resumo.email_do_professor,
                descrever_horario(resumo.horario),
                descrever_etapa(resumo),
                str(resumo.vagas_livres),
            ]
            for coluna, valor in enumerate(valores):
                self.tabela.setItem(linha, coluna, QTableWidgetItem(valor))
        self._resumos = resumos
        self.tabela.blockSignals(False)
        ids = [resumo.id for resumo in resumos]
        if escolhida_antes in ids:
            self.tabela.selectRow(ids.index(escolhida_antes))
        else:
            self._escolher()

    def _escolher(self) -> None:
        selecionadas = self.tabela.selectionModel().selectedRows()
        self._escolhida = self._resumos[selecionadas[0].row()] if selecionadas else None
        self._grupo_da_escolhida.setEnabled(self._escolhida is not None)
        if self._escolhida is None:
            self.escolhida.setText(NENHUMA_ESCOLHIDA)
            return
        resumo = self._escolhida
        self.escolhida.setText(
            f"{nome_da_turma(resumo)}, {descrever_horario(resumo.horario)}, "
            f"com {resumo.email_do_professor}"
        )
        self.horario_da_escolhida.mostrar(resumo.horario)

    def _criar(self) -> None:
        materia_id, nivel = self.materia.currentData(), self.nivel.currentData()
        professor_id = self.professor.currentData()
        campos = self.horario_da_nova
        dias, inicio, fim = campos.dias_marcados(), campos.hora_de_inicio(), campos.hora_de_fim()
        resultado = executar(
            "criar turma",
            self._usuario.email,
            lambda: self._casos_de_uso.criar_turma.executar(
                self._usuario, materia_id, nivel, professor_id, dias, inicio, fim
            ),
        )
        match resultado:
            case Feito(turma):
                self.recarregar()
                nome = f"{self._materias_lidas[turma.materia_id].nome} {nome_do_nivel(turma.nivel)}"
                mostrar_sucesso(
                    self.mensagem,
                    f"Turma de {nome} criada. A 1ª aula é em "
                    f"{formatar_data_e_hora(turma.inicio_da_etapa)}.",
                )
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _trocar(self) -> None:
        resumo = self._escolhida
        if resumo is None:
            return
        professor_id, email = self.novo_professor.currentData(), self.novo_professor.currentText()
        resultado = executar(
            "trocar o professor da turma",
            self._usuario.email,
            lambda: self._casos_de_uso.trocar_professor.executar(
                self._usuario, resumo.id, professor_id
            ),
        )
        match resultado:
            case Feito(_):
                self.recarregar()
                mostrar_sucesso(
                    self.mensagem, f"{email} passa a dar aula na turma de {nome_da_turma(resumo)}."
                )
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _mudar_horario(self) -> None:
        resumo = self._escolhida
        if resumo is None:
            return
        campos = self.horario_da_escolhida
        dias, inicio, fim = campos.dias_marcados(), campos.hora_de_inicio(), campos.hora_de_fim()
        resultado = executar(
            "mudar o horário da turma",
            self._usuario.email,
            lambda: self._casos_de_uso.mudar_horario.executar(
                self._usuario, resumo.id, dias, inicio, fim
            ),
        )
        match resultado:
            case Feito(turma):
                mostrar_aviso(
                    self.mensagem,
                    f"Nada mudou: a turma continua às {descrever_horario(turma.horario)}.",
                )
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)
        # O horário da turma não muda (R24): os campos voltam ao horário que ela tem.
        campos.mostrar(resumo.horario)

    def _encerrar(self) -> None:
        """R25: o pedido é recusado, e a mensagem diz quando a turma encerra."""
        resumo = self._escolhida
        if resumo is None:
            return
        resultado = executar(
            "encerrar turma",
            self._usuario.email,
            lambda: self._casos_de_uso.encerrar_turma.executar(self._usuario, resumo.id),
        )
        match resultado:
            case Feito(_):
                self.recarregar()
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)
