"""Tela do professor com as turmas que o ADM atribuiu a ele (H20)."""

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.materias.domain.materia import nome_do_nivel
from plataforma.modules.turmas.application.casos_de_uso import (
    CasosDeUsoDeTurmas,
    ResumoDaTurma,
)
from plataforma.modules.turmas.domain.horario import descrever_horario
from plataforma.modules.turmas.ui.comum import descrever_etapa
from plataforma.ui_comum import mostrar_aviso, mostrar_recusa, titulo


class TelaMinhasTurmas(QWidget):
    def __init__(self, usuario: Usuario, casos_de_uso: CasosDeUsoDeTurmas) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_de_uso = casos_de_uso
        self.tabela = QTableWidget(0, 4)
        self.tabela.setHorizontalHeaderLabels(["Matéria", "Nível", "Dias e horário", "Etapa"])
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setStretchLastSection(True)
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Minhas turmas"))
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(self.mensagem)
        self.recarregar()

    def recarregar(self) -> None:
        resultado = executar(
            "ver minhas turmas",
            self._usuario.email,
            lambda: self._casos_de_uso.ver_minhas_turmas.executar(self._usuario),
        )
        match resultado:
            case Feito(resumos):
                self._preencher(resumos)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _preencher(self, resumos: list[ResumoDaTurma]) -> None:
        self.tabela.setRowCount(len(resumos))
        for linha, resumo in enumerate(resumos):
            valores = [
                resumo.nome_da_materia,
                nome_do_nivel(resumo.nivel),
                descrever_horario(resumo.horario),
                descrever_etapa(resumo),
            ]
            for coluna, valor in enumerate(valores):
                self.tabela.setItem(linha, coluna, QTableWidgetItem(valor))
        if not resumos:
            mostrar_aviso(
                self.mensagem, "Você ainda não tem turmas. O ADM atribui as turmas a você."
            )
