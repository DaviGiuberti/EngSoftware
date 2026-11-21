"""RNF07: todo caso de uso confere o perfil de quem chama e, quando houver, o dono do recurso."""

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario

_QUEM_PODE = {Perfil.ALUNO: "o aluno", Perfil.PROFESSOR: "o professor", Perfil.ADM: "o ADM"}


class AcessoNegado(Recusa):
    """O usuário não tem o perfil que a ação pede."""


def exigir_perfil(usuario: Usuario, perfil: Perfil, acao: str) -> None:
    """Recusa se o usuário não tem o perfil da ação, dizendo quem pode fazê-la."""
    if usuario.perfil != perfil:
        raise AcessoNegado(f"Só {_QUEM_PODE[perfil]} pode {acao}.")


def exigir_dono(usuario: Usuario, dono_id: int, mensagem: str) -> None:
    """Recusa quem não é o dono do recurso. A mensagem diz de quem é o recurso."""
    if usuario.id != dono_id:
        raise AcessoNegado(mensagem)
