"""Pacote gravado (H25, H26, H34, H35): o fluxo rascunho → em revisão → publicado → arquivado
(R15) e a devolução para rascunho (R38).

O pacote é de uma matéria e de um nível, que não mudam (R56). Ele vai para revisão com pelo menos
1 aula, e o professor edita só o rascunho e o publicado (R57). Cada aula é um vídeo do YouTube, e
o publicado não perde aulas (R58). O ADM define o preço, maior que zero, ao publicar e pode mudá-lo
depois; o arquivado volta com o preço que tinha (R59).

Quem pode fazer cada passo (o professor que criou o pacote ou o ADM) é conferido nos casos de uso.
"""

import re
from dataclasses import dataclass, replace
from enum import StrEnum
from urllib.parse import parse_qs, urlsplit

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.materias.domain.materia import nome_do_nivel

# O id de um vídeo do YouTube tem 11 letras, números, "-" ou "_".
_ID_DO_VIDEO = re.compile(r"[A-Za-z0-9_-]{11}")
_SITES_DO_YOUTUBE = {"youtube.com", "www.youtube.com", "m.youtube.com"}


class EstadoPacote(StrEnum):
    RASCUNHO = "rascunho"
    EM_REVISAO = "em_revisao"
    PUBLICADO = "publicado"
    ARQUIVADO = "arquivado"


NOME_DO_ESTADO = {
    EstadoPacote.RASCUNHO: "em rascunho",
    EstadoPacote.EM_REVISAO: "em revisão",
    EstadoPacote.PUBLICADO: "publicado",
    EstadoPacote.ARQUIVADO: "arquivado",
}


class PacoteNaoEncontrado(Recusa):
    mensagem = "Pacote não encontrado."


class TituloVazio(Recusa):
    """A mensagem diz se falta o título do pacote ou o da aula."""


class NivelForaDaMateria(Recusa):
    """R56: a mensagem diz quais níveis a matéria tem."""


class EstadoErrado(Recusa):
    """R15 e R38: a mensagem diz de que estado sai o passo e em que estado o pacote está."""


class PacoteSemAulas(Recusa):
    mensagem = "Adicione pelo menos 1 aula antes de enviar o pacote para revisão."


class PacoteNaoEditavel(Recusa):
    """R57: a mensagem diz por que o pacote não pode ser editado."""


class LinkInvalido(Recusa):
    mensagem = (
        "O link precisa ser de um vídeo do YouTube, como https://www.youtube.com/watch?v=… ou "
        "https://youtu.be/…."
    )


class AulaFixa(Recusa):
    mensagem = (
        "O pacote já foi publicado: as aulas não podem ser removidas, porque quem comprou "
        "perderia a aula."
    )


class AulaNaoEncontrada(Recusa):
    """A mensagem diz o número da aula que o pacote não tem."""


class PrecoInvalido(Recusa):
    mensagem = "O preço precisa ser maior que zero."


class PrecoAntesDePublicar(Recusa):
    """R59: a mensagem diz em que estado o pacote está."""


@dataclass(frozen=True)
class AulaNova:
    """Aula conferida (R58): o título e o link do vídeo, sempre no formato youtube.com/watch."""

    titulo: str
    link: str


@dataclass(frozen=True)
class AulaGravada:
    """Aula do pacote, numerada de 1 em diante. No publicado, o número não muda mais (R58)."""

    numero: int
    titulo: str
    link: str


@dataclass(frozen=True)
class PacoteNovo:
    """Pacote conferido e pronto para gravar: em rascunho, sem aulas e sem preço (R15)."""

    titulo: str
    materia_id: int
    nivel: int
    professor_id: int

    @property
    def estado(self) -> EstadoPacote:
        return EstadoPacote.RASCUNHO


@dataclass(frozen=True)
class Pacote:
    """preco_em_centavos fica vazio até o ADM publicar o pacote (R59). professor_id é quem o
    criou e o único que o edita (R56)."""

    id: int
    titulo: str
    materia_id: int
    nivel: int
    professor_id: int
    estado: EstadoPacote
    aulas: tuple[AulaGravada, ...] = ()
    preco_em_centavos: int | None = None


def novo_pacote(
    titulo: str,
    materia_id: int,
    nivel: int,
    nivel_maximo: int,
    nome_da_materia: str,
    professor_id: int,
) -> PacoteNovo:
    """R15 e R56: o pacote novo começa em rascunho, num dos níveis da matéria.

    A habilitação do professor na matéria (R11) é conferida pelo caso de uso.
    """
    if not 1 <= nivel <= nivel_maximo:
        if nivel_maximo == 1:
            raise NivelForaDaMateria(f"{nome_da_materia} só tem o nível {nome_do_nivel(1)}.")
        raise NivelForaDaMateria(
            f"{nome_da_materia} tem os níveis {nome_do_nivel(1)} a {nome_do_nivel(nivel_maximo)}."
        )
    return PacoteNovo(_titulo_do_pacote(titulo), materia_id, nivel, professor_id)


def nova_aula(titulo: str, link: str) -> AulaNova:
    """R58: a aula tem título e o link de um vídeo do YouTube, em qualquer dos jeitos de copiá-lo:
    youtube.com/watch?v=…, youtu.be/…, com ou sem www e com outros parâmetros."""
    titulo = titulo.strip()
    if not titulo:
        raise TituloVazio("Informe o título da aula.")
    return AulaNova(titulo, f"https://www.youtube.com/watch?v={_id_do_video(link)}")


def mudar_titulo(pacote: Pacote, titulo: str) -> Pacote:
    """R58: o professor muda o título no rascunho e no publicado."""
    _exigir_editavel(pacote)
    return replace(pacote, titulo=_titulo_do_pacote(titulo))


def adicionar_aula(pacote: Pacote, aula: AulaNova) -> Pacote:
    """R15 e R58: a aula entra no fim, no rascunho e no publicado, sem nova revisão."""
    _exigir_editavel(pacote)
    gravada = AulaGravada(len(pacote.aulas) + 1, aula.titulo, aula.link)
    return replace(pacote, aulas=(*pacote.aulas, gravada))


def corrigir_aula(pacote: Pacote, numero: int, aula: AulaNova) -> Pacote:
    """R58: o professor corrige o título e o link de uma aula, no rascunho e no publicado."""
    _exigir_editavel(pacote)
    _exigir_aula(pacote, numero)
    aulas = tuple(
        AulaGravada(numero, aula.titulo, aula.link) if gravada.numero == numero else gravada
        for gravada in pacote.aulas
    )
    return replace(pacote, aulas=aulas)


def remover_aula(pacote: Pacote, numero: int) -> Pacote:
    """R58: só o rascunho perde aulas, e as seguintes sobem um número."""
    _exigir_editavel(pacote)
    if pacote.estado != EstadoPacote.RASCUNHO:
        raise AulaFixa()
    _exigir_aula(pacote, numero)
    restantes = [aula for aula in pacote.aulas if aula.numero != numero]
    aulas = tuple(replace(aula, numero=n) for n, aula in enumerate(restantes, start=1))
    return replace(pacote, aulas=aulas)


def enviar_para_revisao(pacote: Pacote) -> Pacote:
    """R15 e R57: o professor envia o rascunho, com pelo menos 1 aula, para revisão."""
    _exigir_estado(pacote, EstadoPacote.RASCUNHO, "Só o pacote em rascunho é enviado para revisão.")
    if not pacote.aulas:
        raise PacoteSemAulas()
    return replace(pacote, estado=EstadoPacote.EM_REVISAO)


def publicar(pacote: Pacote, preco_em_centavos: int) -> Pacote:
    """R15 e R59: o ADM publica o pacote em revisão com um preço maior que zero."""
    _exigir_estado(pacote, EstadoPacote.EM_REVISAO, "Só o pacote em revisão é publicado.")
    _exigir_preco(preco_em_centavos)
    return replace(pacote, estado=EstadoPacote.PUBLICADO, preco_em_centavos=preco_em_centavos)


def devolver(pacote: Pacote) -> Pacote:
    """R38: o pacote em revisão volta para rascunho, e o professor pode editá-lo de novo."""
    _exigir_estado(pacote, EstadoPacote.EM_REVISAO, "Só o pacote em revisão é devolvido.")
    return replace(pacote, estado=EstadoPacote.RASCUNHO)


def arquivar(pacote: Pacote) -> Pacote:
    """R15: o pacote publicado sai da vitrine. Quem comprou mantém o acesso (R12)."""
    _exigir_estado(pacote, EstadoPacote.PUBLICADO, "Só o pacote publicado é arquivado.")
    return replace(pacote, estado=EstadoPacote.ARQUIVADO)


def publicar_de_novo(pacote: Pacote) -> Pacote:
    """R15 e R59: o arquivado volta para a vitrine, com o preço que tinha."""
    _exigir_estado(pacote, EstadoPacote.ARQUIVADO, "Só o pacote arquivado é publicado de novo.")
    return replace(pacote, estado=EstadoPacote.PUBLICADO)


def mudar_preco(pacote: Pacote, preco_em_centavos: int) -> Pacote:
    """R59: depois de publicar, o ADM muda o preço no publicado e no arquivado."""
    if pacote.estado not in (EstadoPacote.PUBLICADO, EstadoPacote.ARQUIVADO):
        raise PrecoAntesDePublicar(
            f"O preço é definido ao publicar o pacote. Este está {NOME_DO_ESTADO[pacote.estado]}."
        )
    _exigir_preco(preco_em_centavos)
    return replace(pacote, preco_em_centavos=preco_em_centavos)


def _titulo_do_pacote(titulo: str) -> str:
    titulo = titulo.strip()
    if not titulo:
        raise TituloVazio("Informe o título do pacote.")
    return titulo


def _id_do_video(link: str) -> str:
    link = link.strip()
    if "://" not in link:
        link = f"https://{link}"
    partes = urlsplit(link)
    site = (partes.hostname or "").lower()
    if site == "youtu.be":
        candidato = partes.path.removeprefix("/")
    elif site in _SITES_DO_YOUTUBE and partes.path == "/watch":
        candidato = next(iter(parse_qs(partes.query).get("v", [])), "")
    else:
        raise LinkInvalido()
    if not _ID_DO_VIDEO.fullmatch(candidato):
        raise LinkInvalido()
    return candidato


def _exigir_editavel(pacote: Pacote) -> None:
    """R57: o professor edita o rascunho e o publicado, nunca o em revisão nem o arquivado."""
    if pacote.estado == EstadoPacote.EM_REVISAO:
        raise PacoteNaoEditavel(
            "O pacote em revisão não pode ser editado: espere o ADM publicar ou devolver."
        )
    if pacote.estado == EstadoPacote.ARQUIVADO:
        raise PacoteNaoEditavel("O pacote arquivado não pode ser editado.")


def _exigir_aula(pacote: Pacote, numero: int) -> None:
    if not 1 <= numero <= len(pacote.aulas):
        raise AulaNaoEncontrada(f"O pacote não tem a {numero}ª aula.")


def _exigir_estado(pacote: Pacote, estado: EstadoPacote, so_de: str) -> None:
    if pacote.estado != estado:
        raise EstadoErrado(f"{so_de} Este está {NOME_DO_ESTADO[pacote.estado]}.")


def _exigir_preco(preco_em_centavos: int) -> None:
    if preco_em_centavos <= 0:
        raise PrecoInvalido()
