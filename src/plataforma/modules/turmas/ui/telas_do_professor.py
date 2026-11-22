"""Telas das aulas e da prova final (H20, H21, H22, H23, H24, H32). O professor vê em "Minhas
turmas" as turmas que o ADM atribuiu a ele, e o ADM vê em "Presença e notas" todas as turmas. Na
turma escolhida, os dois veem as aulas de cada etapa, a atual ou uma que terminou, lançam e
corrigem a presença e, no fim da etapa, lançam e corrigem a nota da prova final. Só o professor
marca aula como não realizada (R48)."""

from collections.abc import Callable
from datetime import date

from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
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
    EtapaDaTurma,
    SituacaoDaAula,
)
from plataforma.modules.turmas.application.prova_final import (
    AlunoNaProvaFinal,
    CasosDeUsoDaProvaFinal,
)
from plataforma.modules.turmas.domain.horario import descrever_horario, formatar_data_e_hora
from plataforma.modules.turmas.domain.prova_final import ProvaFinal, ResultadoEtapa
from plataforma.modules.turmas.ui.comum import descrever_etapa, nome_da_turma
from plataforma.ui_comum import mostrar_aviso, mostrar_recusa, mostrar_sucesso, titulo

NENHUMA_ESCOLHIDA = "Escolha uma turma na tabela para ver as aulas da etapa."
AVISO_DA_NAO_REALIZADA = (
    "A aula não realizada (feriado, professor doente) sai das 24 e é reposta no fim da etapa, "
    "no mesmo horário. A marcação é definitiva, e a aula que já tem presença lançada não pode "
    "ser marcada."
)
AVISO_DA_CORRECAO = (
    "Você corrige a presença e a nota até 72 horas depois de lançá-las. Depois, só o ADM corrige."
)
AVISO_DO_ADM = (
    "O ADM lança e corrige a presença e a nota em qualquer turma, a qualquer momento. Depois das "
    "72 horas de correção, a correção só muda o nível para cima."
)
EXPLICACAO_DA_PROVA_FINAL = (
    "A nota vai de 0 a 10, com uma casa decimal, como 6,5. O resultado vale quando terminam as "
    "72 horas de correção: o aprovado sobe de nível, e o reprovado sai da turma."
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


def nome_da_etapa(etapa: EtapaDaTurma) -> str:
    """Como o seletor mostra a etapa: "N2 · terminou em 11/02/2027" ou "N3 · etapa atual"."""
    nivel = nome_do_nivel(etapa.nivel)
    if etapa.terminou:
        return f"{nivel} · terminou em {etapa.fim:%d/%m/%Y}"
    return f"{nivel} · etapa atual"


def descrever_nota(prova: ProvaFinal | None) -> str:
    return "—" if prova is None else str(prova.nota)


def descrever_resultado(aluno: AlunoNaProvaFinal) -> str:
    """O resultado da etapa (R08) e, até o fim do prazo de correção, quando ele vale (R49)."""
    prova = aluno.prova
    if prova is None:
        return "pendente: falta a nota"
    if prova.resultado_aplicado is None:
        return f"{aluno.resultado}: vale em {formatar_data_e_hora(prova.vale_em)}"
    if (
        prova.resultado_aplicado == ResultadoEtapa.APROVADO
        and aluno.resultado == ResultadoEtapa.REPROVADO
    ):
        return "reprovado na correção: o nível não muda"
    return str(aluno.resultado)


def _tabela(colunas: list[str]) -> QTableWidget:
    tabela = QTableWidget(0, len(colunas))
    tabela.setHorizontalHeaderLabels(colunas)
    tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tabela.verticalHeader().setVisible(False)
    cabecalho = tabela.horizontalHeader()
    cabecalho.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    cabecalho.setStretchLastSection(True)
    return tabela


def _por_botoes(tabela: QTableWidget, linha: int, coluna: int, botoes: list[QPushButton]) -> None:
    """Põe os botões na célula, que também ganha um texto vazio, como as outras."""
    tabela.setItem(linha, coluna, QTableWidgetItem(""))
    if not botoes:
        return
    acoes = QWidget()
    linha_de_botoes = QHBoxLayout(acoes)
    linha_de_botoes.setContentsMargins(0, 0, 0, 0)
    for botao in botoes:
        linha_de_botoes.addWidget(botao)
    tabela.setCellWidget(linha, coluna, acoes)


class TelaDasAulas(QWidget):
    """As turmas, as aulas da etapa escolhida e a prova final dela. Cada tela que a usa diz o
    título, as colunas da tabela de turmas e de onde as turmas vêm."""

    TITULO = ""
    COLUNAS: tuple[str, ...] = ()
    AVISO = ""
    SEM_TURMAS = ""
    ACAO_DE_LER = ""
    # Só o professor marca aula como não realizada (R48).
    MARCA_NAO_REALIZADA = False

    def __init__(
        self,
        usuario: Usuario,
        casos_de_uso: CasosDeUsoDeTurmas,
        aulas: CasosDeUsoDasAulas,
        prova_final: CasosDeUsoDaProvaFinal,
    ) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_de_uso = casos_de_uso
        self._casos_das_aulas = aulas
        self._prova_final = prova_final
        self._resumos: list[ResumoDaTurma] = []
        self._turma_escolhida: int | None = None
        # None é a etapa atual da turma.
        self._nivel_escolhido: int | None = None
        self._aulas_lidas: AulasDaTurma | None = None
        self._aula_em_lancamento: AulaDaTurma | None = None
        self._nota_em_lancamento: AlunoNaProvaFinal | None = None
        self.botoes_de_presenca: dict[date, QPushButton] = {}
        self.botoes_de_nao_realizada: dict[date, QPushButton] = {}
        self.botoes_de_correcao: dict[date, QPushButton] = {}
        self.botoes_de_nota: dict[int, QPushButton] = {}
        self.presencas: dict[int, QCheckBox] = {}

        self.tabela = _tabela(list(self.COLUNAS))
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)

        self.escolhida = QLabel(NENHUMA_ESCOLHIDA)
        self.escolhida.setWordWrap(True)
        self.etapa = QComboBox()
        linha_da_etapa = QHBoxLayout()
        linha_da_etapa.addWidget(QLabel("Etapa"))
        linha_da_etapa.addWidget(self.etapa, 1)
        aviso = QLabel(self.AVISO)
        aviso.setWordWrap(True)
        self.aulas = _tabela(["Aula", "Data", "Situação", ""])
        explicacao_da_prova_final = QLabel(EXPLICACAO_DA_PROVA_FINAL)
        explicacao_da_prova_final.setWordWrap(True)
        self.aviso_da_prova_final = QLabel()
        self.aviso_da_prova_final.setWordWrap(True)
        self.notas = _tabela(["Aluno", "Faltas", "Nota", "Resultado", ""])
        self.pagina_da_prova_final = QWidget()
        coluna_da_prova_final = QVBoxLayout(self.pagina_da_prova_final)
        coluna_da_prova_final.addWidget(explicacao_da_prova_final)
        coluna_da_prova_final.addWidget(self.aviso_da_prova_final)
        coluna_da_prova_final.addWidget(self.notas, 1)
        self.abas_da_etapa = QTabWidget()
        self.abas_da_etapa.addTab(self.aulas, "Aulas")
        self.abas_da_etapa.addTab(self.pagina_da_prova_final, "Prova final")
        self._grupo_das_aulas = QGroupBox("Aulas da etapa")
        coluna_das_aulas = QVBoxLayout(self._grupo_das_aulas)
        coluna_das_aulas.addWidget(self.escolhida)
        coluna_das_aulas.addLayout(linha_da_etapa)
        coluna_das_aulas.addWidget(aviso)
        coluna_das_aulas.addWidget(self.abas_da_etapa, 1)

        self.titulo_da_presenca = QLabel()
        self._caixas = QVBoxLayout()
        self.botao_lancar = QPushButton("Lançar presença")
        self.botao_corrigir = QPushButton("Corrigir presença")
        linha_dos_botoes = QHBoxLayout()
        linha_dos_botoes.addWidget(self.botao_lancar)
        linha_dos_botoes.addWidget(self.botao_corrigir)
        linha_dos_botoes.addStretch()
        self.grupo_da_presenca = QGroupBox("Presença")
        coluna_da_presenca = QVBoxLayout(self.grupo_da_presenca)
        coluna_da_presenca.addWidget(self.titulo_da_presenca)
        coluna_da_presenca.addLayout(self._caixas)
        coluna_da_presenca.addLayout(linha_dos_botoes)
        self.grupo_da_presenca.hide()

        self.titulo_da_nota = QLabel()
        self.campo_da_nota = QLineEdit()
        self.campo_da_nota.setPlaceholderText("6,5")
        self.campo_da_nota.setMaximumWidth(80)
        self.botao_salvar_nota = QPushButton("Lançar nota")
        self.grupo_da_nota = QGroupBox("Nota da prova final")
        linha_da_nota = QHBoxLayout(self.grupo_da_nota)
        linha_da_nota.addWidget(self.titulo_da_nota, 1)
        linha_da_nota.addWidget(self.campo_da_nota)
        linha_da_nota.addWidget(self.botao_salvar_nota)
        self.grupo_da_nota.hide()

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo(self.TITULO))
        # As aulas da etapa são a maior parte do trabalho: ganham mais espaço.
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(self._grupo_das_aulas, 3)
        coluna.addWidget(self.grupo_da_presenca)
        coluna.addWidget(self.grupo_da_nota)
        coluna.addWidget(self.mensagem)

        self.tabela.itemSelectionChanged.connect(self._escolher)
        self.etapa.currentIndexChanged.connect(self._escolher_etapa)
        self.botao_lancar.clicked.connect(self._lancar)
        self.botao_corrigir.clicked.connect(self._corrigir)
        self.botao_salvar_nota.clicked.connect(self._salvar_nota)
        self.recarregar()

    def _ler_turmas(self) -> list[ResumoDaTurma]:
        raise NotImplementedError

    def _valores(self, resumo: ResumoDaTurma) -> list[str]:
        raise NotImplementedError

    def recarregar(self) -> None:
        resultado = executar(self.ACAO_DE_LER, self._usuario.email, self._ler_turmas)
        match resultado:
            case Feito(resumos):
                self._preencher(resumos)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _preencher(self, resumos: list[ResumoDaTurma]) -> None:
        self._resumos = resumos
        self.tabela.setRowCount(len(resumos))
        for linha, resumo in enumerate(resumos):
            for coluna, valor in enumerate(self._valores(resumo)):
                self.tabela.setItem(linha, coluna, QTableWidgetItem(valor))
        if not resumos:
            mostrar_aviso(self.mensagem, self.SEM_TURMAS)
        self._escolher()

    def _escolher(self) -> None:
        selecionadas = self.tabela.selectionModel().selectedRows()
        escolhida = self._resumos[selecionadas[0].row()].id if selecionadas else None
        if escolhida != self._turma_escolhida:
            # Outra turma começa pela etapa atual dela.
            self._nivel_escolhido = None
        self._turma_escolhida = escolhida
        self._mostrar_aulas()

    def _escolher_etapa(self, _indice: int) -> None:
        self._nivel_escolhido = self.etapa.currentData()
        self._mostrar_aulas()

    def _mostrar_aulas(self) -> None:
        """Lê de novo as aulas e a prova final da etapa escolhida e fecha o que estava aberto."""
        self._fechar_presenca()
        self._fechar_nota()
        turma_id, nivel = self._turma_escolhida, self._nivel_escolhido
        self._grupo_das_aulas.setEnabled(turma_id is not None)
        if turma_id is None:
            self._aulas_lidas = None
            self.escolhida.setText(NENHUMA_ESCOLHIDA)
            self.aulas.setRowCount(0)
            self.etapa.blockSignals(True)
            self.etapa.clear()
            self.etapa.blockSignals(False)
            self.aviso_da_prova_final.clear()
            self._preencher_notas([])
            return
        resultado = executar(
            "ver as aulas da turma",
            self._usuario.email,
            lambda: self._casos_das_aulas.ver_aulas.executar(self._usuario, turma_id, nivel),
        )
        match resultado:
            case Feito(aulas_da_turma):
                self._preencher_aulas(aulas_da_turma)
                self._preencher_etapas(aulas_da_turma)
                self._mostrar_prova_final(turma_id, aulas_da_turma)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _preencher_etapas(self, aulas_da_turma: AulasDaTurma) -> None:
        # Preencher o seletor não é escolher outra etapa.
        self.etapa.blockSignals(True)
        self.etapa.clear()
        for etapa in aulas_da_turma.etapas:
            self.etapa.addItem(nome_da_etapa(etapa), etapa.nivel)
        self.etapa.setCurrentIndex(self.etapa.findData(aulas_da_turma.nivel))
        self.etapa.blockSignals(False)

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
        self.botoes_de_correcao = {}
        marca = self.MARCA_NAO_REALIZADA and aulas_da_turma.em_andamento
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
                botoes.append(
                    self._botao(
                        "Lançar presença", self._abrir_lancamento, aula, self.botoes_de_presenca
                    )
                )
            if aula.situacao == SituacaoDaAula.COM_PRESENCA:
                botoes.append(
                    self._botao(
                        "Corrigir presença", self._abrir_correcao, aula, self.botoes_de_correcao
                    )
                )
            if marca and aula.situacao in (SituacaoDaAula.SEM_PRESENCA, SituacaoDaAula.FUTURA):
                botoes.append(
                    self._botao(
                        "Não realizada",
                        self._marcar_nao_realizada,
                        aula,
                        self.botoes_de_nao_realizada,
                    )
                )
            _por_botoes(self.aulas, linha, 3, botoes)

    @staticmethod
    def _botao(
        texto: str,
        fazer: Callable[[AulaDaTurma], None],
        aula: AulaDaTurma,
        botoes: dict[date, QPushButton],
    ) -> QPushButton:
        """O botão que faz algo com a aula, guardado em botoes pela data dela."""
        botao = QPushButton(texto)
        botao.clicked.connect(lambda: fazer(aula))
        botoes[aula.data] = botao
        return botao

    def _mostrar_prova_final(self, turma_id: int, aulas_da_turma: AulasDaTurma) -> None:
        """H23: a prova final da etapa escolhida. Antes do fim da etapa, quando ela termina."""
        etapa = next(e for e in aulas_da_turma.etapas if e.nivel == aulas_da_turma.nivel)
        if not etapa.terminou:
            self.aviso_da_prova_final.setText(
                "A nota da prova final é lançada no fim da etapa, depois da 24ª aula: em "
                f"{formatar_data_e_hora(etapa.fim)}."
            )
            self._preencher_notas([])
            return
        resultado = executar(
            "ver a prova final da turma",
            self._usuario.email,
            lambda: self._prova_final.ver_prova_final.executar(
                self._usuario, turma_id, etapa.nivel
            ),
        )
        match resultado:
            case Feito(prova_final):
                self.aviso_da_prova_final.setText(
                    f"A etapa do {nome_do_nivel(etapa.nivel)} terminou em "
                    f"{formatar_data_e_hora(etapa.fim)}. Lance a nota de cada aluno que estava "
                    "na turma."
                )
                self._preencher_notas(prova_final.alunos)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _preencher_notas(self, alunos: list[AlunoNaProvaFinal]) -> None:
        # Zerar as linhas também apaga os botões que estavam nelas.
        self.notas.setRowCount(0)
        self.notas.setRowCount(len(alunos))
        self.botoes_de_nota = {}
        for linha, aluno in enumerate(alunos):
            valores = [
                aluno.email,
                contar_faltas(aluno.faltas),
                descrever_nota(aluno.prova),
                descrever_resultado(aluno),
            ]
            for coluna, valor in enumerate(valores):
                self.notas.setItem(linha, coluna, QTableWidgetItem(valor))
            _por_botoes(self.notas, linha, 4, [self._botao_de_nota(aluno)])

    def _botao_de_nota(self, aluno: AlunoNaProvaFinal) -> QPushButton:
        botao = QPushButton("Lançar nota" if aluno.prova is None else "Corrigir nota")
        botao.clicked.connect(lambda: self._abrir_nota(aluno))
        self.botoes_de_nota[aluno.aluno_id] = botao
        return botao

    def _abrir_lancamento(self, aula: AulaDaTurma) -> None:
        """Mostra os alunos da aula, todos marcados como presentes (R08)."""
        self._abrir_presenca(aula, f"Presença {self._quando(aula)}. Desmarque quem faltou.")
        self.botao_lancar.show()
        self.botao_corrigir.hide()

    def _abrir_correcao(self, aula: AulaDaTurma) -> None:
        """R22: mostra os alunos da aula como a presença foi lançada."""
        self._abrir_presenca(
            aula, f"Correção da presença {self._quando(aula)}. Desmarque quem faltou."
        )
        self.botao_lancar.hide()
        self.botao_corrigir.show()

    @staticmethod
    def _quando(aula: AulaDaTurma) -> str:
        return f"da {aula.numero}ª aula, {formatar_data_e_hora(aula.inicio)}"

    def _abrir_presenca(self, aula: AulaDaTurma, titulo_da_presenca: str) -> None:
        self._fechar_presenca()
        self._fechar_nota()
        self._aula_em_lancamento = aula
        self.titulo_da_presenca.setText(titulo_da_presenca)
        for aluno in aula.alunos:
            caixa = QCheckBox(aluno.email)
            caixa.setChecked(aluno.presente is not False)
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

    def _ausentes(self) -> list[int]:
        return [aluno for aluno, caixa in self.presencas.items() if not caixa.isChecked()]

    def _lancar(self) -> None:
        aula, turma_id = self._aula_em_lancamento, self._turma_escolhida
        if aula is None or turma_id is None:
            return
        ausentes = self._ausentes()
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

    def _corrigir(self) -> None:
        aula, turma_id = self._aula_em_lancamento, self._turma_escolhida
        if aula is None or turma_id is None:
            return
        ausentes = self._ausentes()
        resultado = executar(
            "corrigir presença",
            self._usuario.email,
            lambda: self._casos_das_aulas.corrigir_presenca.executar(
                self._usuario, turma_id, aula.data, ausentes
            ),
        )
        match resultado:
            case Feito(presencas):
                self._mostrar_aulas()
                faltas = sum(1 for presenca in presencas if not presenca.presente)
                mostrar_sucesso(
                    self.mensagem,
                    f"Presença da {aula.numero}ª aula corrigida: {contar_faltas(faltas)}.",
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

    def _abrir_nota(self, aluno: AlunoNaProvaFinal) -> None:
        """H23 e H24: o campo da nota do aluno, com a nota atual, se ela já foi lançada."""
        self._fechar_presenca()
        self._nota_em_lancamento = aluno
        nivel = "" if self._aulas_lidas is None else nome_do_nivel(self._aulas_lidas.nivel)
        self.titulo_da_nota.setText(f"Nota de {aluno.email} na prova final do {nivel}.")
        self.campo_da_nota.setText("" if aluno.prova is None else str(aluno.prova.nota))
        self.botao_salvar_nota.setText("Lançar nota" if aluno.prova is None else "Corrigir nota")
        self.grupo_da_nota.show()
        self.campo_da_nota.setFocus()

    def _fechar_nota(self) -> None:
        self._nota_em_lancamento = None
        self.campo_da_nota.clear()
        self.grupo_da_nota.hide()

    def _salvar_nota(self) -> None:
        aluno, aulas_lidas = self._nota_em_lancamento, self._aulas_lidas
        turma_id = self._turma_escolhida
        if aluno is None or aulas_lidas is None or turma_id is None:
            return
        nivel, nota = aulas_lidas.nivel, self.campo_da_nota.text()
        if aluno.prova is None:
            acao, feito = "lançar a nota da prova final", "lançada:"
            salvar = self._prova_final.lancar_nota.executar
        else:
            acao, feito = "corrigir a nota da prova final", "corrigida para"
            salvar = self._prova_final.corrigir_nota.executar
        resultado = executar(
            acao,
            self._usuario.email,
            lambda: salvar(self._usuario, turma_id, nivel, aluno.aluno_id, nota),
        )
        match resultado:
            case Feito(prova):
                self._mostrar_aulas()
                mostrar_sucesso(self.mensagem, f"Nota de {aluno.email} {feito} {prova.nota}.")
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)


class TelaMinhasTurmas(TelaDasAulas):
    """H20: o professor vê só as turmas que o ADM atribuiu a ele, e a turma continua com ele
    quando passa de nível (R26)."""

    TITULO = "Minhas turmas"
    COLUNAS = ("Matéria", "Nível", "Dias e horário", "Etapa")
    AVISO = f"{AVISO_DA_NAO_REALIZADA} {AVISO_DA_CORRECAO}"
    SEM_TURMAS = "Você ainda não tem turmas. O ADM atribui as turmas a você."
    ACAO_DE_LER = "ver minhas turmas"
    MARCA_NAO_REALIZADA = True

    def _ler_turmas(self) -> list[ResumoDaTurma]:
        return self._casos_de_uso.ver_minhas_turmas.executar(self._usuario)

    def _valores(self, resumo: ResumoDaTurma) -> list[str]:
        return [
            resumo.nome_da_materia,
            nome_do_nivel(resumo.nivel),
            descrever_horario(resumo.horario),
            descrever_etapa(resumo),
        ]


class TelaPresencaENotas(TelaDasAulas):
    """H32: o ADM lança e corrige a presença e a nota em qualquer turma (R10, R22, R23)."""

    TITULO = "Presença e notas"
    COLUNAS = ("Matéria", "Nível", "Professor", "Dias e horário", "Etapa")
    AVISO = AVISO_DO_ADM
    SEM_TURMAS = "Ainda não há turmas. O ADM cria as turmas na aba Turmas."
    ACAO_DE_LER = "ver turmas"

    def _ler_turmas(self) -> list[ResumoDaTurma]:
        return self._casos_de_uso.ver_turmas.executar(self._usuario)

    def _valores(self, resumo: ResumoDaTurma) -> list[str]:
        return [
            resumo.nome_da_materia,
            nome_do_nivel(resumo.nivel),
            resumo.email_do_professor,
            descrever_horario(resumo.horario),
            descrever_etapa(resumo),
        ]
