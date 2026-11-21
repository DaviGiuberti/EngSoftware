"""Casos de uso do módulo materias (H27)."""

from collections.abc import Sequence

from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.domain.autorizacao import exigir_perfil
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.materias.application.portas import RepositorioDeMaterias
from plataforma.modules.materias.domain.materia import (
    Materia,
    MateriaNaoEncontrada,
    exigir_nome_livre,
    nova_materia,
)


class CadastrarMateria:
    """O ADM cadastra a matéria com os níveis, as faixas do nivelamento e a mensalidade."""

    def __init__(self, materias: RepositorioDeMaterias, transacao: Transacao) -> None:
        self._materias = materias
        self._transacao = transacao

    def executar(
        self,
        usuario: Usuario,
        nome: str,
        nivel_maximo: int,
        notas_minimas: Sequence[int],
        mensalidade_em_centavos: int,
    ) -> Materia:
        exigir_perfil(usuario, Perfil.ADM, "cadastrar matéria")
        materia = nova_materia(nome, nivel_maximo, notas_minimas, mensalidade_em_centavos)
        with self._transacao():
            exigir_nome_livre(materia.nome, (outra.nome for outra in self._materias.listar()))
            return self._materias.adicionar(materia)


class ConsultaDeMaterias:
    """Leitura das matérias, para as telas e para os outros módulos (ADR 0002).

    Qualquer perfil pode ver as matérias, então a consulta não confere o perfil.
    """

    def __init__(self, materias: RepositorioDeMaterias) -> None:
        self._materias = materias

    def listar(self) -> list[Materia]:
        return self._materias.listar()

    def obter(self, materia_id: int) -> Materia:
        materia = self._materias.buscar(materia_id)
        if materia is None:
            raise MateriaNaoEncontrada()
        return materia
