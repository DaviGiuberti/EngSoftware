"""Tela do professor (H20, H21, H22): as turmas que o ADM atribuiu a ele e, na turma escolhida,
as aulas da etapa, onde ele lança a presença e marca as aulas não realizadas."""

from datetime import date

from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
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
from plataforma.modules.turmas.application.presenca import (
    AulaDaTurma,
    AulasDaTurma,
    CasosDeUsoDasAulas,
    SituacaoDaAula,
)
from plataforma.modules.turmas.domain.horario import descrever_horario, formatar_data_e_hora
from plataforma.modules.turmas.ui.comum import descrever_etapa, nome_da_turma
from plataforma.ui_comum import mostrar_aviso, mostrar_recusa, mostrar_sucesso, titulo

NENHUMA_ESCOLHIDA = "Escolha uma turma na tabela para ver as aulas da etapa."
AVISO_DA_NAO_REALIZADA = (
    "A aula não realizada (feriado, professor doente) sai das 24 e é reposta no fim da etapa, "
    "no mesmo horário. A marcação é definitiva, e a aula que já tem presença lançada não pode "
    "ser marcada."
)


def contar_faltas(quantas: int) -> str:
    return f"{quantas} falta" if quantas == 1 else f"{quantas} faltas"


def nome_da_aula(aula: AulaDaTurma) -> str:
    return "—" if aula.numero is None else f"{aula.numero}ª aula"


def descrever_situacao_da_aula(aula: AulaDaTurma) -> str:
    match aula.situacao:
        case SituacaoDaAula.NAO_REALIZADA:
            return "não realizada: reposta no fim da etapa"
        case SituacaoDaAula.FUTURA:
            return "ainda não aconteceu"
        case SituacaoDaAula.SEM_PRESENCA:
            return "falta lançar a presença"
        case _:
            ausentes = sum(1 for aluno in aula.alunos if aluno.presente is False)
            return f"presença lançada: {contar_faltas(ausentes)}"


def _tabela(colunas: list[str]) -> QTableWidget:
    tabela = QTableWidget(0, len(colunas))
    tabela.setHorizontalHeaderLabels(colunas)
    tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tabela.verticalHeader().setVisible(False)
    cabecalho = tabela.horizontalHeader()
    cabecalho.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    cabecalho.setStretchLastSection(True)
    return tabela


class TelaMinhasTurmas(QWidget):
    def __init__(
        self, usuario: Usuario, casos_de_uso: CasosDeUsoDeTurmas, aulas: CasosDeUsoDasAulas
    ) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_de_uso = casos_de_uso
        self._casos_das_aulas = aulas
        self._resumos: list[ResumoDaTurma] = []
        self._turma_escolhida: int | None = None
        self._aulas_lidas: AulasDaTurma | None = None
        self._aula_em_lancamento: AulaDaTurma | None = None
        self.botoes_de_presenca: dict[date, QPushButton] = {}
        self.botoes_de_nao_realizada: dict[date, QPushButton] = {}
        self.presencas: dict[int, QCheckBox] = {}

        self.tabela = _tabela(["Matéria", "Nível", "Dias e horário", "Etapa"])
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)

        self.escolhida = QLabel(NENHUMA_ESCOLHIDA)
        self.escolhida.setWordWrap(True)
        aviso = QLabel(AVISO_DA_NAO_REALIZADA)
        aviso.setWordWrap(True)
        self.aulas = _tabela(["Aula", "Data", "Situação", ""])
        self._grupo_das_aulas = QGroupBox("Aulas da etapa")
        coluna_das_aulas = QVBoxLayout(self._grupo_das_aulas)
        coluna_das_aulas.addWidget(self.escolhida)
        coluna_das_aulas.addWidget(aviso)
        coluna_das_aulas.addWidget(self.aulas, 1)

        self.titulo_da_presenca = QLabel()
        self._caixas = QVBoxLayout()
        self.botao_lancar = QPushButton("Lançar presença")
        self.grupo_da_presenca = QGroupBox("Presença")
        coluna_da_presenca = QVBoxLayout(self.grupo_da_presenca)
        coluna_da_presenca.addWidget(self.titulo_da_presenca)
        coluna_da_presenca.addLayout(self._caixas)
        coluna_da_presenca.addWidget(self.botao_lancar)
        self.grupo_da_presenca.hide()

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Minhas turmas"))
        # As aulas da etapa são a maior parte do trabalho do professor: ganham mais espaço.
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(self._grupo_das_aulas, 3)
        coluna.addWidget(self.grupo_da_presenca)
        coluna.addWidget(self.mensagem)

        self.tabela.itemSelectionChanged.connect(self._escolher)
        self.botao_lancar.clicked.connect(self._lancar)
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
        self._resumos = resumos
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
        self._escolher()

    def _escolher(self) -> None:
        selecionadas = self.tabela.selectionModel().selectedRows()
        self._turma_escolhida = self._resumos[selecionadas[0].row()].id if selecionadas else None
        self._mostrar_aulas()

    def _mostrar_aulas(self) -> None:
        """Lê de novo as aulas da turma escolhida e fecha a presença que estava aberta."""
        self._fechar_presenca()
        turma_id = self._turma_escolhida
        self._grupo_das_aulas.setEnabled(turma_id is not None)
        if turma_id is None:
            self._aulas_lidas = None
            self.escolhida.setText(NENHUMA_ESCOLHIDA)
            self.aulas.setRowCount(0)
            return
        resultado = executar(
            "ver as aulas da turma",
            self._usuario.email,
            lambda: self._casos_das_aulas.ver_aulas.executar(self._usuario, turma_id),
        )
        match resultado:
            case Feito(aulas_da_turma):
                self._preencher_aulas(aulas_da_turma)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _preencher_aulas(self, aulas_da_turma: AulasDaTurma) -> None:
        self._aulas_lidas = aulas_da_turma
        resumo = aulas_da_turma.resumo
        self.escolhida.setText(
            f"{nome_da_turma(resumo)}, {descrever_horario(resumo.horario)}: "
            f"{descrever_etapa(resumo)}."
        )
        # Zerar as linhas também apaga os botões que estavam nelas.
        self.aulas.setRowCount(0)
        self.aulas.setRowCount(len(aulas_da_turma.aulas))
        self.botoes_de_presenca = {}
        self.botoes_de_nao_realizada = {}
        for linha, aula in enumerate(aulas_da_turma.aulas):
            valores = [
                nome_da_aula(aula),
                formatar_data_e_hora(aula.inicio),
                descrever_situacao_da_aula(aula),
            ]
            for coluna, valor in enumerate(valores):
                self.aulas.setItem(linha, coluna, QTableWidgetItem(valor))
            botoes = []
            if aula.situacao == SituacaoDaAula.SEM_PRESENCA:
                botoes.append(self._botao_de_presenca(aula))
            if aula.situacao in (SituacaoDaAula.SEM_PRESENCA, SituacaoDaAula.FUTURA):
                botoes.append(self._botao_de_nao_realizada(aula))
            if botoes:
                acoes = QWidget()
                linha_de_botoes = QHBoxLayout(acoes)
                linha_de_botoes.setContentsMargins(0, 0, 0, 0)
                for botao in botoes:
                    linha_de_botoes.addWidget(botao)
                self.aulas.setCellWidget(linha, 3, acoes)
            else:
                self.aulas.setItem(linha, 3, QTableWidgetItem(""))

    def _botao_de_presenca(self, aula: AulaDaTurma) -> QPushButton:
        botao = QPushButton("Lançar presença")
        botao.clicked.connect(lambda: self._abrir_presenca(aula))
        self.botoes_de_presenca[aula.data] = botao
        return botao

    def _botao_de_nao_realizada(self, aula: AulaDaTurma) -> QPushButton:
        botao = QPushButton("Não realizada")
        botao.clicked.connect(lambda: self._marcar_nao_realizada(aula))
        self.botoes_de_nao_realizada[aula.data] = botao
        return botao

    def _abrir_presenca(self, aula: AulaDaTurma) -> None:
        """Mostra os alunos da aula, todos marcados como presentes (R08)."""
        self._fechar_presenca()
        self._aula_em_lancamento = aula
        self.titulo_da_presenca.setText(
            f"Presença da {aula.numero}ª aula, {formatar_data_e_hora(aula.inicio)}. "
            "Desmarque quem faltou."
        )
        for aluno in aula.alunos:
            caixa = QCheckBox(aluno.email)
            caixa.setChecked(True)
            self._caixas.addWidget(caixa)
            self.presencas[aluno.aluno_id] = caixa
        self.grupo_da_presenca.show()

    def _fechar_presenca(self) -> None:
        for caixa in self.presencas.values():
            self._caixas.removeWidget(caixa)
            caixa.deleteLater()
        self.presencas = {}
        self._aula_em_lancamento = None
        self.grupo_da_presenca.hide()

    def _lancar(self) -> None:
        aula, turma_id = self._aula_em_lancamento, self._turma_escolhida
        if aula is None or turma_id is None:
            return
        ausentes = [aluno for aluno, caixa in self.presencas.items() if not caixa.isChecked()]
        resultado = executar(
            "lançar presença",
            self._usuario.email,
            lambda: self._casos_das_aulas.lancar_presenca.executar(
                self._usuario, turma_id, aula.data, ausentes
            ),
        )
        match resultado:
            case Feito(presencas):
                self._mostrar_aulas()
                faltas = sum(1 for presenca in presencas if not presenca.presente)
                mostrar_sucesso(
                    self.mensagem,
                    f"Presença da {aula.numero}ª aula lançada: {contar_faltas(faltas)}.",
                )
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _marcar_nao_realizada(self, aula: AulaDaTurma) -> None:
        turma_id = self._turma_escolhida
        if turma_id is None:
            return
        resultado = executar(
            "marcar aula como não realizada",
            self._usuario.email,
            lambda: self._casos_das_aulas.marcar_nao_realizada.executar(
                self._usuario, turma_id, aula.data
            ),
        )
        match resultado:
            case Feito(_):
                self._mostrar_aulas()
                # R18: a reposição fica no fim, então a 24ª aula, a última da lista, mudou.
                fim = ""
                if self._aulas_lidas is not None:
                    ultima = self._aulas_lidas.aulas[-1].inicio
                    fim = f": a 24ª aula passa para {formatar_data_e_hora(ultima)}"
                mostrar_sucesso(
                    self.mensagem,
                    f"A aula de {aula.data:%d/%m/%Y} não foi realizada. Ela será reposta no fim "
                    f"da etapa{fim}.",
                )
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)
