"""Casos de uso da identidade (H38): cadastrar aluno, criar o primeiro ADM e entrar."""

import secrets

from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.application.portas import RepositorioDeUsuarios
from plataforma.modules.identidade.domain.cadastro import (
    exigir_email_livre,
    exigir_que_nao_haja_adm,
    normalizar_email,
    validar_email,
)
from plataforma.modules.identidade.domain.login import autenticar
from plataforma.modules.identidade.domain.senha import gerar_hash, validar_senha
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario

TAMANHO_DO_SAL_EM_BYTES = 16


class CadastrarAluno:
    """O aluno se cadastra sozinho, com e-mail e senha."""

    def __init__(self, usuarios: RepositorioDeUsuarios, transacao: Transacao) -> None:
        self._usuarios = usuarios
        self._transacao = transacao

    def executar(self, email: str, senha: str) -> Usuario:
        with self._transacao():
            return _adicionar_usuario(self._usuarios, email, senha, Perfil.ALUNO)


class CriarPrimeiroAdm:
    """Na primeira abertura do app, sem nenhum ADM, a pessoa define o e-mail e a senha do ADM."""

    def __init__(self, usuarios: RepositorioDeUsuarios, transacao: Transacao) -> None:
        self._usuarios = usuarios
        self._transacao = transacao

    def pendente(self) -> bool:
        """Diz se o app ainda não tem ADM e por isso deve abrir na tela do primeiro ADM."""
        return not self._usuarios.existe_adm()

    def executar(self, email: str, senha: str) -> Usuario:
        with self._transacao():
            exigir_que_nao_haja_adm(self._usuarios.existe_adm())
            return _adicionar_usuario(self._usuarios, email, senha, Perfil.ADM)


class Entrar:
    """Qualquer perfil entra com e-mail e senha."""

    def __init__(self, usuarios: RepositorioDeUsuarios) -> None:
        self._usuarios = usuarios

    def executar(self, email: str, senha: str) -> Usuario:
        return autenticar(self._usuarios.buscar_credencial(normalizar_email(email)), senha)


def _adicionar_usuario(
    usuarios: RepositorioDeUsuarios, email: str, senha: str, perfil: Perfil
) -> Usuario:
    """Confere o e-mail (R39) e a senha (RNF06) e grava o usuário com um sal novo.

    Roda dentro da transação de quem chama.
    """
    email = normalizar_email(email)
    validar_email(email)
    validar_senha(senha)
    exigir_email_livre(usuarios.buscar_credencial(email) is not None)
    sal = secrets.token_bytes(TAMANHO_DO_SAL_EM_BYTES)
    return usuarios.adicionar(email, gerar_hash(senha, sal), perfil)
