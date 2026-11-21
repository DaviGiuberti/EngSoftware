"""Professor e habilitação por matéria (H29): habilitado numa matéria, o professor dá aula em
todos os níveis dela (R11)."""

from dataclasses import dataclass, replace

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario


class ProfessorNaoEncontrado(Recusa):
    mensagem = "Professor não encontrado."


class SemHabilitacao(Recusa):
    """R11: a mensagem diz quem é o professor e qual é a matéria."""


class HabilitacaoRepetida(Recusa):
    """A mensagem diz quem é o professor e qual é a matéria."""


@dataclass(frozen=True)
class Professor:
    """Usuário com o perfil de professor e as matérias em que o ADM o habilitou.

    materias_habilitadas guarda o id de cada matéria. A habilitação não tem nível: vale para
    todos os níveis da matéria (R11).
    """

    usuario: Usuario
    materias_habilitadas: frozenset[int] = frozenset()

    def __post_init__(self) -> None:
        if self.usuario.perfil != Perfil.PROFESSOR:
            raise ValueError(f"Usuário sem o perfil de professor: {self.usuario.email}")

    @property
    def id(self) -> int:
        return self.usuario.id

    @property
    def email(self) -> str:
        return self.usuario.email


def habilitar(professor: Professor, materia_id: int, nome_da_materia: str) -> Professor:
    """O ADM habilita o professor numa matéria. Habilitar de novo na mesma é recusado."""
    if materia_id in professor.materias_habilitadas:
        raise HabilitacaoRepetida(f"{professor.email} já tem habilitação em {nome_da_materia}.")
    return replace(professor, materias_habilitadas=professor.materias_habilitadas | {materia_id})


def exigir_habilitacao(professor: Professor, materia_id: int, nome_da_materia: str) -> None:
    """R11: só dá aula numa turma o professor habilitado na matéria dela, em qualquer nível."""
    if materia_id not in professor.materias_habilitadas:
        raise SemHabilitacao(f"{professor.email} não tem habilitação em {nome_da_materia}.")
