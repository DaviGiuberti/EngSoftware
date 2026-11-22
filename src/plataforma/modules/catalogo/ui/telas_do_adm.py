"""Tela "Pacotes" do ADM (H34, H35): ver as aulas do pacote em revisão, definir o preço e
publicá-lo ou devolvê-lo ao professor (R15, R38, R59), mudar o preço, arquivar e publicar de novo
(R15, R59)."""

from collections.abc import Callable

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.compartilhado.dinheiro import formatar_reais
from plataforma.modules.catalogo.application.casos_de_uso import (
    CasosDeUsoDoCatalogo,
    ResumoDoPacote,
)
from plataforma.modules.catalogo.domain.pacote import Pacote
from plataforma.modules.catalogo.ui.comum import (
    descrever_estado,
    descrever_preco,
    linhas_das_aulas,
    reescolher,
)
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.materias.domain.materia import nome_do_nivel
from plataforma.ui_comum import (
    linha_escolhida,
    mostrar_aviso,
    mostrar_recusa,
    mostrar_sucesso,
    preencher,
    tabela_de_escolha,
    titulo,
)

NENHUM_ESCOLHIDO = "Escolha um pacote na tabela para ver as aulas."
SEM_PACOTES = "Nenhum pacote ainda. Os professores criam os pacotes e os enviam para revisão."
EXPLICACAO = (
    "Revise as aulas do pacote em revisão e publique-o com o preço ou devolva-o ao professor, que "
    "pode editá-lo e enviá-lo de novo. O preço pode mudar depois e vale para as compras seguintes. "
    "O pacote arquivado sai da vitrine, e quem comprou mantém o acesso."
)


def _preco(pacote: Pacote) -> str:
    return formatar_reais(pacote.preco_em_centavos or 0)


class TelaPacotes(QWidget):
    def __init__(self, usuario: Usuario, casos_de_uso: CasosDeUsoDoCatalogo) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_de_uso = casos_de_uso
        self._resumos: list[ResumoDoPacote] = []
        self._escolhido: Pacote | None = None

        self.tabela = tabela_de_escolha(
            ["Título", "Matéria", "Nível", "Professor", "Aulas", "Estado", "Preço"]
        )
        self.escolhido = QLabel(NENHUM_ESCOLHIDO)
        self.aulas = tabela_de_escolha(["Nº", "Título", "Link do YouTube"])
        self.preco = QDoubleSpinBox()
        self.preco.setPrefix("R$ ")
        self.preco.setDecimals(2)
        self.preco.setRange(0, 100_000)
        self.botao_publicar = QPushButton("Publicar")
        self.botao_devolver = QPushButton("Devolver ao professor")
        self.botao_mudar_preco = QPushButton("Mudar preço")
        self.botao_arquivar = QPushButton("Arquivar")
        self.botao_publicar_de_novo = QPushButton("Publicar de novo")
        formulario = QFormLayout()
        formulario.addRow("Preço", self.preco)
        botoes = QHBoxLayout()
        for botao in (
            self.botao_publicar,
            self.botao_devolver,
            self.botao_mudar_preco,
            self.botao_arquivar,
            self.botao_publicar_de_novo,
        ):
            botoes.addWidget(botao)
        botoes.addStretch()
        self._grupo_do_escolhido = QGroupBox("Pacote escolhido")
        coluna_do_escolhido = QVBoxLayout(self._grupo_do_escolhido)
        coluna_do_escolhido.addWidget(self.escolhido)
        coluna_do_escolhido.addWidget(self.aulas, 1)
        coluna_do_escolhido.addLayout(formulario)
        coluna_do_escolhido.addLayout(botoes)

        explicacao = QLabel(EXPLICACAO)
        explicacao.setWordWrap(True)
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Pacotes"))
        coluna.addWidget(explicacao)
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(self._grupo_do_escolhido, 1)
        coluna.addWidget(self.mensagem)

        self.tabela.itemSelectionChanged.connect(self._escolher)
        self.botao_publicar.clicked.connect(self._publicar)
        self.botao_devolver.clicked.connect(self._devolver)
        self.botao_mudar_preco.clicked.connect(self._mudar_preco)
        self.botao_arquivar.clicked.connect(self._arquivar)
        self.botao_publicar_de_novo.clicked.connect(self._publicar_de_novo)
        self.recarregar()

    def recarregar(self) -> None:
        """Lê de novo os pacotes, mantendo o pacote escolhido."""
        ver = self._casos_de_uso.ver_pacotes
        match executar("ver os pacotes", self._usuario.email, lambda: ver.executar(self._usuario)):
            case Feito(resumos):
                self._mostrar(resumos)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _mostrar(self, resumos: list[ResumoDoPacote]) -> None:
        if not resumos:
            mostrar_aviso(self.mensagem, SEM_PACOTES)
        escolhido_antes = self._escolhido.id if self._escolhido else None
        preencher(
            self.tabela,
            [
                [
                    resumo.pacote.titulo,
                    resumo.nome_da_materia,
                    nome_do_nivel(resumo.pacote.nivel),
                    resumo.email_do_professor,
                    str(len(resumo.pacote.aulas)),
                    descrever_estado(resumo.pacote),
                    descrever_preco(resumo.pacote),
                ]
                for resumo in resumos
            ],
        )
        self._resumos = resumos
        reescolher(self.tabela, resumos, escolhido_antes)
        self._escolher()

    def _escolher(self) -> None:
        linha = linha_escolhida(self.tabela)
        resumo = None if linha is None else self._resumos[linha]
        self._escolhido = None if resumo is None else resumo.pacote
        self._grupo_do_escolhido.setEnabled(resumo is not None)
        if resumo is None:
            self.escolhido.setText(NENHUM_ESCOLHIDO)
            preencher(self.aulas, [])
            return
        pacote = resumo.pacote
        self.escolhido.setText(
            f"{pacote.titulo}, de {resumo.nome_da_materia} {nome_do_nivel(pacote.nivel)}, por "
            f"{resumo.email_do_professor}, {descrever_estado(pacote)}"
        )
        preencher(self.aulas, linhas_das_aulas(pacote.aulas))
        # O campo mostra o preço que o pacote tem, e o ADM o troca para publicar ou mudar.
        self.preco.setValue((pacote.preco_em_centavos or 0) / 100)

    def _preco_em_centavos(self) -> int:
        return round(self.preco.value() * 100)

    def _publicar(self) -> None:
        preco = self._preco_em_centavos()
        self._no_escolhido(
            "publicar pacote",
            lambda pacote_id: self._casos_de_uso.publicar.executar(
                self._usuario, pacote_id, preco
            ),
            lambda pacote: f"{pacote.titulo} publicado por {_preco(pacote)}.",
        )

    def _devolver(self) -> None:
        self._no_escolhido(
            "devolver pacote",
            lambda pacote_id: self._casos_de_uso.devolver.executar(self._usuario, pacote_id),
            lambda pacote: f"{pacote.titulo} devolvido ao professor, em rascunho.",
        )

    def _mudar_preco(self) -> None:
        preco = self._preco_em_centavos()
        self._no_escolhido(
            "mudar o preço do pacote",
            lambda pacote_id: self._casos_de_uso.mudar_preco.executar(
                self._usuario, pacote_id, preco
            ),
            lambda pacote: f"{pacote.titulo} passa a custar {_preco(pacote)}.",
        )

    def _arquivar(self) -> None:
        self._no_escolhido(
            "arquivar pacote",
            lambda pacote_id: self._casos_de_uso.arquivar.executar(self._usuario, pacote_id),
            lambda pacote: (
                f"{pacote.titulo} arquivado: saiu da vitrine, e quem comprou mantém o acesso."
            ),
        )

    def _publicar_de_novo(self) -> None:
        self._no_escolhido(
            "publicar pacote de novo",
            lambda pacote_id: self._casos_de_uso.publicar_de_novo.executar(
                self._usuario, pacote_id
            ),
            lambda pacote: f"{pacote.titulo} publicado de novo por {_preco(pacote)}.",
        )

    def _no_escolhido(
        self, acao: str, fazer: Callable[[int], Pacote], sucesso: Callable[[Pacote], str]
    ) -> None:
        """Faz a ação no pacote escolhido, lê tudo de novo e mostra o resultado."""
        escolhido = self._escolhido
        if escolhido is None:
            return
        match executar(acao, self._usuario.email, lambda: fazer(escolhido.id)):
            case Feito(pacote):
                self.recarregar()
                mostrar_sucesso(self.mensagem, sucesso(pacote))
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)
                # O campo volta ao preço que o pacote tem.
                self._escolher()
