"""Pacotes no SQLite, nas tabelas pacote e aula_gravada da migração 0013 (RNF08: só SQL com "?")."""

import sqlite3
from collections import defaultdict

from plataforma.modules.catalogo.domain.pacote import (
    AulaGravada,
    EstadoPacote,
    Pacote,
    PacoteNovo,
)

# Cada filtro NULL deixa passar todos os pacotes.
_PACOTES = (
    "SELECT id, titulo, materia_id, nivel, professor_id, estado, preco_em_centavos FROM pacote "
    "WHERE (:pacote_id IS NULL OR id = :pacote_id) "
    "AND (:professor_id IS NULL OR professor_id = :professor_id) "
    "AND (:estado IS NULL OR estado = :estado) "
    "ORDER BY id"
)

# As aulas dos mesmos pacotes, com os mesmos filtros.
_AULAS = (
    "SELECT aula.pacote_id, aula.numero, aula.titulo, aula.link FROM aula_gravada AS aula "
    "JOIN pacote ON pacote.id = aula.pacote_id "
    "WHERE (:pacote_id IS NULL OR pacote.id = :pacote_id) "
    "AND (:professor_id IS NULL OR pacote.professor_id = :professor_id) "
    "AND (:estado IS NULL OR pacote.estado = :estado) "
    "ORDER BY aula.pacote_id, aula.numero"
)


class RepositorioDePacotesSqlite:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self._conexao = conexao

    def adicionar(self, pacote: PacoteNovo) -> Pacote:
        (pacote_id,) = self._conexao.execute(
            "INSERT INTO pacote (titulo, materia_id, nivel, professor_id, estado) "
            "VALUES (?, ?, ?, ?, ?) RETURNING id",
            (
                pacote.titulo,
                pacote.materia_id,
                pacote.nivel,
                pacote.professor_id,
                str(pacote.estado),
            ),
        ).fetchone()
        return Pacote(
            pacote_id,
            pacote.titulo,
            pacote.materia_id,
            pacote.nivel,
            pacote.professor_id,
            pacote.estado,
        )

    def buscar(self, pacote_id: int) -> Pacote | None:
        return next(iter(self._ler(pacote_id=pacote_id)), None)

    def listar(self) -> list[Pacote]:
        return self._ler()

    def do_professor(self, professor_id: int) -> list[Pacote]:
        return self._ler(professor_id=professor_id)

    def publicados(self) -> list[Pacote]:
        return self._ler(estado=EstadoPacote.PUBLICADO)

    def salvar(self, pacote: Pacote) -> None:
        self._conexao.execute(
            "UPDATE pacote SET titulo = ?, estado = ?, preco_em_centavos = ? WHERE id = ?",
            (pacote.titulo, str(pacote.estado), pacote.preco_em_centavos, pacote.id),
        )
        # As aulas são gravadas pelo número, sem apagar as que continuam: depois de publicado,
        # o pacote e o número dizem qual é a aula (R58). Só o rascunho perde aulas do fim.
        self._conexao.executemany(
            "INSERT INTO aula_gravada (pacote_id, numero, titulo, link) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (pacote_id, numero) DO UPDATE SET titulo = excluded.titulo, "
            "link = excluded.link",
            [(pacote.id, aula.numero, aula.titulo, aula.link) for aula in pacote.aulas],
        )
        self._conexao.execute(
            "DELETE FROM aula_gravada WHERE pacote_id = ? AND numero > ?",
            (pacote.id, len(pacote.aulas)),
        )

    def _ler(
        self,
        pacote_id: int | None = None,
        professor_id: int | None = None,
        estado: EstadoPacote | None = None,
    ) -> list[Pacote]:
        filtros: dict[str, object] = {
            "pacote_id": pacote_id,
            "professor_id": professor_id,
            "estado": None if estado is None else str(estado),
        }
        linhas = self._conexao.execute(_PACOTES, filtros).fetchall()
        aulas = self._aulas(filtros)
        return [
            Pacote(
                id=id_do_pacote,
                titulo=titulo,
                materia_id=materia_id,
                nivel=nivel,
                professor_id=dono,
                estado=EstadoPacote(estado_gravado),
                aulas=tuple(aulas[id_do_pacote]),
                preco_em_centavos=preco,
            )
            for id_do_pacote, titulo, materia_id, nivel, dono, estado_gravado, preco in linhas
        ]

    def _aulas(self, filtros: dict[str, object]) -> defaultdict[int, list[AulaGravada]]:
        aulas: defaultdict[int, list[AulaGravada]] = defaultdict(list)
        for id_do_pacote, numero, titulo, link in self._conexao.execute(_AULAS, filtros):
            aulas[id_do_pacote].append(AulaGravada(numero, titulo, link))
        return aulas
