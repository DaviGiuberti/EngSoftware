"""Portas da identidade: o que os casos de uso pedem à infraestrutura."""

from typing import Protocol

from plataforma.modules.identidade.domain.login import Credencial
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario


class RepositorioDeUsuarios(Protocol):
    def buscar_credencial(self, email: str) -> Credencial | None:
        """O usuário com o hash da senha, ou None se o e-mail não tem conta."""
        ...

    def existe_adm(self) -> bool: ...

    def adicionar(self, email: str, hash_da_senha: str, perfil: Perfil) -> Usuario: ...
