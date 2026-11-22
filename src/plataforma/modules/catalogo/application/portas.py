"""Portas do catálogo: o que os casos de uso pedem à infraestrutura."""

from typing import Protocol

from plataforma.modules.catalogo.domain.pacote import Pacote, PacoteNovo


class RepositorioDePacotes(Protocol):
    """O pacote com as aulas gravadas dele, em ordem de número."""

    def adicionar(self, pacote: PacoteNovo) -> Pacote:
        """Grava o pacote em rascunho, sem aulas e sem preço (R15)."""
        ...

    def buscar(self, pacote_id: int) -> Pacote | None: ...

    def listar(self) -> list[Pacote]:
        """Todos os pacotes, na ordem em que foram criados."""
        ...

    def do_professor(self, professor_id: int) -> list[Pacote]:
        """Os pacotes que o professor criou, na ordem em que foram criados."""
        ...

    def publicados(self) -> list[Pacote]:
        """Os pacotes publicados, na ordem em que foram criados (R15)."""
        ...

    def salvar(self, pacote: Pacote) -> None:
        """Grava o que pode mudar: o título, o estado, o preço e as aulas. A matéria e o nível
        não mudam (R56)."""
        ...
