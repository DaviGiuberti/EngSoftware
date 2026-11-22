"""Portas do catálogo: o que os casos de uso pedem à infraestrutura."""

from datetime import datetime
from typing import Protocol

from plataforma.modules.catalogo.domain.aulas_do_aluno import AcessoAoPacote, AulaConcluida
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


class RepositorioDeAulasConcluidas(Protocol):
    def do_aluno(self, aluno_id: int) -> list[AulaConcluida]:
        """As aulas que o aluno concluiu, de todos os pacotes, na ordem em que concluiu."""
        ...

    def adicionar(self, aluno_id: int, concluida: AulaConcluida) -> None: ...

    def apagar(self, aluno_id: int, pacote_id: int) -> None:
        """Apaga as aulas que o aluno concluiu no pacote, no reembolso (R63)."""
        ...


class Acessos(Protocol):
    """O acesso que a compra dá, que é do módulo vendas. O main.py liga esta porta à consulta de
    acessos do vendas, e o catalogo não importa o vendas (ADR 0002)."""

    def do_aluno(self, aluno_id: int, agora: datetime) -> dict[int, AcessoAoPacote]:
        """O acesso a cada pacote que o aluno comprou, pelo id do pacote, da compra mais recente."""
        ...
