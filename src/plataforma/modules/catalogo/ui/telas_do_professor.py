"""Tela "Meus pacotes" do professor (H25, H26): criar o pacote numa matéria em que ele está
habilitado (R56), mudar o título, adicionar, corrigir e remover aulas (R58) e enviar o pacote
para revisão (R15, R57)."""

from collections.abc import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.modules.catalogo.application.casos_de_uso import (
    CasosDeUsoDoCatalogo,
    MeusPacotes,
    ResumoDoPacote,
)
from plataforma.modules.catalogo.domain.pacote import Pacote
from plataforma.modules.catalogo.ui.comum import (
    descrever_estado,
    descrever_preco,
    linha_escolhida,
    linhas_das_aulas,
    preencher,
    reescolher,
    tabela_de_escolha,
)
from plataforma.modules.identidade.domain.usuario import Usuario
from plataforma.modules.materias.domain.materia import Materia, nome_do_nivel
from plataforma.modules.materias.ui.telas import preencher_com_materias
from plataforma.ui_comum import mostrar_aviso, mostrar_recusa, mostrar_sucesso, titulo

NENHUM_ESCOLHIDO = "Escolha um pacote na tabela para editar as aulas."
EXPLICACAO = (
    "O pacote começa em rascunho. Com pelo menos 1 aula, envie para revisão: o ADM define o preço "
    "e publica ou devolve. Em revisão, o pacote não pode ser editado. Publicado, você adiciona e "
    "corrige aulas sem nova revisão, mas não remove nenhuma."
)


class TelaMeusPacotes(QWidget):
    def __init__(self, usuario: Usuario, casos_de_uso: CasosDeUsoDoCatalogo) -> None:
        super().__init__()
        self._usuario = usuario
        self._casos_de_uso = casos_de_uso
        self._resumos: list[ResumoDoPacote] = []
        self._materias: dict[int, Materia] = {}
        self._escolhido: Pacote | None = None

        self.tabela = tabela_de_escolha(["Título", "Matéria", "Nível", "Aulas", "Estado", "Preço"])

        self.titulo = QLineEdit()
        self.materia = QComboBox()
        self.nivel = QComboBox()
        self.botao_criar = QPushButton("Criar pacote")
        formulario_do_novo = QFormLayout()
        formulario_do_novo.addRow("Título", self.titulo)
        formulario_do_novo.addRow("Matéria", self.materia)
        formulario_do_novo.addRow("Nível", self.nivel)
        novo = QGroupBox("Novo pacote")
        coluna_do_novo = QVBoxLayout(novo)
        coluna_do_novo.addLayout(formulario_do_novo)
        coluna_do_novo.addWidget(self.botao_criar)

        self.escolhido = QLabel(NENHUM_ESCOLHIDO)
        self.titulo_escolhido = QLineEdit()
        self.botao_mudar_titulo = QPushButton("Mudar título")
        self.aulas = tabela_de_escolha(["Nº", "Título", "Link do YouTube"])
        self.titulo_da_aula = QLineEdit()
        self.link_da_aula = QLineEdit()
        self.link_da_aula.setPlaceholderText("https://www.youtube.com/watch?v=… ou https://youtu.be/…")
        self.botao_adicionar_aula = QPushButton("Adicionar aula")
        self.botao_corrigir_aula = QPushButton("Corrigir aula escolhida")
        self.botao_remover_aula = QPushButton("Remover aula escolhida")
        self.botao_enviar = QPushButton("Enviar para revisão")
        linha_do_titulo = QHBoxLayout()
        linha_do_titulo.addWidget(self.titulo_escolhido, 1)
        linha_do_titulo.addWidget(self.botao_mudar_titulo)
        formulario_da_aula = QFormLayout()
        formulario_da_aula.addRow("Título do pacote", linha_do_titulo)
        formulario_da_aula.addRow("Título da aula", self.titulo_da_aula)
        formulario_da_aula.addRow("Link da aula", self.link_da_aula)
        botoes_da_aula = QHBoxLayout()
        for botao in (self.botao_adicionar_aula, self.botao_corrigir_aula, self.botao_remover_aula):
            botoes_da_aula.addWidget(botao)
        botoes_da_aula.addStretch()
        botoes_da_aula.addWidget(self.botao_enviar)
        self._grupo_do_escolhido = QGroupBox("Pacote escolhido")
        coluna_do_escolhido = QVBoxLayout(self._grupo_do_escolhido)
        coluna_do_escolhido.addWidget(self.escolhido)
        coluna_do_escolhido.addWidget(self.aulas, 1)
        coluna_do_escolhido.addLayout(formulario_da_aula)
        coluna_do_escolhido.addLayout(botoes_da_aula)

        explicacao = QLabel(EXPLICACAO)
        explicacao.setWordWrap(True)
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)

        coluna = QVBoxLayout(self)
        coluna.addWidget(titulo("Meus pacotes"))
        coluna.addWidget(explicacao)
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(novo)
        coluna.addWidget(self._grupo_do_escolhido, 2)
        coluna.addWidget(self.mensagem)

        self.materia.currentIndexChanged.connect(self._mostrar_niveis)
        self.tabela.itemSelectionChanged.connect(self._escolher)
        self.aulas.itemSelectionChanged.connect(self._escolher_aula)
        self.botao_criar.clicked.connect(self._criar)
        self.botao_mudar_titulo.clicked.connect(self._mudar_titulo)
        self.botao_adicionar_aula.clicked.connect(self._adicionar_aula)
        self.botao_corrigir_aula.clicked.connect(self._corrigir_aula)
        self.botao_remover_aula.clicked.connect(self._remover_aula)
        self.botao_enviar.clicked.connect(self._enviar)
        self.recarregar()

    def recarregar(self) -> None:
        """Lê de novo os pacotes e as matérias, mantendo o pacote escolhido."""
        ver = self._casos_de_uso.ver_meus_pacotes
        resultado = executar(
            "ver os seus pacotes", self._usuario.email, lambda: ver.executar(self._usuario)
        )
        match resultado:
            case Feito(meus):
                self._mostrar(meus)
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _mostrar(self, meus: MeusPacotes) -> None:
        self._materias = {materia.id: materia for materia in meus.materias}
        preencher_com_materias(self.materia, meus.materias)
        self._mostrar_niveis()
        # R56: sem habilitação, o professor não tem em que matéria criar pacote.
        self.botao_criar.setEnabled(bool(meus.materias))
        if not meus.materias:
            mostrar_aviso(
                self.mensagem,
                "Você ainda não tem habilitação em nenhuma matéria. O ADM habilita os professores.",
            )
        escolhido_antes = self._escolhido.id if self._escolhido else None
        preencher(
            self.tabela,
            [
                [
                    resumo.pacote.titulo,
                    resumo.nome_da_materia,
                    nome_do_nivel(resumo.pacote.nivel),
                    str(len(resumo.pacote.aulas)),
                    descrever_estado(resumo.pacote),
                    descrever_preco(resumo.pacote),
                ]
                for resumo in meus.pacotes
            ],
        )
        self._resumos = meus.pacotes
        reescolher(self.tabela, meus.pacotes, escolhido_antes)
        self._escolher()

    def _mostrar_niveis(self) -> None:
        """R56: o pacote é de um dos níveis da matéria escolhida."""
        escolhido = self.nivel.currentData()
        self.nivel.clear()
        materia = self._materias.get(self.materia.currentData())
        if materia is None:
            return
        for nivel in range(1, materia.nivel_maximo + 1):
            self.nivel.addItem(nome_do_nivel(nivel), nivel)
        self.nivel.setCurrentIndex(max(self.nivel.findData(escolhido), 0))

    def _escolher(self) -> None:
        linha = linha_escolhida(self.tabela)
        resumo = None if linha is None else self._resumos[linha]
        self._escolhido = None if resumo is None else resumo.pacote
        self._grupo_do_escolhido.setEnabled(resumo is not None)
        if resumo is None:
            self.escolhido.setText(NENHUM_ESCOLHIDO)
            self.titulo_escolhido.clear()
            preencher(self.aulas, [])
            return
        pacote = resumo.pacote
        self.escolhido.setText(
            f"{pacote.titulo}, de {resumo.nome_da_materia} {nome_do_nivel(pacote.nivel)}, "
            f"{descrever_estado(pacote)}"
        )
        self.titulo_escolhido.setText(pacote.titulo)
        preencher(self.aulas, linhas_das_aulas(pacote.aulas))

    def _escolher_aula(self) -> None:
        """A aula escolhida vai para os campos, para o professor corrigi-la."""
        linha = linha_escolhida(self.aulas)
        if self._escolhido is None or linha is None:
            return
        aula = self._escolhido.aulas[linha]
        self.titulo_da_aula.setText(aula.titulo)
        self.link_da_aula.setText(aula.link)

    def _numero_da_aula(self) -> int | None:
        linha = linha_escolhida(self.aulas)
        if linha is None:
            mostrar_aviso(self.mensagem, "Escolha uma aula na lista.")
            return None
        return linha + 1

    def _criar(self) -> None:
        titulo_do_pacote = self.titulo.text()
        materia_id, nivel = self.materia.currentData(), self.nivel.currentData()
        resultado = executar(
            "criar pacote",
            self._usuario.email,
            lambda: self._casos_de_uso.criar_pacote.executar(
                self._usuario, titulo_do_pacote, materia_id, nivel
            ),
        )
        match resultado:
            case Feito(pacote):
                self.titulo.clear()
                self._escolhido = pacote
                self.recarregar()
                mostrar_sucesso(self.mensagem, f"Pacote {pacote.titulo} criado em rascunho.")
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)

    def _mudar_titulo(self) -> None:
        novo = self.titulo_escolhido.text()
        self._no_escolhido(
            "editar pacote",
            lambda pacote_id: self._casos_de_uso.mudar_titulo.executar(
                self._usuario, pacote_id, novo
            ),
            lambda pacote: f"Título mudado para {pacote.titulo}.",
        )

    def _adicionar_aula(self) -> None:
        titulo_da_aula, link = self.titulo_da_aula.text(), self.link_da_aula.text()
        self._no_escolhido(
            "editar pacote",
            lambda pacote_id: self._casos_de_uso.adicionar_aula.executar(
                self._usuario, pacote_id, titulo_da_aula, link
            ),
            lambda pacote: f"{len(pacote.aulas)}ª aula adicionada.",
            limpar_aula=True,
        )

    def _corrigir_aula(self) -> None:
        numero = self._numero_da_aula()
        if numero is None:
            return
        titulo_da_aula, link = self.titulo_da_aula.text(), self.link_da_aula.text()
        self._no_escolhido(
            "editar pacote",
            lambda pacote_id: self._casos_de_uso.corrigir_aula.executar(
                self._usuario, pacote_id, numero, titulo_da_aula, link
            ),
            lambda _: f"{numero}ª aula corrigida.",
            limpar_aula=True,
        )

    def _remover_aula(self) -> None:
        numero = self._numero_da_aula()
        if numero is None:
            return
        self._no_escolhido(
            "editar pacote",
            lambda pacote_id: self._casos_de_uso.remover_aula.executar(
                self._usuario, pacote_id, numero
            ),
            lambda _: f"{numero}ª aula removida.",
            limpar_aula=True,
        )

    def _enviar(self) -> None:
        self._no_escolhido(
            "enviar pacote para revisão",
            lambda pacote_id: self._casos_de_uso.enviar_para_revisao.executar(
                self._usuario, pacote_id
            ),
            lambda pacote: f"{pacote.titulo} enviado para revisão. O ADM publica ou devolve.",
        )

    def _no_escolhido(
        self,
        acao: str,
        fazer: Callable[[int], Pacote],
        sucesso: Callable[[Pacote], str],
        limpar_aula: bool = False,
    ) -> None:
        """Faz a ação no pacote escolhido, lê tudo de novo e mostra o resultado."""
        escolhido = self._escolhido
        if escolhido is None:
            return
        match executar(acao, self._usuario.email, lambda: fazer(escolhido.id)):
            case Feito(pacote):
                if limpar_aula:
                    self.titulo_da_aula.clear()
                    self.link_da_aula.clear()
                self.recarregar()
                mostrar_sucesso(self.mensagem, sucesso(pacote))
            case Falhou(mensagem):
                mostrar_recusa(self.mensagem, mensagem)
