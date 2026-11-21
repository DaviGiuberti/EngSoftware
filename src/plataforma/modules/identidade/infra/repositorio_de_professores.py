"""Professores no SQLite: a tabela usuario da migração 0002 e a habilitacao da 0006.

Todo SQL usa parâmetros (RNF08).
"""

import sqlite3
from collections import defaultdict

from plataforma.modules.identidade.domain.professor import Professor
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario

# Com professor_id NULL, a consulta traz todos os professores; com um id, só aquele.
_PROFESSORES = (
    "SELECT u.id, u.email, h.materia_id FROM usuario u "
    "LEFT JOIN habilitacao h ON h.professor_id = u.id "
    "WHERE u.perfil = :perfil AND (:professor_id IS NULL OR u.id = :professor_id) "
    "ORDER BY u.email, h.materia_id"
)


class RepositorioDeProfessoresSqlite:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self._conexao = conexao

    def listar(self) -> list[Professor]:
        return self._ler(None)

    def buscar(self, professor_id: int) -> Professor | None:
        return next(iter(self._ler(professor_id)), None)

    def adicionar_habilitacao(self, professor_id: int, materia_id: int) -> None:
        self._conexao.execute(
            "INSERT INTO habilitacao (professor_id, materia_id) VALUES (?, ?)",
            (professor_id, materia_id),
        )

    def _ler(self, professor_id: int | None) -> list[Professor]:
        linhas = self._conexao.execute(
            _PROFESSORES, {"perfil": Perfil.PROFESSOR.value, "professor_id": professor_id}
        ).fetchall()
        emails: dict[int, str] = {}
        materias: defaultdict[int, set[int]] = defaultdict(set)
        for id_professor, email, materia_id in linhas:
            emails[id_professor] = email
            # O LEFT JOIN traz materia_id NULL para o professor sem habilitação.
            if materia_id is not None:
                materias[id_professor].add(materia_id)
        return [
            Professor(
                Usuario(id_professor, email, Perfil.PROFESSOR), frozenset(materias[id_professor])
            )
            for id_professor, email in emails.items()
        ]
