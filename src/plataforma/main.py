"""Monta o app: banco na pasta de dados, migrações, log, casos de uso e janela principal."""

import os
import sys
from functools import partial
from pathlib import Path

from PySide6.QtWidgets import QApplication

from plataforma.banco import (
    PASTA_MIGRACOES,
    aplicar_migracoes,
    conectar,
    transacao,
    verificar_banco,
)
from plataforma.janela_principal import CasosDeUso, JanelaPrincipal
from plataforma.log import configurar_log, fechar_log
from plataforma.modules.identidade.application.casos_de_uso import (
    CadastrarAluno,
    CasosDeUsoDaIdentidade,
    CriarPrimeiroAdm,
    Entrar,
)
from plataforma.modules.identidade.infra.repositorio_de_usuarios import (
    RepositorioDeUsuariosSqlite,
)
from plataforma.modules.materias.application.casos_de_uso import (
    CadastrarMateria,
    CasosDeUsoDeMaterias,
    ConsultaDeMaterias,
)
from plataforma.modules.materias.infra.repositorio_de_materias import (
    RepositorioDeMateriasSqlite,
)
from plataforma.modules.nivelamento.application.casos_de_uso import (
    CadastrarQuestao,
    CasosDeUsoDoNivelamento,
    ListarQuestoes,
)
from plataforma.modules.nivelamento.infra.repositorio_de_questoes import (
    RepositorioDeQuestoesSqlite,
)


def pasta_de_dados_padrao() -> Path:
    """Pasta do banco, das cópias e do log, a mesma para o código e para qualquer .exe."""
    return Path(os.environ["LOCALAPPDATA"]) / "Plataforma"


def criar_janela(pasta_de_dados: Path) -> JanelaPrincipal:
    """Aplica as migrações, liga o log, monta os casos de uso e a janela.

    É o único lugar que conhece as implementações da infra/: os casos de uso recebem as
    portas prontas. Ao fechar a janela, a conexão e o log são fechados.
    """
    caminho_banco = pasta_de_dados / "plataforma.db"
    aplicar_migracoes(caminho_banco, PASTA_MIGRACOES, pasta_de_dados / "copias")
    configurar_log(pasta_de_dados / "logs")
    conexao = conectar(caminho_banco)
    em_transacao = partial(transacao, conexao)

    usuarios = RepositorioDeUsuariosSqlite(conexao)
    materias = RepositorioDeMateriasSqlite(conexao)
    consulta_de_materias = ConsultaDeMaterias(materias)
    questoes = RepositorioDeQuestoesSqlite(conexao)
    casos_de_uso = CasosDeUso(
        identidade=CasosDeUsoDaIdentidade(
            cadastrar_aluno=CadastrarAluno(usuarios, em_transacao),
            entrar=Entrar(usuarios),
            criar_primeiro_adm=CriarPrimeiroAdm(usuarios, em_transacao),
        ),
        materias=CasosDeUsoDeMaterias(
            cadastrar_materia=CadastrarMateria(materias, em_transacao),
            consulta=consulta_de_materias,
        ),
        nivelamento=CasosDeUsoDoNivelamento(
            cadastrar_questao=CadastrarQuestao(questoes, consulta_de_materias, em_transacao),
            listar_questoes=ListarQuestoes(questoes),
        ),
    )

    def ao_fechar() -> None:
        conexao.close()
        fechar_log()

    return JanelaPrincipal(
        banco_ok=verificar_banco(caminho_banco), casos_de_uso=casos_de_uso, ao_fechar=ao_fechar
    )


def main() -> int:
    """Abre o app e devolve o código de saída quando a janela fecha."""
    app = QApplication(sys.argv)
    janela = criar_janela(pasta_de_dados_padrao())
    janela.show()
    return app.exec()
