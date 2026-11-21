"""Entrar com e-mail e senha (H38)."""

from dataclasses import dataclass, field

from plataforma.compartilhado.recusa import Recusa
from plataforma.modules.identidade.domain.senha import senha_confere
from plataforma.modules.identidade.domain.usuario import Usuario


class LoginInvalido(Recusa):
    def __init__(self) -> None:
        # A mesma mensagem para e-mail sem cadastro e para senha errada: assim a tela não
        # revela quais e-mails têm conta.
        super().__init__("E-mail ou senha incorretos.")


@dataclass(frozen=True)
class Credencial:
    """O usuário com o hash da senha guardado no banco. Só é usada para entrar."""

    usuario: Usuario
    hash_da_senha: str = field(repr=False)


def autenticar(credencial: Credencial | None, senha: str) -> Usuario:
    """Devolve o usuário se o e-mail tem cadastro e a senha confere. Senão, recusa."""
    if credencial is None or not senha_confere(senha, credencial.hash_da_senha):
        raise LoginInvalido()
    return credencial.usuario
