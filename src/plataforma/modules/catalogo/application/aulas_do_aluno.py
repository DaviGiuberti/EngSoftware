"""Casos de uso do aluno no catálogo (H14, H16, H17): ver a vitrine, com destaque para o nível dele
em cada matéria (R15, R31), ver os pacotes que comprou, com o progresso, assistir à aula pelo link
do YouTube (R61) e marcar a aula como concluída (R62). No reembolso, o vendas apaga as aulas
concluídas do pacote pelo ApagarAulasConcluidas (R63).

O acesso de cada pacote vem do módulo vendas pela porta Acessos (ADR 0002).
"""

from dataclasses import dataclass
from datetime import datetime

from plataforma.compartilhado.relogio import Relogio
from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.catalogo.application.casos_de_uso import (
    ConsultaDePacotes,
    ResumoDoPacote,
)
from plataforma.modules.catalogo.application.portas import (
    Acessos,
    RepositorioDeAulasConcluidas,
    RepositorioDePacotes,
)
from plataforma.modules.catalogo.domain.aulas_do_aluno import (
    AcessoAoPacote,
    AulaConcluida,
    AulaConcluidaNaMateria,
    concluir_aula,
    exigir_acesso,
    progresso,
    vitrine,
)
from plataforma.modules.catalogo.domain.pacote import AulaNaoEncontrada, Pacote
from plataforma.modules.identidade.application.casos_de_uso import ConsultaDeProfessores
from plataforma.modules.identidade.domain.autorizacao import exigir_perfil
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.nivelamento.application.consulta_de_niveis import ConsultaDeNiveis


@dataclass(frozen=True)
class PacoteNaVitrine:
    """Um pacote da vitrine: em destaque se é do nível do aluno na matéria (R31) e, se o aluno já
    o comprou, o acesso dele (R12)."""

    resumo: ResumoDoPacote
    destaque: bool
    acesso: AcessoAoPacote | None


@dataclass(frozen=True)
class PacoteComprado:
    """Um pacote que o aluno comprou, mesmo arquivado depois (R12), com o acesso, as aulas que ele
    concluiu, pelo número da aula (R62), e o progresso: quantas concluiu e quantas o pacote tem."""

    resumo: ResumoDoPacote
    acesso: AcessoAoPacote
    concluidas: dict[int, datetime]
    progresso: tuple[int, int]


class _CasoDoAluno:
    """Dependências e passos comuns aos casos de uso do aluno no catálogo."""

    def __init__(
        self,
        pacotes: RepositorioDePacotes,
        concluidas: RepositorioDeAulasConcluidas,
        materias: ConsultaDeMaterias,
        professores: ConsultaDeProfessores,
        niveis: ConsultaDeNiveis,
        acessos: Acessos,
        relogio: Relogio,
        transacao: Transacao,
    ) -> None:
        self._pacotes = pacotes
        self._concluidas = concluidas
        self._materias = materias
        self._professores = professores
        self._niveis = niveis
        self._acessos = acessos
        self._relogio = relogio
        self._transacao = transacao

    def _resumir(self, pacotes: list[Pacote]) -> list[ResumoDoPacote]:
        """Os pacotes com o nome da matéria e o e-mail do professor, em ordem de matéria, nível e
        título."""
        nomes = {materia.id: materia.nome for materia in self._materias.listar()}
        emails = {professor.id: professor.email for professor in self._professores.listar()}
        resumos = [
            ResumoDoPacote(pacote, nomes[pacote.materia_id], emails[pacote.professor_id])
            for pacote in pacotes
        ]
        return sorted(
            resumos, key=lambda r: (r.nome_da_materia, r.pacote.nivel, r.pacote.titulo, r.pacote.id)
        )

    def _pacote_com_acesso(
        self, aluno: Usuario, pacote_id: int, agora: datetime
    ) -> tuple[Pacote, AcessoAoPacote | None]:
        pacote = ConsultaDePacotes(self._pacotes).obter(pacote_id)
        return pacote, self._acessos.do_aluno(aluno.id, agora).get(pacote.id)


class VerVitrine(_CasoDoAluno):
    """H14: o aluno vê os pacotes publicados de todos os níveis, com os do nível dele em cada
    matéria primeiro, em destaque (R15, R31)."""

    def executar(self, aluno: Usuario) -> list[PacoteNaVitrine]:
        exigir_perfil(aluno, Perfil.ALUNO, "ver a vitrine de pacotes")
        agora = self._relogio.agora()
        resumos = {r.pacote.id: r for r in self._resumir(self._pacotes.publicados())}
        ordenados = [resumo.pacote for resumo in resumos.values()]
        acessos = self._acessos.do_aluno(aluno.id, agora)
        niveis = self._niveis.niveis_do_aluno(aluno.id)
        return [
            PacoteNaVitrine(resumos[item.pacote.id], item.destaque, acessos.get(item.pacote.id))
            for item in vitrine(ordenados, niveis)
        ]


class VerPacotesComprados(_CasoDoAluno):
    """H16: o aluno vê os pacotes que comprou, mesmo os arquivados depois (R12), com o acesso, que
    pode ter vencido, e as aulas que concluiu."""

    def executar(self, aluno: Usuario) -> list[PacoteComprado]:
        exigir_perfil(aluno, Perfil.ALUNO, "ver os pacotes comprados")
        acessos = self._acessos.do_aluno(aluno.id, self._relogio.agora())
        consulta = ConsultaDePacotes(self._pacotes)
        resumos = self._resumir([consulta.obter(pacote_id) for pacote_id in acessos])
        concluidas = self._concluidas.do_aluno(aluno.id)
        return [
            PacoteComprado(
                resumo,
                acessos[resumo.pacote.id],
                {c.numero: c.concluida_em for c in concluidas if c.pacote_id == resumo.pacote.id},
                progresso(resumo.pacote, concluidas),
            )
            for resumo in resumos
        ]


class AssistirAula(_CasoDoAluno):
    """H16: com o acesso ativo, o aluno recebe o link do YouTube da aula, que a tela abre no
    navegador (R12, R61)."""

    def executar(self, aluno: Usuario, pacote_id: int, numero: int) -> str:
        exigir_perfil(aluno, Perfil.ALUNO, "assistir à aula gravada")
        pacote, acesso = self._pacote_com_acesso(aluno, pacote_id, self._relogio.agora())
        exigir_acesso(acesso)
        aula = next((a for a in pacote.aulas if a.numero == numero), None)
        if aula is None:
            raise AulaNaoEncontrada(f"O pacote não tem a {numero}ª aula.")
        return aula.link


class ConcluirAula(_CasoDoAluno):
    """H16: com o acesso ativo, o aluno marca a aula como concluída, de uma vez só (R62)."""

    def executar(self, aluno: Usuario, pacote_id: int, numero: int) -> AulaConcluida:
        exigir_perfil(aluno, Perfil.ALUNO, "concluir aula gravada")
        agora = self._relogio.agora()
        with self._transacao():
            pacote, acesso = self._pacote_com_acesso(aluno, pacote_id, agora)
            concluida = concluir_aula(
                pacote, numero, acesso, self._concluidas.do_aluno(aluno.id), agora
            )
            self._concluidas.adicionar(aluno.id, concluida)
            return concluida


class ConsultaDeAulasConcluidas:
    """As métricas leem as aulas concluídas sem ler as tabelas do catalogo (ADR 0002)."""

    def __init__(self, concluidas: RepositorioDeAulasConcluidas) -> None:
        self._concluidas = concluidas

    def de_todos(self) -> list[AulaConcluidaNaMateria]:
        """As aulas concluídas de todos os alunos, com a matéria e o nível do pacote (R64)."""
        return self._concluidas.de_todos()


class ApagarAulasConcluidas:
    """R63: o reembolso apaga as aulas que o aluno concluiu no pacote. O vendas chama este serviço
    dentro da transação do reembolso, sem ler a tabela do catalogo (ADR 0002)."""

    def __init__(self, concluidas: RepositorioDeAulasConcluidas) -> None:
        self._concluidas = concluidas

    def executar(self, aluno_id: int, pacote_id: int) -> None:
        self._concluidas.apagar(aluno_id, pacote_id)


@dataclass(frozen=True)
class CasosDeUsoDoAluno:
    """Os casos de uso do aluno no catálogo, montados pelo main.py e entregues às telas."""

    ver_vitrine: VerVitrine
    ver_pacotes_comprados: VerPacotesComprados
    assistir: AssistirAula
    concluir_aula: ConcluirAula


def montar_casos_de_uso_do_aluno(
    pacotes: RepositorioDePacotes,
    concluidas: RepositorioDeAulasConcluidas,
    materias: ConsultaDeMaterias,
    professores: ConsultaDeProfessores,
    niveis: ConsultaDeNiveis,
    acessos: Acessos,
    relogio: Relogio,
    transacao: Transacao,
) -> CasosDeUsoDoAluno:
    """Todos os casos de uso do aluno no catálogo recebem as mesmas dependências."""
    dependencias = (pacotes, concluidas, materias, professores, niveis, acessos, relogio, transacao)
    return CasosDeUsoDoAluno(
        ver_vitrine=VerVitrine(*dependencias),
        ver_pacotes_comprados=VerPacotesComprados(*dependencias),
        assistir=AssistirAula(*dependencias),
        concluir_aula=ConcluirAula(*dependencias),
    )
