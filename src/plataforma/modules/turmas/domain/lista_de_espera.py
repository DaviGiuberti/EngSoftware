"""Lista de espera (H05, H06, H13), em ordem de entrada e só para turma cheia (R05).

Quando abre uma vaga, o 1º da lista ainda sem oferta tem 72 horas para confirmá-la, e a vaga
fica reservada (R05). Quem não confirma sai da lista, e a vaga passa para o próximo (R35). A
partir da 13ª aula da etapa, a lista não recebe ninguém e a vaga não é oferecida (R45).
"""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.turmas.domain.horario import formatar_data_e_hora
from plataforma.modules.turmas.domain.matricula import matricula_aberta
from plataforma.modules.turmas.domain.turma import Turma

PRAZO_PARA_CONFIRMAR = timedelta(hours=72)


class JaEstaNaLista(Recusa):
    mensagem = "Você já está na lista de espera desta turma."


class TurmaComVaga(Recusa):
    mensagem = "A turma tem vaga: você pode se matricular sem lista de espera."


class ListaFechada(Recusa):
    mensagem = "A lista de espera desta turma fechou: a etapa já chegou à 13ª aula."


class SemOferta(Recusa):
    mensagem = "Você não tem vaga oferecida nesta turma."


class PrazoVencido(Recusa):
    """R05: a mensagem diz quando o prazo terminou."""


@dataclass(frozen=True)
class NaLista:
    """Um aluno na lista de espera. Com uma oferta de vaga, prazo diz até quando ele confirma."""

    aluno_id: int
    entrou_em: datetime
    prazo: datetime | None = None


# Os alunos na ordem em que entraram na lista.
type ListaDeEspera = tuple[NaLista, ...]


def entrar(lista: ListaDeEspera, aluno_id: int, agora: datetime) -> ListaDeEspera:
    """R05: quem entra fica no fim da lista."""
    if any(na_lista.aluno_id == aluno_id for na_lista in lista):
        raise JaEstaNaLista()
    return (*lista, NaLista(aluno_id, agora))


def posicao(lista: ListaDeEspera, aluno_id: int) -> int:
    """O lugar do aluno na lista, a partir de 1."""
    return next(i for i, na_lista in enumerate(lista, start=1) if na_lista.aluno_id == aluno_id)


def exigir_turma_cheia(vagas_livres: int) -> None:
    """R05: só a turma cheia tem lista de espera. Com vaga, o aluno se matricula."""
    if vagas_livres > 0:
        raise TurmaComVaga()


def exigir_lista_aberta(aulas_dadas: int) -> None:
    """R45: a partir da 13ª aula da etapa, a lista de espera não recebe ninguém."""
    if not matricula_aberta(aulas_dadas):
        raise ListaFechada()


def reservadas(lista: ListaDeEspera) -> int:
    """R05: cada oferta de vaga reserva uma vaga da turma até o prazo."""
    return sum(1 for na_lista in lista if na_lista.prazo is not None)


def pode_oferecer_em(turma: Turma) -> Callable[[datetime], bool]:
    """R45: a vaga que abre só é oferecida à lista de espera antes da 13ª aula da etapa."""

    def pode_oferecer(momento: datetime) -> bool:
        return matricula_aberta(turma.aulas_dadas(momento))

    return pode_oferecer


def oferecer_vaga(lista: ListaDeEspera, momento: datetime, pode_oferecer: bool) -> ListaDeEspera:
    """R05: a vaga que abre vai para o 1º da lista ainda sem oferta, com 72 horas para confirmar.

    Sem ninguém para receber a oferta, ou com pode_oferecer falso (R45), a vaga fica livre.
    """
    if not pode_oferecer:
        return lista
    for indice, na_lista in enumerate(lista):
        if na_lista.prazo is None:
            com_oferta = replace(na_lista, prazo=momento + PRAZO_PARA_CONFIRMAR)
            return (*lista[:indice], com_oferta, *lista[indice + 1 :])
    return lista


def vencer_prazos(
    lista: ListaDeEspera, agora: datetime, pode_oferecer: Callable[[datetime], bool]
) -> ListaDeEspera:
    """R35: quem não confirmou até o prazo sai da lista, e a vaga passa para o próximo (R05).

    O novo prazo conta do fim do anterior, e não de agora: o resultado é o mesmo, seja qual for
    o momento em que o sistema olha a lista. pode_oferecer diz se, num momento, a vaga ainda
    pode ser oferecida (R45).
    """
    while True:
        vencidos = [
            (na_lista.prazo, na_lista.aluno_id)
            for na_lista in lista
            if na_lista.prazo is not None and na_lista.prazo <= agora
        ]
        if not vencidos:
            return lista
        fim_do_prazo, aluno_id = min(vencidos)
        sem_ele = tuple(na_lista for na_lista in lista if na_lista.aluno_id != aluno_id)
        lista = oferecer_vaga(sem_ele, fim_do_prazo, pode_oferecer(fim_do_prazo))


def confirmar(
    lista: ListaDeEspera,
    aluno_id: int,
    agora: datetime,
    pode_oferecer: Callable[[datetime], bool],
) -> ListaDeEspera:
    """R05: dentro do prazo, o aluno confirma a vaga e sai da lista.

    Os prazos que venceram antes de agora valem primeiro (R35): a vaga pode ter chegado ao
    aluno porque o prazo de quem estava na frente venceu. Quem chama faz a matrícula, que é o
    que confirmar a vaga significa (R47).
    """
    efetiva = vencer_prazos(lista, agora, pode_oferecer)
    if any(n.aluno_id == aluno_id and n.prazo is not None for n in efetiva):
        return tuple(na_lista for na_lista in efetiva if na_lista.aluno_id != aluno_id)
    oferta_vencida = next(
        (n.prazo for n in lista if n.aluno_id == aluno_id and n.prazo is not None), None
    )
    if oferta_vencida is not None:
        raise PrazoVencido(
            f"O prazo para confirmar a vaga terminou em {formatar_data_e_hora(oferta_vencida)}."
        )
    raise SemOferta()


def sair(
    lista: ListaDeEspera, aluno_id: int, momento: datetime, pode_oferecer: bool
) -> ListaDeEspera:
    """R44: o aluno que se matriculou noutra turma da matéria sai da lista.

    Se ele tinha uma oferta de vaga, a vaga passa para o próximo a partir de agora (R05).
    """
    saindo = next((na_lista for na_lista in lista if na_lista.aluno_id == aluno_id), None)
    if saindo is None:
        return lista
    sem_ele = tuple(na_lista for na_lista in lista if na_lista.aluno_id != aluno_id)
    if saindo.prazo is None:
        return sem_ele
    return oferecer_vaga(sem_ele, momento, pode_oferecer)
