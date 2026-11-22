"""Casos de uso do catálogo (H25, H26, H34, H35).

O professor cria o pacote numa matéria em que está habilitado, edita o título e as aulas e o envia
para revisão (R15, R56, R57, R58). Só quem criou o pacote o edita (R56). O ADM publica com o preço,
devolve, muda o preço, arquiva e publica de novo (R15, R38, R59). Os outros módulos, como as
vendas, leem os pacotes pela ConsultaDePacotes (ADR 0002).
"""

from collections.abc import Callable
from dataclasses import dataclass

from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.catalogo.application.portas import RepositorioDePacotes
from plataforma.modules.catalogo.domain.pacote import (
    Pacote,
    PacoteNaoEncontrado,
    adicionar_aula,
    arquivar,
    corrigir_aula,
    devolver,
    enviar_para_revisao,
    mudar_preco,
    mudar_titulo,
    nova_aula,
    novo_pacote,
    publicar,
    publicar_de_novo,
    remover_aula,
)
from plataforma.modules.identidade.application.casos_de_uso import ConsultaDeProfessores
from plataforma.modules.identidade.domain.autorizacao import exigir_dono, exigir_perfil
from plataforma.modules.identidade.domain.professor import exigir_habilitacao
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.materias.domain.materia import Materia

SO_QUEM_CRIOU = "Só o professor que criou o pacote pode editá-lo."

type Mudanca = Callable[[Pacote], Pacote]


@dataclass(frozen=True)
class ResumoDoPacote:
    """Um pacote como as telas mostram: com o nome da matéria e o e-mail do professor."""

    pacote: Pacote
    nome_da_materia: str
    email_do_professor: str


@dataclass(frozen=True)
class MeusPacotes:
    """Os pacotes do professor e as matérias em que ele pode criar pacote (R56)."""

    pacotes: list[ResumoDoPacote]
    materias: list[Materia]


class ConsultaDePacotes:
    """Leitura dos pacotes para os outros módulos, como a vitrine e a compra (ADR 0002)."""

    def __init__(self, pacotes: RepositorioDePacotes) -> None:
        self._pacotes = pacotes

    def obter(self, pacote_id: int) -> Pacote:
        pacote = self._pacotes.buscar(pacote_id)
        if pacote is None:
            raise PacoteNaoEncontrado()
        return pacote

    def publicados(self) -> list[Pacote]:
        """Os pacotes à venda, na ordem em que foram criados (R15)."""
        return self._pacotes.publicados()


class _CasoDoCatalogo:
    """Dependências e passos comuns aos casos de uso do catálogo."""

    def __init__(
        self,
        pacotes: RepositorioDePacotes,
        materias: ConsultaDeMaterias,
        professores: ConsultaDeProfessores,
        transacao: Transacao,
    ) -> None:
        self._pacotes = pacotes
        self._materias = materias
        self._professores = professores
        self._transacao = transacao

    def _resumir(self, pacotes: list[Pacote]) -> list[ResumoDoPacote]:
        nomes = {materia.id: materia.nome for materia in self._materias.listar()}
        emails = {professor.id: professor.email for professor in self._professores.listar()}
        return [
            ResumoDoPacote(pacote, nomes[pacote.materia_id], emails[pacote.professor_id])
            for pacote in pacotes
        ]

    def _mudar(self, pacote_id: int, mudanca: Mudanca, professor: Usuario | None = None) -> Pacote:
        """Lê o pacote, aplica a mudança e grava, tudo numa transação (RNF05).

        Com o professor, só quem criou o pacote o muda (R56).
        """
        with self._transacao():
            pacote = ConsultaDePacotes(self._pacotes).obter(pacote_id)
            if professor is not None:
                exigir_dono(professor, pacote.professor_id, SO_QUEM_CRIOU)
            mudado = mudanca(pacote)
            self._pacotes.salvar(mudado)
            return mudado

    def _do_professor(
        self, usuario: Usuario, acao: str, pacote_id: int, mudanca: Mudanca
    ) -> Pacote:
        exigir_perfil(usuario, Perfil.PROFESSOR, acao)
        return self._mudar(pacote_id, mudanca, professor=usuario)

    def _do_adm(self, usuario: Usuario, acao: str, pacote_id: int, mudanca: Mudanca) -> Pacote:
        exigir_perfil(usuario, Perfil.ADM, acao)
        return self._mudar(pacote_id, mudanca)


class CriarPacote(_CasoDoCatalogo):
    """H25: o professor cria o pacote em rascunho, numa matéria em que está habilitado (R56)."""

    def executar(self, usuario: Usuario, titulo: str, materia_id: int, nivel: int) -> Pacote:
        exigir_perfil(usuario, Perfil.PROFESSOR, "criar pacote")
        materia = self._materias.obter(materia_id)
        with self._transacao():
            professor = self._professores.obter(usuario.id)
            exigir_habilitacao(professor, materia.id, materia.nome)
            novo = novo_pacote(
                titulo, materia.id, nivel, materia.nivel_maximo, materia.nome, usuario.id
            )
            return self._pacotes.adicionar(novo)


class MudarTitulo(_CasoDoCatalogo):
    """R58: o professor muda o título do pacote em rascunho ou publicado."""

    def executar(self, usuario: Usuario, pacote_id: int, titulo: str) -> Pacote:
        return self._do_professor(
            usuario, "editar pacote", pacote_id, lambda pacote: mudar_titulo(pacote, titulo)
        )


class AdicionarAula(_CasoDoCatalogo):
    """H25 e H26: o professor adiciona uma aula ao rascunho ou ao publicado, sem nova revisão."""

    def executar(self, usuario: Usuario, pacote_id: int, titulo: str, link: str) -> Pacote:
        aula = nova_aula(titulo, link)
        return self._do_professor(
            usuario, "editar pacote", pacote_id, lambda pacote: adicionar_aula(pacote, aula)
        )


class CorrigirAula(_CasoDoCatalogo):
    """H26: o professor corrige o título e o link de uma aula do rascunho ou do publicado."""

    def executar(
        self, usuario: Usuario, pacote_id: int, numero: int, titulo: str, link: str
    ) -> Pacote:
        aula = nova_aula(titulo, link)
        return self._do_professor(
            usuario,
            "editar pacote",
            pacote_id,
            lambda pacote: corrigir_aula(pacote, numero, aula),
        )


class RemoverAula(_CasoDoCatalogo):
    """R58: o professor remove uma aula, só do rascunho."""

    def executar(self, usuario: Usuario, pacote_id: int, numero: int) -> Pacote:
        return self._do_professor(
            usuario, "editar pacote", pacote_id, lambda pacote: remover_aula(pacote, numero)
        )


class EnviarParaRevisao(_CasoDoCatalogo):
    """H25: o professor envia o rascunho, com pelo menos 1 aula, para revisão (R15, R57)."""

    def executar(self, usuario: Usuario, pacote_id: int) -> Pacote:
        return self._do_professor(
            usuario, "enviar pacote para revisão", pacote_id, enviar_para_revisao
        )


class PublicarPacote(_CasoDoCatalogo):
    """H34: o ADM define o preço e publica o pacote em revisão (R15, R59)."""

    def executar(self, usuario: Usuario, pacote_id: int, preco_em_centavos: int) -> Pacote:
        return self._do_adm(
            usuario,
            "publicar pacote",
            pacote_id,
            lambda pacote: publicar(pacote, preco_em_centavos),
        )


class DevolverPacote(_CasoDoCatalogo):
    """H34: o ADM devolve o pacote em revisão, que volta para rascunho (R38)."""

    def executar(self, usuario: Usuario, pacote_id: int) -> Pacote:
        return self._do_adm(usuario, "devolver pacote", pacote_id, devolver)


class MudarPreco(_CasoDoCatalogo):
    """H34 e H35: o ADM muda o preço do publicado ou do arquivado (R15, R59)."""

    def executar(self, usuario: Usuario, pacote_id: int, preco_em_centavos: int) -> Pacote:
        return self._do_adm(
            usuario,
            "mudar o preço do pacote",
            pacote_id,
            lambda pacote: mudar_preco(pacote, preco_em_centavos),
        )


class ArquivarPacote(_CasoDoCatalogo):
    """H35: o ADM tira o pacote publicado da vitrine (R15)."""

    def executar(self, usuario: Usuario, pacote_id: int) -> Pacote:
        return self._do_adm(usuario, "arquivar pacote", pacote_id, arquivar)


class PublicarDeNovo(_CasoDoCatalogo):
    """H35: o ADM publica de novo o arquivado, com o preço que ele tinha (R15, R59)."""

    def executar(self, usuario: Usuario, pacote_id: int) -> Pacote:
        return self._do_adm(usuario, "publicar pacote de novo", pacote_id, publicar_de_novo)


class VerMeusPacotes(_CasoDoCatalogo):
    """O professor vê os pacotes que criou e as matérias em que pode criar pacote (R56)."""

    def executar(self, usuario: Usuario) -> MeusPacotes:
        exigir_perfil(usuario, Perfil.PROFESSOR, "ver os seus pacotes")
        professor = self._professores.obter(usuario.id)
        habilitadas = [
            materia
            for materia in self._materias.listar()
            if materia.id in professor.materias_habilitadas
        ]
        return MeusPacotes(self._resumir(self._pacotes.do_professor(usuario.id)), habilitadas)


class VerPacotes(_CasoDoCatalogo):
    """H34 e H35: o ADM vê todos os pacotes, em qualquer estado."""

    def executar(self, usuario: Usuario) -> list[ResumoDoPacote]:
        exigir_perfil(usuario, Perfil.ADM, "ver todos os pacotes")
        return self._resumir(self._pacotes.listar())


@dataclass(frozen=True)
class CasosDeUsoDoCatalogo:
    """Os casos de uso do módulo, montados pelo main.py e entregues às telas."""

    criar_pacote: CriarPacote
    mudar_titulo: MudarTitulo
    adicionar_aula: AdicionarAula
    corrigir_aula: CorrigirAula
    remover_aula: RemoverAula
    enviar_para_revisao: EnviarParaRevisao
    publicar: PublicarPacote
    devolver: DevolverPacote
    mudar_preco: MudarPreco
    arquivar: ArquivarPacote
    publicar_de_novo: PublicarDeNovo
    ver_meus_pacotes: VerMeusPacotes
    ver_pacotes: VerPacotes


def montar_casos_de_uso(
    pacotes: RepositorioDePacotes,
    materias: ConsultaDeMaterias,
    professores: ConsultaDeProfessores,
    transacao: Transacao,
) -> CasosDeUsoDoCatalogo:
    """Todos os casos de uso do catálogo recebem as mesmas dependências."""
    dependencias = (pacotes, materias, professores, transacao)
    return CasosDeUsoDoCatalogo(
        criar_pacote=CriarPacote(*dependencias),
        mudar_titulo=MudarTitulo(*dependencias),
        adicionar_aula=AdicionarAula(*dependencias),
        corrigir_aula=CorrigirAula(*dependencias),
        remover_aula=RemoverAula(*dependencias),
        enviar_para_revisao=EnviarParaRevisao(*dependencias),
        publicar=PublicarPacote(*dependencias),
        devolver=DevolverPacote(*dependencias),
        mudar_preco=MudarPreco(*dependencias),
        arquivar=ArquivarPacote(*dependencias),
        publicar_de_novo=PublicarDeNovo(*dependencias),
        ver_meus_pacotes=VerMeusPacotes(*dependencias),
        ver_pacotes=VerPacotes(*dependencias),
    )
