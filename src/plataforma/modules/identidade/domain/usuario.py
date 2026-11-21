"""Usuário e perfil: quem entra na plataforma e o que pode fazer."""

from dataclasses import dataclass
from enum import StrEnum


class Perfil(StrEnum):
    """Papel do usuário. Cada usuário tem um só (R39)."""

    ALUNO = "aluno"
    PROFESSOR = "professor"
    ADM = "adm"


@dataclass(frozen=True)
class Usuario:
    """Pessoa com login na plataforma. Não leva a senha: o hash só aparece na Credencial."""

    id: int
    email: str
    perfil: Perfil
