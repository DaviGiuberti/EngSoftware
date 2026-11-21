"""RNF07: todo caso de uso confere o perfil de quem chama."""

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario

_QUEM_PODE = {Perfil.ALUNO: "o aluno", Perfil.PROFESSOR: "o professor", Perfil.ADM: "o ADM"}


class AcessoNegado(Recusa):
    """O usuário não tem o perfil que a ação pede."""


def exigir_perfil(usuario: Usuario, perfil: Perfil, acao: str) -> None:
    """Recusa se o usuário não tem o perfil da ação, dizendo quem pode fazê-la."""
    if usuario.perfil != perfil:
        raise AcessoNegado(f"Só {_QUEM_PODE[perfil]} pode {acao}.")
