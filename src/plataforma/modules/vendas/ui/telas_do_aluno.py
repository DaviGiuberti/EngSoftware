"""Aba "Pacotes" do aluno (H14, H15, H16, H17): a vitrine com os pacotes publicados de todos os
níveis, com destaque para o nível dele (R15, R31), a compra (R12, R60) e os pacotes comprados, com
as aulas, que abrem no navegador (R61, ADR 0004), a aula concluída (R62) e o reembolso (R13,
R63)."""

from collections.abc import Callable
from datetime import date

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.compartilhado.dinheiro import formatar_reais
from plataforma.modules.catalogo.application.aulas_do_aluno import (
    CasosDeUsoDoAluno,
    PacoteComprado,
    PacoteNaVitrine,
)
from plataforma.modules.catalogo.domain.aulas_do_aluno import AcessoAoPacote
from plataforma.modules.catalogo.ui.comum import (
    descrever_preco,
    linha_escolhida,
    preencher,
    tabela_de_escolha,
)
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.materias.domain.materia import nome_do_nivel
from plataforma.modules.vendas.application.casos_de_uso import CasosDeUsoDeVendas
from plataforma.ui_comum import mostrar_aviso, mostrar_recusa, mostrar_sucesso, titulo

DESTAQUE = "★ seu nível"
SEM_PACOTES = "Nenhum pacote à venda ainda."
EXPLICACAO = (
    "Você compra pacotes de qualquer nível, com ou sem nivelamento; os do seu nível em cada "
    "matéria aparecem primeiro. A compra dá 12 meses de acesso. As aulas abrem no navegador."
)
EXPLICACAO_DO_REEMBOLSO = (
    "O reembolso pode ser pedido até as 23h59 do 7º dia depois da compra. Ele encerra o acesso e "
    "apaga as aulas concluídas do pacote. Comprado de novo, o pacote não tem mais reembolso."
)


def descrever_acesso(acesso: AcessoAoPacote | None) -> str:
    """R12 e R60: até quando vai o acesso ou quando ele venceu."""
    if acesso is None:
        return "—"
    if acesso.ativo:
        return f"até {acesso.ate:%d/%m/%Y}"
    return f"venceu em {acesso.ate:%d/%m/%Y}"


def _abrir_no_navegador(link: str) -> None:
    QDesktopServices.openUrl(QUrl(link))


def _formatar_data(quando: date) -> str:
    return f"{quando:%d/%m/%Y}"


class TelaPacotesDoAluno(QWidget):
    def __init__(
        self, usuario: Usuario, catalogo: CasosDeUsoDoAluno, vendas: CasosDeUsoDeVendas
    ) -> None:
        super().__init__()
        self._usuario = usuario
        self._catalogo = catalogo
        self._vendas = vendas
        self._na_vitrine: list[PacoteNaVitrine] = []
        self._comprados: list[PacoteComprado] = []
        self._escolhido_id: int | None = None
        # Os testes trocam por uma função que só guarda o link, sem abrir o navegador.
        self.abrir_link: Callable[[str], object] = _abrir_no_navegador

        self.vitrine = tabela_de_escolha(
            ["Destaque", "Título", "Matéria", "Nível", "Aulas", "Preço", "Seu acesso"]
        )
        self.botao_comprar = QPushButton("Comprar pacote escolhido")
        grupo_da_vitrine = QGroupBox("Vitrine")
        coluna_da_vitrine = QVBoxLayout(grupo_da_vitrine)
        explicacao = QLabel(EXPLICACAO)
        explicacao.setWordWrap(True)
        coluna_da_vitrine.addWidget(explicacao)
        coluna_da_vitrine.addWidget(self.vitrine, 1)
        linha_da_compra = QHBoxLayout()
        linha_da_compra.addStretch()
        linha_da_compra.addWidget(self.botao_comprar)
        coluna_da_vitrine.addLayout(linha_da_compra)

        self.comprados = tabela_de_escolha(
            ["Título", "Matéria", "Nível", "Aulas concluídas", "Acesso"]
        )
        self.aulas = tabela_de_escolha(["Nº", "Título", "Situação"])
        self.botao_assistir = QPushButton("Assistir no navegador")
        self.botao_concluir = QPushButton("Marcar como concluída")
        self.botao_reembolso = QPushButton("Pedir reembolso do pacote")
        grupo_dos_comprados = QGroupBox("Meus pacotes")
        coluna_dos_comprados = QVBoxLayout(grupo_dos_comprados)
        coluna_dos_comprados.addWidget(self.comprados, 1)
        coluna_dos_comprados.addWidget(QLabel("Aulas do pacote escolhido"))
        coluna_dos_comprados.addWidget(self.aulas, 1)
        explicacao_do_reembolso = QLabel(EXPLICACAO_DO_REEMBOLSO)
        explicacao_do_reembolso.setWordWrap(True)
        coluna_dos_comprados.addWidget(explicacao_do_reembolso)
        linha_das_aulas = QHBoxLayout()
        linha_das_aulas.addWidget(self.botao_reembolso)
        linha_das_aulas.addStretch()
        linha_das_aulas.addWidget(self.botao_assistir)
        linha_das_aulas.addWidget(self.botao_concluir)
        coluna_dos_comprados.addLayout(linha_das_aulas)

        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Pacotes"))
        coluna.addWidget(grupo_da_vitrine, 1)
        coluna.addWidget(grupo_dos_comprados, 1)
        coluna.addWidget(self.mensagem)

        self.comprados.itemSelectionChanged.connect(self._escolher)
        self.botao_comprar.clicked.connect(self._comprar)
        self.botao_assistir.clicked.connect(self._assistir)
        self.botao_concluir.clicked.connect(self._concluir)
        self.botao_reembolso.clicked.connect(self._pedir_reembolso)
        self.recarregar()

    def recarregar(self) -> None:
        """Lê de novo a vitrine e os pacotes comprados, mantendo o pacote escolhido."""
        resultado = executar("ver a vitrine de pacotes", self._usuario.email, self._ler)
        match resultado:
            case Feito((na_vitrine, comprados)):
                self._mostrar_vitrine(na_vitrine)
                self._mostrar_comprados(comprados)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _ler(self) -> tuple[list[PacoteNaVitrine], list[PacoteComprado]]:
        return (
            self._catalogo.ver_vitrine.executar(self._usuario),
            self._catalogo.ver_pacotes_comprados.executar(self._usuario),
        )

    def _mostrar_vitrine(self, na_vitrine: list[PacoteNaVitrine]) -> None:
        if not na_vitrine:
            mostrar_aviso(self.mensagem, SEM_PACOTES)
        preencher(
            self.vitrine,
            [
                [
                    DESTAQUE if item.destaque else "",
                    item.resumo.pacote.titulo,
                    item.resumo.nome_da_materia,
                    nome_do_nivel(item.resumo.pacote.nivel),
                    str(len(item.resumo.pacote.aulas)),
                    descrever_preco(item.resumo.pacote),
                    descrever_acesso(item.acesso),
                ]
                for item in na_vitrine
            ],
        )
        self._na_vitrine = na_vitrine
        self.botao_comprar.setEnabled(bool(na_vitrine))

    def _mostrar_comprados(self, comprados: list[PacoteComprado]) -> None:
        escolhido_antes = self._escolhido_id
        preencher(
            self.comprados,
            [
                [
                    comprado.resumo.pacote.titulo,
                    comprado.resumo.nome_da_materia,
                    nome_do_nivel(comprado.resumo.pacote.nivel),
                    f"{comprado.progresso[0]} de {comprado.progresso[1]}",
                    descrever_acesso(comprado.acesso),
                ]
                for comprado in comprados
            ],
        )
        self._comprados = comprados
        ids = [comprado.resumo.pacote.id for comprado in comprados]
        if escolhido_antes in ids:
            self.comprados.selectRow(ids.index(escolhido_antes))
        self._escolher()

    def _escolhido(self) -> PacoteComprado | None:
        linha = linha_escolhida(self.comprados)
        return None if linha is None else self._comprados[linha]

    def _escolher(self) -> None:
        comprado = self._escolhido()
        self._escolhido_id = None if comprado is None else comprado.resumo.pacote.id
        if comprado is None:
            preencher(self.aulas, [])
            return
        preencher(
            self.aulas,
            [
                [
                    str(aula.numero),
                    aula.titulo,
                    (
                        f"concluída em {_formatar_data(comprado.concluidas[aula.numero])}"
                        if aula.numero in comprado.concluidas
                        else ""
                    ),
                ]
                for aula in comprado.resumo.pacote.aulas
            ],
        )

    def _comprar(self) -> None:
        linha = linha_escolhida(self.vitrine)
        if linha is None:
            mostrar_aviso(self.mensagem, "Escolha um pacote na vitrine.")
            return
        pacote = self._na_vitrine[linha].resumo.pacote
        resultado = executar(
            "comprar pacote",
            self._usuario.email,
            lambda: self._vendas.comprar.executar(self._usuario, pacote.id),
        )
        match resultado:
            case Feito(feita):
                self._escolhido_id = pacote.id
                self.recarregar()
                mostrar_sucesso(
                    self.mensagem,
                    f"Você comprou {pacote.titulo} por "
                    f"{formatar_reais(feita.compra.valor_em_centavos)}. O acesso vai até "
                    f"{_formatar_data(feita.acesso_ate)}.",
                )
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _aula_escolhida(self) -> tuple[int, int] | None:
        """O pacote e o número da aula escolhida."""
        comprado, linha = self._escolhido(), linha_escolhida(self.aulas)
        if comprado is None or linha is None:
            mostrar_aviso(self.mensagem, "Escolha um pacote e uma aula.")
            return None
        return comprado.resumo.pacote.id, linha + 1

    def _assistir(self) -> None:
        escolhida = self._aula_escolhida()
        if escolhida is None:
            return
        pacote_id, numero = escolhida
        resultado = executar(
            "assistir à aula gravada",
            self._usuario.email,
            lambda: self._catalogo.assistir.executar(self._usuario, pacote_id, numero),
        )
        match resultado:
            case Feito(link):
                self.abrir_link(link)
                mostrar_sucesso(self.mensagem, f"A {numero}ª aula abriu no navegador.")
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _pedir_reembolso(self) -> None:
        comprado = self._escolhido()
        if comprado is None:
            mostrar_aviso(self.mensagem, "Escolha um pacote em Meus pacotes.")
            return
        pacote = comprado.resumo.pacote
        resultado = executar(
            "pedir reembolso",
            self._usuario.email,
            lambda: self._vendas.pedir_reembolso.executar(self._usuario, pacote.id),
        )
        match resultado:
            case Feito(reembolsada):
                self.recarregar()
                mostrar_sucesso(
                    self.mensagem,
                    f"Reembolso de {pacote.titulo} aceito: "
                    f"{formatar_reais(reembolsada.valor_em_centavos)} devolvidos. O acesso foi "
                    "encerrado.",
                )
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _concluir(self) -> None:
        escolhida = self._aula_escolhida()
        if escolhida is None:
            return
        pacote_id, numero = escolhida
        resultado = executar(
            "concluir aula gravada",
            self._usuario.email,
            lambda: self._catalogo.concluir_aula.executar(self._usuario, pacote_id, numero),
        )
        match resultado:
            case Feito(_):
                self.recarregar()
                mostrar_sucesso(self.mensagem, f"{numero}ª aula marcada como concluída.")
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)
