"""Usuários no SQLite, na tabela usuario da migração 0002. Todo SQL usa parâmetros (RNF08)."""

import sqlite3

from plataforma.modules.identidade.domain.login import Credencial
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario


class RepositorioDeUsuariosSqlite:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self._conexao = conexao

    def buscar_credencial(self, email: str) -> Credencial | None:
        linha = self._conexao.execute(
            "SELECT id, email, perfil, hash_da_senha FROM usuario WHERE email = ?", (email,)
        ).fetchone()
        if linha is None:
            return None
        id_usuario, email_guardado, perfil, hash_da_senha = linha
        return Credencial(Usuario(id_usuario, email_guardado, Perfil(perfil)), hash_da_senha)

    def existe_adm(self) -> bool:
        linha = self._conexao.execute(
            "SELECT 1 FROM usuario WHERE perfil = ? LIMIT 1", (Perfil.ADM.value,)
        ).fetchone()
        return linha is not None

    def adicionar(self, email: str, hash_da_senha: str, perfil: Perfil) -> Usuario:
        (id_usuario,) = self._conexao.execute(
            "INSERT INTO usuario (email, hash_da_senha, perfil) VALUES (?, ?, ?) RETURNING id",
            (email, hash_da_senha, perfil.value),
        ).fetchone()
        return Usuario(id_usuario, email, perfil)

    def buscar(self, usuario_id: int) -> Usuario | None:
        linha = self._conexao.execute(
            "SELECT id, email, perfil FROM usuario WHERE id = ?", (usuario_id,)
        ).fetchone()
        if linha is None:
            return None
        id_usuario, email, perfil = linha
        return Usuario(id_usuario, email, Perfil(perfil))
