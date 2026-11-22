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
from plataforma.compartilhado.relogio import Relogio
from plataforma.janela_principal import CasosDeUso, JanelaPrincipal
from plataforma.log import configurar_log, fechar_log
from plataforma.modules.catalogo.application.aulas_do_aluno import (
    ApagarAulasConcluidas,
    ConsultaDeAulasConcluidas,
    montar_casos_de_uso_do_aluno,
)
from plataforma.modules.catalogo.application.casos_de_uso import (
    ConsultaDePacotes,
    montar_casos_de_uso,
)
from plataforma.modules.catalogo.infra.repositorio_de_aulas_concluidas import (
    RepositorioDeAulasConcluidasSqlite,
)
from plataforma.modules.catalogo.infra.repositorio_de_pacotes import RepositorioDePacotesSqlite
from plataforma.modules.identidade.application.casos_de_uso import (
    CadastrarAluno,
    CadastrarProfessor,
    CasosDeUsoDaIdentidade,
    ConsultaDeAlunos,
    ConsultaDeProfessores,
    CriarPrimeiroAdm,
    Entrar,
    HabilitarProfessor,
)
from plataforma.modules.identidade.infra.repositorio_de_professores import (
    RepositorioDeProfessoresSqlite,
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
from plataforma.modules.metricas.application.casos_de_uso import VerMetricas
from plataforma.modules.nivelamento.application.casos_de_uso import (
    CadastrarQuestao,
    CasosDeUsoDoNivelamento,
    ListarQuestoes,
)
from plataforma.modules.nivelamento.application.certificados import VerMeusCertificados
from plataforma.modules.nivelamento.application.consulta_de_niveis import ConsultaDeNiveis
from plataforma.modules.nivelamento.application.fazer_nivelamento import (
    ConcluirNivelamento,
    DarMaisTempo,
    FecharNivelamento,
    IniciarNivelamento,
    LiberarRefazer,
    RegistrarTempo,
    ResponderQuestao,
    VerMeusNiveis,
)
from plataforma.modules.nivelamento.application.historico import HistoricoDoNivelamento
from plataforma.modules.nivelamento.application.promocao import Promocoes
from plataforma.modules.nivelamento.infra.repositorio_de_nivelamentos import (
    RepositorioDeNivelamentosSqlite,
)
from plataforma.modules.nivelamento.infra.repositorio_de_questoes import (
    RepositorioDeQuestoesSqlite,
)
from plataforma.modules.turmas.application.casos_de_uso import (
    CasosDeUsoDeTurmas,
    CriarTurma,
    EncerrarTurma,
    MudarHorario,
    TrocarProfessor,
    VerMinhasTurmas,
    VerTurmas,
)
from plataforma.modules.turmas.application.consulta_de_presencas import ConsultaDePresencas
from plataforma.modules.turmas.application.em_dia import AtualizarTurmas, TurmasEmDia
from plataforma.modules.turmas.application.matricula import (
    CasosDeUsoDaMatricula,
    ConfirmarVaga,
    EntrarNaListaDeEspera,
    Matricular,
    PagarMensalidade,
    SairDaTurma,
    VerTurmasDoAluno,
    VerVagasPerdidas,
)
from plataforma.modules.turmas.application.presenca import (
    CasosDeUsoDasAulas,
    CorrigirPresenca,
    LancarPresenca,
    MarcarAulaNaoRealizada,
    VerAulasDaTurma,
)
from plataforma.modules.turmas.application.prova_final import (
    CasosDeUsoDaProvaFinal,
    CorrigirNota,
    LancarNota,
    VerProvaFinal,
)
from plataforma.modules.turmas.infra.repositorio_de_turmas import RepositorioDeTurmasSqlite
from plataforma.modules.vendas.application.casos_de_uso import (
    ConsultaDeAcessos,
    montar_casos_de_uso_de_vendas,
)
from plataforma.modules.vendas.infra.repositorio_de_compras import RepositorioDeComprasSqlite
from plataforma.relogio import RelogioDoSistema


def pasta_de_dados_padrao() -> Path:
    """Pasta do banco, das cópias e do log, a mesma para o código e para qualquer .exe."""
    return Path(os.environ["LOCALAPPDATA"]) / "Plataforma"


def criar_janela(pasta_de_dados: Path, relogio: Relogio | None = None) -> JanelaPrincipal:
    """Aplica as migrações, liga o log, monta os casos de uso e a janela.

    É o único lugar que conhece as implementações da infra/: os casos de uso recebem as
    portas prontas. O relógio é o do sistema, a não ser que um teste passe outro. Ao fechar
    a janela, a conexão e o log são fechados.
    """
    relogio = relogio or RelogioDoSistema()
    caminho_banco = pasta_de_dados / "plataforma.db"
    aplicar_migracoes(caminho_banco, PASTA_MIGRACOES, pasta_de_dados / "copias")
    configurar_log(pasta_de_dados / "logs")
    conexao = conectar(caminho_banco)
    em_transacao = partial(transacao, conexao)

    usuarios = RepositorioDeUsuariosSqlite(conexao)
    alunos = ConsultaDeAlunos(usuarios)
    professores = RepositorioDeProfessoresSqlite(conexao)
    consulta_de_professores = ConsultaDeProfessores(professores)
    materias = RepositorioDeMateriasSqlite(conexao)
    consulta_de_materias = ConsultaDeMaterias(materias)
    questoes = RepositorioDeQuestoesSqlite(conexao)
    nivelamentos = RepositorioDeNivelamentosSqlite(conexao)
    do_aluno = (nivelamentos, questoes, consulta_de_materias, relogio, em_transacao)
    turmas = RepositorioDeTurmasSqlite(conexao)
    niveis = ConsultaDeNiveis(nivelamentos)
    # Todo caso de uso das turmas põe as turmas em dia antes de agir, e a promoção é do
    # nivelamento (ADR 0002).
    promocoes = Promocoes(nivelamentos, consulta_de_materias)
    em_dia = TurmasEmDia(turmas, consulta_de_materias, promocoes)
    leitura_das_turmas = (
        turmas,
        consulta_de_materias,
        consulta_de_professores,
        relogio,
        em_transacao,
        em_dia,
    )
    do_aluno_nas_turmas = (
        turmas,
        consulta_de_materias,
        consulta_de_professores,
        niveis,
        relogio,
        em_transacao,
        em_dia,
    )
    das_aulas = (
        turmas,
        consulta_de_materias,
        consulta_de_professores,
        alunos,
        relogio,
        em_transacao,
        em_dia,
    )
    pacotes = RepositorioDePacotesSqlite(conexao)
    compras = RepositorioDeComprasSqlite(conexao)
    concluidas = RepositorioDeAulasConcluidasSqlite(conexao)
    casos_de_uso = CasosDeUso(
        identidade=CasosDeUsoDaIdentidade(
            cadastrar_aluno=CadastrarAluno(usuarios, em_transacao),
            entrar=Entrar(usuarios),
            criar_primeiro_adm=CriarPrimeiroAdm(usuarios, em_transacao),
            cadastrar_professor=CadastrarProfessor(usuarios, em_transacao),
            habilitar_professor=HabilitarProfessor(
                professores, consulta_de_materias, em_transacao
            ),
            consulta_de_professores=consulta_de_professores,
        ),
        materias=CasosDeUsoDeMaterias(
            cadastrar_materia=CadastrarMateria(materias, em_transacao),
            consulta=consulta_de_materias,
        ),
        nivelamento=CasosDeUsoDoNivelamento(
            cadastrar_questao=CadastrarQuestao(questoes, consulta_de_materias, em_transacao),
            listar_questoes=ListarQuestoes(questoes),
            iniciar=IniciarNivelamento(*do_aluno),
            responder=ResponderQuestao(*do_aluno),
            registrar_tempo=RegistrarTempo(*do_aluno),
            fechar=FecharNivelamento(*do_aluno),
            concluir=ConcluirNivelamento(*do_aluno),
            ver_meus_niveis=VerMeusNiveis(nivelamentos, questoes, consulta_de_materias),
            ver_meus_certificados=VerMeusCertificados(nivelamentos, consulta_de_materias),
            dar_mais_tempo=DarMaisTempo(
                nivelamentos, consulta_de_materias, alunos, relogio, em_transacao
            ),
            liberar_refazer=LiberarRefazer(
                nivelamentos, consulta_de_materias, alunos, em_transacao
            ),
        ),
        turmas=CasosDeUsoDeTurmas(
            criar_turma=CriarTurma(*leitura_das_turmas),
            trocar_professor=TrocarProfessor(*leitura_das_turmas),
            mudar_horario=MudarHorario(turmas),
            encerrar_turma=EncerrarTurma(
                turmas, consulta_de_materias, relogio, em_transacao, em_dia
            ),
            ver_turmas=VerTurmas(*leitura_das_turmas),
            ver_minhas_turmas=VerMinhasTurmas(*leitura_das_turmas),
            atualizar=AtualizarTurmas(em_dia, relogio, em_transacao),
        ),
        matricula=CasosDeUsoDaMatricula(
            ver_turmas_do_aluno=VerTurmasDoAluno(*do_aluno_nas_turmas),
            matricular=Matricular(*do_aluno_nas_turmas),
            entrar_na_lista=EntrarNaListaDeEspera(*do_aluno_nas_turmas),
            confirmar_vaga=ConfirmarVaga(*do_aluno_nas_turmas),
            sair_da_turma=SairDaTurma(*do_aluno_nas_turmas),
            pagar_mensalidade=PagarMensalidade(*do_aluno_nas_turmas),
            ver_vagas_perdidas=VerVagasPerdidas(*do_aluno_nas_turmas),
        ),
        aulas=CasosDeUsoDasAulas(
            ver_aulas=VerAulasDaTurma(*das_aulas),
            lancar_presenca=LancarPresenca(*das_aulas),
            corrigir_presenca=CorrigirPresenca(*das_aulas),
            marcar_nao_realizada=MarcarAulaNaoRealizada(*das_aulas),
        ),
        prova_final=CasosDeUsoDaProvaFinal(
            ver_prova_final=VerProvaFinal(*das_aulas),
            lancar_nota=LancarNota(*das_aulas),
            corrigir_nota=CorrigirNota(*das_aulas),
        ),
        catalogo=montar_casos_de_uso(
            pacotes, consulta_de_materias, consulta_de_professores, em_transacao
        ),
        # O catalogo pergunta o acesso ao vendas pela porta Acessos (ADR 0002).
        catalogo_do_aluno=montar_casos_de_uso_do_aluno(
            pacotes,
            concluidas,
            consulta_de_materias,
            consulta_de_professores,
            niveis,
            ConsultaDeAcessos(compras),
            relogio,
            em_transacao,
        ),
        # No reembolso, o vendas apaga as aulas concluídas pelo serviço do catalogo (R63).
        vendas=montar_casos_de_uso_de_vendas(
            compras,
            ConsultaDePacotes(pacotes),
            ApagarAulasConcluidas(concluidas),
            relogio,
            em_transacao,
        ),
        # As métricas só leem as consultas públicas dos outros módulos (ADR 0002).
        metricas=VerMetricas(
            HistoricoDoNivelamento(nivelamentos),
            ConsultaDePresencas(turmas),
            ConsultaDeAulasConcluidas(concluidas),
            relogio,
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
