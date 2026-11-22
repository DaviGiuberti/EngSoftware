"""Aba Turmas do aluno (H04, H05, H06, H13, H08, H07): as turmas do nível dele, com a matrícula,
a lista de espera, o aviso da vaga oferecida, a saída da turma e, nas turmas em que ele está, a
mensalidade em aberto, a aula da etapa, as faltas e a prova final da última etapa que terminou.
Quem perdeu a vaga por atraso da mensalidade vê o aviso (R55)."""

from collections.abc import Callable
from datetime import timedelta

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.compartilhado.dinheiro import formatar_reais
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.materias.domain.materia import nome_do_nivel
from plataforma.modules.turmas.application.em_dia import SituacaoNaProvaFinal
from plataforma.modules.turmas.application.matricula import (
    CasosDeUsoDaMatricula,
    MatriculaFeita,
    MensalidadePaga,
    TurmaDoAluno,
    VagaPerdida,
)
from plataforma.modules.turmas.domain.etapa import AULAS_POR_ETAPA
from plataforma.modules.turmas.domain.horario import descrever_horario, formatar_data_e_hora
from plataforma.modules.turmas.domain.matricula import SituacaoNaTurma
from plataforma.modules.turmas.domain.mensalidade import SituacaoDaMensalidade
from plataforma.modules.turmas.domain.presenca import LIMITE_DE_FALTAS, passou_do_limite
from plataforma.modules.turmas.domain.prova_final import ResultadoEtapa
from plataforma.modules.turmas.ui.comum import descrever_etapa, nome_da_turma
from plataforma.ui_comum import mostrar_aviso, mostrar_recusa, mostrar_sucesso, titulo

SEM_TURMAS = (
    "Você ainda não tem turmas do seu nível. Faça o nivelamento em Meus níveis para ver as "
    "turmas de cada matéria."
)


def descrever_situacao(vista: TurmaDoAluno) -> str:
    """A situação do aluno na turma, como a coluna Situação mostra."""
    prazo, vencimento = vista.prazo_para_confirmar, vista.proximo_vencimento
    if vista.situacao == SituacaoNaTurma.MATRICULADO and vencimento is not None:
        return f"Você está nesta turma. Próxima mensalidade: {vencimento:%d/%m/%Y}."
    if vista.situacao == SituacaoNaTurma.VAGA_OFERECIDA and prazo is not None:
        return f"Vaga para você até {formatar_data_e_hora(prazo)}."
    if vista.situacao == SituacaoNaTurma.NA_LISTA:
        return f"Lista de espera: {vista.posicao_na_lista}º lugar."
    if vista.situacao == SituacaoNaTurma.COM_VAGA:
        livres = vista.resumo.vagas_livres
        return "1 vaga livre." if livres == 1 else f"{livres} vagas livres."
    return "Turma cheia."


def avisar_vaga(vista: TurmaDoAluno) -> str | None:
    """H06: o aviso da vaga oferecida, com o prazo para confirmar (R05)."""
    if vista.situacao != SituacaoNaTurma.VAGA_OFERECIDA or vista.prazo_para_confirmar is None:
        return None
    return (
        f"Abriu uma vaga para você na turma de {nome_da_turma(vista.resumo)}, "
        f"{descrever_horario(vista.resumo.horario)}. "
        f"Confirme até {formatar_data_e_hora(vista.prazo_para_confirmar)}."
    )


def descrever_aula_da_etapa(aulas_dadas: int) -> str:
    """H08: "aula 15 de 24", ou antes da 1ª aula da etapa."""
    if aulas_dadas == 0:
        return "antes da 1ª aula"
    return f"aula {aulas_dadas} de {AULAS_POR_ETAPA}"


def descrever_faltas(faltas: int) -> str:
    """H08: as faltas do aluno na etapa e o limite de 6 (R08)."""
    if passou_do_limite(faltas):
        return (
            f"{faltas} faltas: você passou do limite de {LIMITE_DE_FALTAS} e não será promovido "
            "nesta etapa."
        )
    return f"{faltas} de {LIMITE_DE_FALTAS} faltas permitidas"


def descrever_prova_final(situacao: SituacaoNaProvaFinal | None) -> str:
    """H08 e R49: a nota da última etapa que terminou e, até o fim das 72 horas de correção,
    quando o resultado vale."""
    if situacao is None:
        return "—"
    nivel = nome_do_nivel(situacao.nivel)
    prova = situacao.prova
    if prova is None:
        return f"{nivel}: a nota ainda não foi lançada."
    if (
        prova.resultado_aplicado == ResultadoEtapa.APROVADO
        and situacao.resultado == ResultadoEtapa.REPROVADO
    ):
        # R22: depois que o resultado valeu, a correção que reprova não tira a promoção.
        return f"{nivel}: nota {prova.nota}. A sua promoção continua valendo."
    texto = f"{nivel}: nota {prova.nota}, {situacao.resultado}"
    if prova.resultado_aplicado is None:
        return f"{texto}. Vale em {formatar_data_e_hora(prova.vale_em)}."
    return f"{texto}."


def descrever_mensalidade(vista: TurmaDoAluno) -> list[str]:
    """H07: o valor, o vencimento e a situação da mensalidade seguinte às pagas (R28, R53, R54)."""
    devida, situacao = vista.mensalidade_devida, vista.situacao_da_mensalidade
    if devida is None or situacao is None or situacao == SituacaoDaMensalidade.SEM_MENSALIDADE:
        return ["—", "—", "sem mensalidade: a turma encerrou"]
    valor = formatar_reais(vista.mensalidade_em_centavos)
    vencimento = f"{devida.vencimento:%d/%m/%Y}"
    match situacao:
        case SituacaoDaMensalidade.A_ABRIR:
            return [valor, vencimento, f"paga: a próxima abre em {devida.abre_em:%d/%m/%Y}"]
        case SituacaoDaMensalidade.ATRASADA:
            # R37: a tolerância vai até as 23h59 do dia anterior ao da perda da vaga.
            ultimo_dia = devida.perde_a_vaga_em - timedelta(days=1)
            return [
                valor,
                vencimento,
                f"atrasada: pague até {ultimo_dia:%d/%m/%Y}, às 23h59, para não perder a vaga",
            ]
        case _:
            return [valor, vencimento, "em aberto"]


def avisar_vaga_perdida(vaga: VagaPerdida) -> str:
    """R55: o aviso de quem perdeu a vaga por atraso da mensalidade."""
    return (
        f"Você perdeu a vaga na turma de {vaga.nome_da_materia}, "
        f"{descrever_horario(vaga.horario)}, em {vaga.perdida_em:%d/%m/%Y}, por atraso da "
        "mensalidade."
    )


def _mensalidade_paga(paga: MensalidadePaga) -> str:
    return (
        f"Mensalidade de {paga.vencimento:%d/%m/%Y} paga: {formatar_reais(paga.valor_em_centavos)}"
        f". A próxima vence em {paga.proximo_vencimento:%d/%m/%Y}."
    )


def _pagamento(feita: MatriculaFeita) -> str:
    return (
        f"Você pagou {formatar_reais(feita.valor_pago_em_centavos)}, e a próxima mensalidade "
        f"vence em {feita.proximo_vencimento:%d/%m/%Y}."
    )


class TelaTurmasDoAluno(QWidget):
    # Quantas vagas oferecidas o aluno tem para confirmar, para o título da aba avisar.
    avisos_mudaram = Signal(int)

    def __init__(self, usuario: Usuario, casos_de_uso: CasosDeUsoDaMatricula) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_de_uso = casos_de_uso
        self.botoes: dict[int, QPushButton] = {}
        self.botoes_de_pagamento: dict[int, QPushButton] = {}
        self.vagas_oferecidas = 0
        self._vagas_perdidas: list[VagaPerdida] = []

        self.avisos = QLabel()
        self.avisos.setWordWrap(True)
        self.avisos.setStyleSheet("background: #fff4c2; padding: 8px; font-weight: bold")
        self.avisos.hide()
        explicacao = QLabel(
            "Aqui estão as suas turmas e as turmas do seu nível em cada matéria. A matrícula "
            "paga a 1ª mensalidade, e as seguintes vencem todo mês no dia da matrícula."
        )
        explicacao.setWordWrap(True)
        self.tabela = QTableWidget(0, 6)
        self.tabela.setHorizontalHeaderLabels(
            ["Turma", "Dias e horário", "Professor", "Etapa", "Situação", ""]
        )
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setStretchLastSection(True)
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)
        self.etapas = QTableWidget(0, 4)
        self.etapas.setHorizontalHeaderLabels(["Turma", "Aula", "Faltas", "Prova final"])
        self.etapas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.etapas.verticalHeader().setVisible(False)
        self.etapas.setMaximumHeight(140)
        cabecalho_das_etapas = self.etapas.horizontalHeader()
        cabecalho_das_etapas.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecalho_das_etapas.setStretchLastSection(True)
        self._grupo_das_etapas = QGroupBox("Minhas etapas")
        QVBoxLayout(self._grupo_das_etapas).addWidget(self.etapas)
        self._grupo_das_etapas.hide()
        self.mensalidades = QTableWidget(0, 5)
        self.mensalidades.setHorizontalHeaderLabels(
            ["Turma", "Valor", "Vencimento", "Situação", ""]
        )
        self.mensalidades.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.mensalidades.verticalHeader().setVisible(False)
        self.mensalidades.setMaximumHeight(140)
        cabecalho_das_mensalidades = self.mensalidades.horizontalHeader()
        cabecalho_das_mensalidades.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecalho_das_mensalidades.setStretchLastSection(True)
        explicacao_das_mensalidades = QLabel(
            "A mensalidade seguinte pode ser paga desde o vencimento da anterior. Atrasada, você "
            "tem 7 dias de tolerância; depois disso, perde a vaga."
        )
        explicacao_das_mensalidades.setWordWrap(True)
        self.grupo_das_mensalidades = QGroupBox("Mensalidades")
        coluna_das_mensalidades = QVBoxLayout(self.grupo_das_mensalidades)
        coluna_das_mensalidades.addWidget(explicacao_das_mensalidades)
        coluna_das_mensalidades.addWidget(self.mensalidades)
        self.grupo_das_mensalidades.hide()

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Turmas"))
        coluna.addWidget(self.avisos)
        coluna.addWidget(explicacao)
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(self.grupo_das_mensalidades)
        coluna.addWidget(self._grupo_das_etapas)
        coluna.addWidget(self.mensagem)
        self.recarregar()

    def recarregar(self) -> None:
        """Lê de novo as turmas, como depois de o aluno fazer o nivelamento."""
        self.mensagem.clear()
        perdidas = executar(
            "ver as vagas perdidas",
            self._usuario.email,
            lambda: self._casos_de_uso.ver_vagas_perdidas.executar(self._usuario),
        )
        self._vagas_perdidas = perdidas.valor if isinstance(perdidas, Feito) else []
        resultado = executar(
            "ver turmas do seu nível",
            self._usuario.email,
            lambda: self._casos_de_uso.ver_turmas_do_aluno.executar(self._usuario),
        )
        match resultado:
            case Feito(vistas):
                self._preencher(vistas)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _preencher(self, vistas: list[TurmaDoAluno]) -> None:
        # Zerar as linhas também apaga os botões que estavam nelas.
        self.tabela.setRowCount(0)
        self.tabela.setRowCount(len(vistas))
        self.botoes = {}
        for linha, vista in enumerate(vistas):
            resumo = vista.resumo
            valores = [
                nome_da_turma(resumo),
                descrever_horario(resumo.horario),
                resumo.email_do_professor,
                descrever_etapa(resumo),
                descrever_situacao(vista),
            ]
            for coluna, valor in enumerate(valores):
                self.tabela.setItem(linha, coluna, QTableWidgetItem(valor))
            acao = self._acao(vista)
            if acao is None:
                self.tabela.setItem(linha, 5, QTableWidgetItem(""))
            else:
                texto, fazer = acao
                botao = QPushButton(texto)
                botao.clicked.connect(fazer)
                self.tabela.setCellWidget(linha, 5, botao)
                self.botoes[resumo.id] = botao
        ofertas = [aviso for vista in vistas if (aviso := avisar_vaga(vista)) is not None]
        avisos = ofertas + [avisar_vaga_perdida(vaga) for vaga in self._vagas_perdidas]
        self.avisos.setText("\n".join(avisos))
        self.avisos.setVisible(bool(avisos))
        self.vagas_oferecidas = len(ofertas)
        self.avisos_mudaram.emit(self.vagas_oferecidas)
        self._preencher_mensalidades(vistas)
        self._preencher_etapas(vistas)
        if not vistas:
            mostrar_aviso(self.mensagem, SEM_TURMAS)

    def _preencher_mensalidades(self, vistas: list[TurmaDoAluno]) -> None:
        """H07: em cada turma em que o aluno está, a mensalidade seguinte e o botão de pagá-la
        quando ela está em aberto ou atrasada (R28, R53)."""
        minhas = [vista for vista in vistas if vista.situacao == SituacaoNaTurma.MATRICULADO]
        # Zerar as linhas também apaga os botões que estavam nelas.
        self.mensalidades.setRowCount(0)
        self.mensalidades.setRowCount(len(minhas))
        self.botoes_de_pagamento = {}
        a_pagar = (SituacaoDaMensalidade.EM_ABERTO, SituacaoDaMensalidade.ATRASADA)
        for linha, vista in enumerate(minhas):
            valores = [nome_da_turma(vista.resumo), *descrever_mensalidade(vista), ""]
            for coluna, valor in enumerate(valores):
                self.mensalidades.setItem(linha, coluna, QTableWidgetItem(valor))
            if vista.situacao_da_mensalidade in a_pagar:
                botao = QPushButton(f"Pagar {formatar_reais(vista.mensalidade_em_centavos)}")
                botao.clicked.connect(self._pagar_em(vista))
                self.mensalidades.setCellWidget(linha, 4, botao)
                self.botoes_de_pagamento[vista.resumo.id] = botao
        self.grupo_das_mensalidades.setVisible(bool(minhas))

    def _pagar_em(self, vista: TurmaDoAluno) -> Callable[[], None]:
        return lambda: self._fazer(
            "pagar a mensalidade",
            lambda: self._casos_de_uso.pagar_mensalidade.executar(self._usuario, vista.resumo.id),
            _mensalidade_paga,
        )

    def _preencher_etapas(self, vistas: list[TurmaDoAluno]) -> None:
        """H08: em cada turma em que o aluno está, a aula da etapa, as faltas dele (R08) e a
        prova final da última etapa que terminou (R49)."""
        minhas = [vista for vista in vistas if vista.situacao == SituacaoNaTurma.MATRICULADO]
        self.etapas.setRowCount(len(minhas))
        for linha, vista in enumerate(minhas):
            valores = [
                nome_da_turma(vista.resumo),
                descrever_aula_da_etapa(vista.resumo.aulas_dadas),
                descrever_faltas(vista.faltas or 0),
                descrever_prova_final(vista.prova_final),
            ]
            for coluna, valor in enumerate(valores):
                self.etapas.setItem(linha, coluna, QTableWidgetItem(valor))
        self._grupo_das_etapas.setVisible(bool(minhas))

    def _acao(self, vista: TurmaDoAluno) -> tuple[str, Callable[[], None]] | None:
        """O botão de cada situação: o texto e o que ele faz."""
        valor = formatar_reais(vista.mensalidade_em_centavos)
        match vista.situacao:
            case SituacaoNaTurma.MATRICULADO:
                return "Sair da turma", lambda: self._sair(vista)
            case SituacaoNaTurma.VAGA_OFERECIDA:
                return f"Confirmar e pagar {valor}", lambda: self._confirmar(vista)
            case SituacaoNaTurma.COM_VAGA:
                return f"Matricular-se e pagar {valor}", lambda: self._matricular(vista)
            case SituacaoNaTurma.CHEIA:
                return "Entrar na lista de espera", lambda: self._entrar_na_lista(vista)
            case _:
                return None

    def _matricular(self, vista: TurmaDoAluno) -> None:
        nome = nome_da_turma(vista.resumo)
        self._fazer(
            "se matricular numa turma",
            lambda: self._casos_de_uso.matricular.executar(self._usuario, vista.resumo.id),
            lambda feita: f"Matrícula feita na turma de {nome}. {_pagamento(feita)}",
        )

    def _confirmar(self, vista: TurmaDoAluno) -> None:
        nome = nome_da_turma(vista.resumo)
        self._fazer(
            "confirmar a vaga",
            lambda: self._casos_de_uso.confirmar_vaga.executar(self._usuario, vista.resumo.id),
            lambda feita: f"Vaga confirmada: você está na turma de {nome}. {_pagamento(feita)}",
        )

    def _entrar_na_lista(self, vista: TurmaDoAluno) -> None:
        nome = nome_da_turma(vista.resumo)
        self._fazer(
            "entrar na lista de espera",
            lambda: self._casos_de_uso.entrar_na_lista.executar(self._usuario, vista.resumo.id),
            lambda lugar: f"Você entrou na lista de espera da turma de {nome}, em {lugar}º lugar.",
        )

    def _sair(self, vista: TurmaDoAluno) -> None:
        nome = nome_da_turma(vista.resumo)
        self._fazer(
            "sair da turma",
            lambda: self._casos_de_uso.sair_da_turma.executar(self._usuario, vista.resumo.id),
            lambda _: f"Você saiu da turma de {nome}. A mensalidade já paga não é devolvida.",
        )

    def _fazer[T](self, acao: str, funcao: Callable[[], T], sucesso: Callable[[T], str]) -> None:
        """Roda a ação; se der certo, lê as turmas de novo e mostra o resultado."""
        match executar(acao, self._usuario.email, funcao):
            case Feito(valor):
                self.recarregar()
                mostrar_sucesso(self.mensagem, sucesso(valor))
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)
