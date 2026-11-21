"""Telas da identidade (H38): primeiro ADM, entrar e cadastro de aluno.

As telas só chamam os casos de uso, pelo executar: as regras e a checagem de perfil ficam nos
casos de uso (RNF07), e a tela mostra o motivo de cada recusa (RNF02).
"""

from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from plataforma.acoes import Falhou, Feito, executar
from plataforma.modules.identidade.application.casos_de_uso import (
    CadastrarAluno,
    CriarPrimeiroAdm,
    Entrar,
)
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario

NOME_DO_PERFIL = {Perfil.ALUNO: "aluno", Perfil.PROFESSOR: "professor", Perfil.ADM: "ADM"}


class _TelaDeEmailESenha(QWidget):
    """Base das três telas: título, explicação, e-mail, senha, botões e a mensagem de recusa."""

    entrou = Signal(object)

    def __init__(self, titulo: str, explicacao: str) -> None:
        super().__init__()
        self.email = QLineEdit()
        self.email.setPlaceholderText("nome@exemplo.com")
        self.senha = QLineEdit()
        self.senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.senha.setPlaceholderText("pelo menos 8 caracteres")
        self.senha.returnPressed.connect(self._enviar)
        self.mensagem = QLabel()
        self.mensagem.setWordWrap(True)
        self.mensagem.setStyleSheet("color: #b3261e")

        rotulo_titulo = QLabel(titulo)
        rotulo_titulo.setStyleSheet("font-size: 18px; font-weight: bold")
        rotulo_explicacao = QLabel(explicacao)
        rotulo_explicacao.setWordWrap(True)
        formulario = QFormLayout()
        formulario.addRow("E-mail", self.email)
        formulario.addRow("Senha", self.senha)
        self._botoes = QHBoxLayout()

        conteudo = QWidget()
        conteudo.setMaximumWidth(420)
        coluna = QVBoxLayout(conteudo)
        coluna.addStretch()
        coluna.addWidget(rotulo_titulo)
        coluna.addWidget(rotulo_explicacao)
        coluna.addLayout(formulario)
        coluna.addLayout(self._botoes)
        coluna.addWidget(self.mensagem)
        coluna.addStretch()
        centro = QHBoxLayout(self)
        centro.addStretch()
        centro.addWidget(conteudo)
        centro.addStretch()

    def limpar(self) -> None:
        self.email.clear()
        self.senha.clear()
        self.mensagem.clear()

    def _adicionar_botoes(self, *botoes: QPushButton) -> None:
        for botao in botoes:
            self._botoes.addWidget(botao)

    def _enviar(self) -> None:
        raise NotImplementedError

    def _executar(self, acao: str, funcao: Callable[[], Usuario]) -> None:
        """Roda o caso de uso: se der certo, avisa quem entrou; se não, mostra o motivo."""
        match executar(acao, self.email.text(), funcao):
            case Feito(usuario):
                self.limpar()
                self.entrou.emit(usuario)
            case Falhou(mensagem):
                self.mensagem.setText(mensagem)


class TelaPrimeiroAdm(_TelaDeEmailESenha):
    def __init__(self, criar_primeiro_adm: CriarPrimeiroAdm) -> None:
        super().__init__(
            "Primeira abertura",
            "Crie o ADM, que administra a plataforma. Não existe senha padrão: guarde o "
            "e-mail e a senha que você definir.",
        )
        self._criar_primeiro_adm = criar_primeiro_adm
        self.botao_criar = QPushButton("Criar ADM")
        self.botao_criar.clicked.connect(self._enviar)
        self._adicionar_botoes(self.botao_criar)

    def _enviar(self) -> None:
        email, senha = self.email.text(), self.senha.text()
        self._executar(
            "criar primeiro ADM", lambda: self._criar_primeiro_adm.executar(email, senha)
        )


class TelaEntrar(_TelaDeEmailESenha):
    pediu_cadastro = Signal()

    def __init__(self, entrar: Entrar) -> None:
        super().__init__("Entrar", "Use o e-mail e a senha da sua conta.")
        self._entrar = entrar
        self.botao_entrar = QPushButton("Entrar")
        self.botao_entrar.clicked.connect(self._enviar)
        self.botao_cadastro = QPushButton("Criar conta de aluno")
        self.botao_cadastro.clicked.connect(self._pedir_cadastro)
        self._adicionar_botoes(self.botao_entrar, self.botao_cadastro)

    def _enviar(self) -> None:
        email, senha = self.email.text(), self.senha.text()
        self._executar("entrar", lambda: self._entrar.executar(email, senha))

    def _pedir_cadastro(self) -> None:
        self.limpar()
        self.pediu_cadastro.emit()


class TelaCadastro(_TelaDeEmailESenha):
    voltou = Signal()

    def __init__(self, cadastrar_aluno: CadastrarAluno) -> None:
        super().__init__(
            "Criar conta de aluno",
            "Cadastre-se para fazer o nivelamento e estudar no seu nível.",
        )
        self._cadastrar_aluno = cadastrar_aluno
        self.botao_cadastrar = QPushButton("Cadastrar")
        self.botao_cadastrar.clicked.connect(self._enviar)
        self.botao_voltar = QPushButton("Voltar")
        self.botao_voltar.clicked.connect(self._voltar)
        self._adicionar_botoes(self.botao_cadastrar, self.botao_voltar)

    def _enviar(self) -> None:
        email, senha = self.email.text(), self.senha.text()
        self._executar("cadastrar aluno", lambda: self._cadastrar_aluno.executar(email, senha))

    def _voltar(self) -> None:
        self.limpar()
        self.voltou.emit()
