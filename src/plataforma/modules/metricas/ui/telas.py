"""Aba "Métricas" do ADM (H36): a M1, a M2 e a M3 dos nivelamentos concluídos no mês escolhido, com
a meta de cada uma e como o número foi calculado (R64 a R67)."""

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.metricas.application.casos_de_uso import Metricas, VerMetricas
from plataforma.modules.metricas.domain.metricas import (
    ContinuidadeNaTrilha,
    TaxaDeProgressao,
    TempoAteNivelCerto,
)
from plataforma.ui_comum import (
    mostrar_aviso,
    mostrar_recusa,
    preencher,
    tabela_de_escolha,
    titulo,
)

MESES = [
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
]
EXPLICACAO = (
    "Cada aluno conta em cada matéria pelo primeiro nivelamento que concluiu nela, no mês da "
    "conclusão. A atividade de estudo é a presença numa aula de turma ou uma aula gravada "
    "concluída."
)


def formatar_numero(valor: float) -> str:
    """Sem casa decimal quando o número é inteiro; com uma, e vírgula, quando não é."""
    if valor == int(valor):
        return str(int(valor))
    return f"{valor:.1f}".replace(".", ",")


def formatar_porcentagem(valor: float | None) -> str:
    return "—" if valor is None else f"{formatar_numero(round(valor, 1))}%"


def linha_da_m1(m1: TaxaDeProgressao) -> list[str]:
    """R65: entram todos os nivelados do mês, e a tela diz quantos ainda estão no prazo."""
    if m1.nivelados == 0:
        detalhe = "Nenhum nivelamento concluído no mês."
    else:
        detalhe = (
            f"{m1.promovidos} de {m1.nivelados} nivelados promovidos em até 6 meses; "
            f"{m1.ainda_no_prazo} ainda dentro dos 6 meses."
        )
    nome = "M1 · taxa de progressão"
    return [nome, formatar_porcentagem(m1.porcentagem), "30% ou mais em 6 meses", detalhe]


def linha_da_m2(m2: ContinuidadeNaTrilha) -> list[str]:
    """R66: só entra quem se nivelou há pelo menos 28 dias."""
    if m2.elegiveis == 0:
        detalhe = "Nenhum nivelado do mês tem 4 semanas ainda."
    else:
        detalhe = (
            f"{m2.com_atividade} de {m2.elegiveis} nivelados há pelo menos 4 semanas estudaram "
            "na 4ª semana."
        )
    nome = "M2 · continuidade na trilha"
    return [nome, formatar_porcentagem(m2.porcentagem), "50% ou mais na 4ª semana", detalhe]


def linha_da_m3(m3: TempoAteNivelCerto) -> list[str]:
    """R67: a mediana, com uma casa decimal, de quem já estudou no nível recebido."""
    mediana = m3.mediana
    if mediana is None:
        valor = "—"
        detalhe = "Nenhum nivelado do mês estudou no nível recebido ainda."
    else:
        valor = f"{formatar_numero(mediana)} {'dia' if mediana == 1 else 'dias'}"
        alunos = len(m3.dias)
        quem = "1 aluno que já estudou" if alunos == 1 else f"{alunos} alunos que já estudaram"
        detalhe = f"Mediana de {quem} no nível recebido."
    return ["M3 · tempo até estudar no nível certo", valor, "mediana de até 3 dias", detalhe]


class TelaMetricas(QWidget):
    def __init__(self, usuario: Usuario, ver_metricas: VerMetricas) -> None:
        super().__init__()
        self._usuario = usuario
        self._ver_metricas = ver_metricas

        self.mes = QComboBox()
        for numero, nome in enumerate(MESES, start=1):
            self.mes.addItem(nome, numero)
        self.ano = QSpinBox()
        self.ano.setRange(2000, 2100)
        ano, mes = ver_metricas.mes_de_agora()
        self.mes.setCurrentIndex(mes - 1)
        self.ano.setValue(ano)
        self.botao_ver = QPushButton("Ver métricas")
        linha_do_periodo = QHBoxLayout()
        linha_do_periodo.addWidget(QLabel("Nivelamentos concluídos em"))
        linha_do_periodo.addWidget(self.mes)
        linha_do_periodo.addWidget(QLabel("de"))
        linha_do_periodo.addWidget(self.ano)
        linha_do_periodo.addWidget(self.botao_ver)
        linha_do_periodo.addStretch()

        self.tabela = tabela_de_escolha(["Métrica", "Valor", "Meta", "Como foi calculada"])
        explicacao = QLabel(EXPLICACAO)
        explicacao.setWordWrap(True)
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Métricas"))
        coluna.addWidget(explicacao)
        coluna.addLayout(linha_do_periodo)
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(self.mensagem)

        self.botao_ver.clicked.connect(self.recarregar)
        self.recarregar()

    def recarregar(self) -> None:
        """Calcula de novo as métricas do mês escolhido."""
        ano, mes = self.ano.value(), int(self.mes.currentData())
        resultado = executar(
            "ver as métricas",
            self._usuario.email,
            lambda: self._ver_metricas.executar(self._usuario, ano, mes),
        )
        match resultado:
            case Feito(metricas):
                self._mostrar(metricas)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _mostrar(self, metricas: Metricas) -> None:
        preencher(
            self.tabela,
            [linha_da_m1(metricas.m1), linha_da_m2(metricas.m2), linha_da_m3(metricas.m3)],
        )
        mostrar_aviso(
            self.mensagem,
            f"Métricas dos nivelamentos concluídos em {MESES[metricas.mes - 1]} de "
            f"{metricas.ano}.",
        )
