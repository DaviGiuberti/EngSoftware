"""Telas do aluno no nivelamento: o nível em cada matéria, com a trilha concluída (H03), o teste
(H01, H02) e os certificados de nível e de trilha (H12)."""

import math
from collections.abc import Callable
from datetime import timedelta

from PySide6.QtCore import QElapsedTimer, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.materias.domain.materia import nome_do_nivel
from plataforma.modules.nivelamento.application.casos_de_uso import CasosDeUsoDoNivelamento
from plataforma.modules.nivelamento.application.certificados import CertificadoDoAluno
from plataforma.modules.nivelamento.application.fazer_nivelamento import (
    EstadoDoNivelamento,
    NivelNaMateria,
)
from plataforma.modules.nivelamento.domain.certificado import TipoDeCertificado
from plataforma.modules.nivelamento.domain.nivelamento import SituacaoNaMateria
from plataforma.modules.nivelamento.domain.questao import LETRAS_DAS_ALTERNATIVAS
from plataforma.ui_comum import mostrar_aviso, mostrar_recusa, titulo

INTERVALO_DO_REGISTRO_EM_MS = 15_000
TEXTO_DO_BOTAO = {
    SituacaoNaMateria.SEM_NIVEL: "Fazer nivelamento",
    SituacaoNaMateria.EM_ANDAMENTO: "Continuar nivelamento",
    SituacaoNaMateria.REFAZER_LIBERADO: "Refazer nivelamento",
}


NOME_DO_CERTIFICADO = {
    TipoDeCertificado.NIVEL: "Certificado de nível",
    TipoDeCertificado.TRILHA: "Certificado de trilha",
}
SEM_CERTIFICADOS = (
    "Você ainda não tem certificados. O certificado de nível sai quando você é aprovado na etapa "
    "de uma turma, e o de trilha, quando é aprovado no nível máximo da matéria."
)


def formatar_tempo(tempo: timedelta) -> str:
    """Minutos e segundos, com os segundos arredondados para cima: 59,5 s viram "01:00"."""
    segundos = max(math.ceil(tempo.total_seconds()), 0)
    return f"{segundos // 60:02d}:{segundos % 60:02d}"


class TelaMeusNiveis(QWidget):
    """H03: o nível do aluno em cada matéria, com o botão de fazer o nivelamento."""

    abrir_nivelamento = Signal(int)

    def __init__(self, usuario: Usuario, casos_de_uso: CasosDeUsoDoNivelamento) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_de_uso = casos_de_uso
        self.tabela = QTableWidget(0, 3)
        self.tabela.setHorizontalHeaderLabels(["Matéria", "Nível", ""])
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setStretchLastSection(True)
        self.botoes: dict[str, QPushButton] = {}
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)
        explicacao = QLabel(
            "O nivelamento de cada matéria é feito uma vez, tem 60 minutos e define o nível "
            "em que você começa. O tempo só corre com o teste aberto."
        )
        explicacao.setWordWrap(True)

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Meus níveis"))
        coluna.addWidget(explicacao)
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(self.mensagem)
        self.recarregar()

    def recarregar(self) -> None:
        resultado = executar(
            "ver meus níveis",
            self._usuario.email,
            lambda: self._casos_de_uso.ver_meus_niveis.executar(self._usuario),
        )
        match resultado:
            case Feito(linhas):
                self._preencher(linhas)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def mostrar_recusa(self, texto: str) -> None:
        mostrar_recusa(self.mensagem, texto)

    def _preencher(self, linhas: list[NivelNaMateria]) -> None:
        # Zerar as linhas também apaga os botões que estavam nelas.
        self.tabela.setRowCount(0)
        self.tabela.setRowCount(len(linhas))
        self.botoes = {}
        for numero, linha in enumerate(linhas):
            nivel = nome_do_nivel(linha.nivel) if linha.nivel is not None else "sem nível"
            self.tabela.setItem(numero, 0, QTableWidgetItem(linha.nome_da_materia))
            self.tabela.setItem(numero, 1, QTableWidgetItem(nivel))
            texto_do_botao = TEXTO_DO_BOTAO.get(linha.situacao)
            if texto_do_botao is not None:
                botao = self._botao(texto_do_botao, linha.materia_id)
                self.tabela.setCellWidget(numero, 2, botao)
                self.botoes[linha.nome_da_materia] = botao
            elif linha.situacao == SituacaoNaMateria.INDISPONIVEL:
                aviso = QTableWidgetItem("Nivelamento ainda não disponível")
                self.tabela.setItem(numero, 2, aviso)
            elif linha.trilha_concluida:
                # H03 e R09: aprovado no nível máximo, o aluno concluiu a trilha da matéria.
                self.tabela.setItem(numero, 2, QTableWidgetItem("Trilha concluída"))
            else:
                self.tabela.setItem(numero, 2, QTableWidgetItem(""))

    def _botao(self, texto: str, materia_id: int) -> QPushButton:
        botao = QPushButton(texto)
        botao.clicked.connect(lambda: self.abrir_nivelamento.emit(materia_id))
        return botao


class TelaDoNivelamento(QWidget):
    """H01 e H02: uma questão por vez, o tempo restante e, no fim, o resultado.

    A tela só mostra a contagem. Quem decide o tempo é o caso de uso, que a tela chama a cada
    resposta e a cada 15 segundos: se o app cair, o aluno perde no máximo esse intervalo (R30).
    """

    terminou = Signal()

    def __init__(self, usuario: Usuario, casos_de_uso: CasosDeUsoDoNivelamento) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_de_uso = casos_de_uso
        self._estado: EstadoDoNivelamento | None = None
        self._indice = 0
        self._desde_o_ultimo_estado = QElapsedTimer()

        self.titulo = titulo("")
        self.tempo = QLabel()
        self.progresso = QLabel()
        self.enunciado = QLabel()
        self.enunciado.setWordWrap(True)
        self.alternativas = [QRadioButton() for _ in LETRAS_DAS_ALTERNATIVAS]
        self._grupo = QButtonGroup(self)
        for posicao, alternativa in enumerate(self.alternativas):
            self._grupo.addButton(alternativa, posicao)
        self.botao_anterior = QPushButton("Anterior")
        self.botao_proxima = QPushButton("Próxima")
        self.botao_entregar = QPushButton("Entregar")
        self.botao_sair = QPushButton("Sair e continuar depois")
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)
        self.resultado = QLabel()
        self.resultado.setWordWrap(True)
        self.resultado.setStyleSheet("font-size: 16px")
        self.botao_voltar = QPushButton("Voltar aos meus níveis")

        self._paginas = QStackedWidget()
        self._paginas.addWidget(self._montar_prova())
        self._paginas.addWidget(self._montar_fim())
        coluna = QVBoxLayout(self)
        coluna.addWidget(self.titulo)
        coluna.addWidget(self._paginas, 1)

        self._contagem = QTimer(self)
        self._contagem.setInterval(1000)
        self._contagem.timeout.connect(self._mostrar_tempo)
        self._registro = QTimer(self)
        self._registro.setInterval(INTERVALO_DO_REGISTRO_EM_MS)
        self._registro.timeout.connect(self._registrar_tempo)

        self._grupo.idClicked.connect(self._responder)
        self.botao_anterior.clicked.connect(self._anterior)
        self.botao_proxima.clicked.connect(self._proxima)
        self.botao_entregar.clicked.connect(self._entregar)
        self.botao_sair.clicked.connect(self._sair)
        self.botao_voltar.clicked.connect(self._voltar)

    def abrir(self, materia_id: int) -> str | None:
        """Abre o nivelamento na primeira questão sem resposta. Devolve o motivo da recusa."""
        resultado = executar(
            "iniciar nivelamento",
            self._usuario.email,
            lambda: self._casos_de_uso.iniciar.executar(self._usuario, materia_id),
        )
        match resultado:
            case Feito(estado):
                self.mensagem.clear()
                self._indice = _primeira_sem_resposta(estado)
                self._mostrar(estado)
                return None
            case Falhou(mensagem):
                return mensagem

    def fechar_se_aberto(self) -> None:
        """Quem sai da conta ou do app no meio do teste para o tempo (R30)."""
        estado = self._estado
        self._parar()
        self._estado = None
        if estado is not None and estado.resultado is None:
            executar(
                "fechar nivelamento",
                self._usuario.email,
                lambda: self._casos_de_uso.fechar.executar(self._usuario, estado.nivelamento_id),
            )

    def _montar_prova(self) -> QWidget:
        prova = QWidget()
        topo = QHBoxLayout()
        topo.addWidget(self.progresso)
        topo.addStretch()
        topo.addWidget(self.tempo)
        navegacao = QHBoxLayout()
        navegacao.addWidget(self.botao_anterior)
        navegacao.addWidget(self.botao_proxima)
        navegacao.addStretch()
        navegacao.addWidget(self.botao_sair)
        navegacao.addWidget(self.botao_entregar)
        coluna = QVBoxLayout(prova)
        coluna.addLayout(topo)
        coluna.addWidget(self.enunciado)
        for alternativa in self.alternativas:
            coluna.addWidget(alternativa)
        coluna.addStretch()
        coluna.addLayout(navegacao)
        coluna.addWidget(QLabel("Questões sem resposta contam como erro."))
        coluna.addWidget(self.mensagem)
        return prova

    def _montar_fim(self) -> QWidget:
        fim = QWidget()
        coluna = QVBoxLayout(fim)
        coluna.addWidget(self.resultado)
        coluna.addWidget(self.botao_voltar)
        coluna.addStretch()
        return fim

    def _mostrar(self, estado: EstadoDoNivelamento) -> None:
        self._estado = estado
        self._desde_o_ultimo_estado.restart()
        materia = estado.nome_da_materia
        self.titulo.setText(f"Nivelamento de {materia}")
        if estado.resultado is not None:
            self._parar()
            self.resultado.setText(
                f"Nivelamento de {materia} concluído. Nota: {estado.resultado.nota}%. "
                f"Seu nível em {materia}: {nome_do_nivel(estado.resultado.nivel)}."
            )
            self._paginas.setCurrentIndex(1)
            return
        self._paginas.setCurrentIndex(0)
        self._mostrar_questao()
        self._mostrar_tempo()
        if not self._contagem.isActive():
            self._contagem.start()
            self._registro.start()

    def _mostrar_questao(self) -> None:
        estado = self._estado
        if estado is None:
            return
        questao = estado.questoes[self._indice]
        total = len(estado.questoes)
        respondidas = len(estado.respostas)
        plural = "respondida" if respondidas == 1 else "respondidas"
        self.progresso.setText(f"Questão {self._indice + 1} de {total} · {respondidas} {plural}")
        self.enunciado.setText(questao.enunciado)
        marcada = estado.respostas.get(questao.id)
        # Num grupo exclusivo, o Qt não deixa desmarcar o botão marcado sem isso.
        self._grupo.setExclusive(False)
        for posicao, (letra, alternativa, texto) in enumerate(
            zip(LETRAS_DAS_ALTERNATIVAS, self.alternativas, questao.alternativas, strict=True)
        ):
            alternativa.setText(f"{letra}) {texto}")
            alternativa.setChecked(posicao == marcada)
        self._grupo.setExclusive(True)
        self.botao_anterior.setEnabled(self._indice > 0)
        self.botao_proxima.setEnabled(self._indice < total - 1)

    def _mostrar_tempo(self) -> None:
        estado = self._estado
        if estado is None or estado.resultado is not None:
            return
        decorrido = timedelta(milliseconds=self._desde_o_ultimo_estado.elapsed())
        restante = estado.tempo_restante - decorrido
        if restante <= timedelta(0):
            # O caso de uso confere que o tempo acabou, encerra e corrige (R34).
            self._registrar_tempo()
            return
        self.tempo.setText(f"Tempo restante: {formatar_tempo(restante)}")

    def _responder(self, posicao: int) -> None:
        estado = self._estado
        if estado is None:
            return
        questao_id = estado.questoes[self._indice].id
        self._executar(
            "responder questão",
            lambda: self._casos_de_uso.responder.executar(
                self._usuario, estado.nivelamento_id, questao_id, posicao
            ),
        )

    def _registrar_tempo(self) -> None:
        estado = self._estado
        if estado is None:
            return
        self._executar(
            "registrar o tempo do nivelamento",
            lambda: self._casos_de_uso.registrar_tempo.executar(
                self._usuario, estado.nivelamento_id
            ),
        )

    def _entregar(self) -> None:
        estado = self._estado
        if estado is None:
            return
        self._executar(
            "concluir nivelamento",
            lambda: self._casos_de_uso.concluir.executar(self._usuario, estado.nivelamento_id),
        )

    def _executar(self, acao: str, funcao: Callable[[], EstadoDoNivelamento]) -> None:
        match executar(acao, self._usuario.email, funcao):
            case Feito(estado):
                self.mensagem.clear()
                self._mostrar(estado)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _anterior(self) -> None:
        self._indice = max(self._indice - 1, 0)
        self._mostrar_questao()

    def _proxima(self) -> None:
        if self._estado is not None:
            self._indice = min(self._indice + 1, len(self._estado.questoes) - 1)
            self._mostrar_questao()

    def _sair(self) -> None:
        self.fechar_se_aberto()
        self.terminou.emit()

    def _voltar(self) -> None:
        self._estado = None
        self.terminou.emit()

    def _parar(self) -> None:
        self._contagem.stop()
        self._registro.stop()


def _primeira_sem_resposta(estado: EstadoDoNivelamento) -> int:
    """H02: o aluno continua de onde parou. Com tudo respondido, fica na última questão."""
    return next(
        (i for i, questao in enumerate(estado.questoes) if questao.id not in estado.respostas),
        len(estado.questoes) - 1,
    )


class TelaMeusCertificados(QWidget):
    """H12: os certificados de nível e de trilha do aluno, na ordem em que foram emitidos, com a
    data em que o resultado da etapa valeu (R33, R36)."""

    def __init__(self, usuario: Usuario, casos_de_uso: CasosDeUsoDoNivelamento) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_de_uso = casos_de_uso
        self.tabela = QTableWidget(0, 4)
        self.tabela.setHorizontalHeaderLabels(["Matéria", "Certificado", "Nível", "Emitido em"])
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setStretchLastSection(True)
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)
        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Meus certificados"))
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(self.mensagem)
        self.recarregar()

    def recarregar(self) -> None:
        self.mensagem.clear()
        resultado = executar(
            "ver os próprios certificados",
            self._usuario.email,
            lambda: self._casos_de_uso.ver_meus_certificados.executar(self._usuario),
        )
        match resultado:
            case Feito(emitidos):
                self._preencher(emitidos)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _preencher(self, emitidos: list[CertificadoDoAluno]) -> None:
        self.tabela.setRowCount(len(emitidos))
        for linha, certificado in enumerate(emitidos):
            valores = [
                certificado.nome_da_materia,
                NOME_DO_CERTIFICADO[certificado.tipo],
                nome_do_nivel(certificado.nivel),
                f"{certificado.emitido_em:%d/%m/%Y}",
            ]
            for coluna, valor in enumerate(valores):
                self.tabela.setItem(linha, coluna, QTableWidgetItem(valor))
        if not emitidos:
            mostrar_aviso(self.mensagem, SEM_CERTIFICADOS)


class AreaDoAluno(QStackedWidget):
    """O que o aluno vê depois de entrar: os níveis e, quando ele abre um, o teste."""

    def __init__(self, usuario: Usuario, casos_de_uso: CasosDeUsoDoNivelamento) -> None:
        super().__init__()
        self.tela_meus_niveis = TelaMeusNiveis(usuario, casos_de_uso)
        self.tela_do_nivelamento = TelaDoNivelamento(usuario, casos_de_uso)
        self.addWidget(self.tela_meus_niveis)
        self.addWidget(self.tela_do_nivelamento)
        self.tela_meus_niveis.abrir_nivelamento.connect(self._abrir_nivelamento)
        self.tela_do_nivelamento.terminou.connect(self._voltar_aos_niveis)

    def ao_sair(self) -> None:
        self.tela_do_nivelamento.fechar_se_aberto()

    def _abrir_nivelamento(self, materia_id: int) -> None:
        motivo = self.tela_do_nivelamento.abrir(materia_id)
        if motivo is None:
            self.setCurrentWidget(self.tela_do_nivelamento)
        else:
            self.tela_meus_niveis.mostrar_recusa(motivo)

    def _voltar_aos_niveis(self) -> None:
        self.tela_meus_niveis.recarregar()
        self.setCurrentWidget(self.tela_meus_niveis)
