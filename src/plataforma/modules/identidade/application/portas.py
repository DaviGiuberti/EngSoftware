"""Portas da identidade: o que os casos de uso pedem à infraestrutura."""

from typing import Protocol

from plataforma.modules.identidade.domain.login import Credencial
from plataforma.modules.identidade.domain.professor import Professor
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario


class RepositorioDeUsuarios(Protocol):
    def buscar_credencial(self, email: str) -> Credencial | None:
        """O usuário com o hash da senha, ou None se o e-mail não tem conta."""
        ...

    def existe_adm(self) -> bool: ...

    def adicionar(self, email: str, hash_da_senha: str, perfil: Perfil) -> Usuario: ...

    def buscar(self, usuario_id: int) -> Usuario | None: ...


class RepositorioDeProfessores(Protocol):
    def listar(self) -> list[Professor]:
        """Os professores em ordem de e-mail, com as matérias em que estão habilitados."""
        ...

    def buscar(self, professor_id: int) -> Professor | None:
        """O professor, ou None se o id não é de um usuário com o perfil de professor."""
        ...

    def adicionar_habilitacao(self, professor_id: int, materia_id: int) -> None: ...
