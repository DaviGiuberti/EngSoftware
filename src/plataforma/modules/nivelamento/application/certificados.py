"""Caso de uso dos certificados de nível e de trilha (H12): o aluno vê os próprios certificados,
que saem das promoções e das trilhas concluídas que o nivelamento guarda (R33, R36)."""

from dataclasses import dataclass
from datetime import datetime

from plataforma.modules.identidade.domain.autorizacao import exigir_perfil
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.nivelamento.application.portas import RepositorioDeNivelamentos
from plataforma.modules.nivelamento.domain.certificado import TipoDeCertificado, certificados


@dataclass(frozen=True)
class CertificadoDoAluno:
    """Um certificado como o aluno o vê, com o nome da matéria."""

    tipo: TipoDeCertificado
    materia_id: int
    nome_da_materia: str
    nivel: int
    emitido_em: datetime


class VerMeusCertificados:
    """H12: o aluno vê os próprios certificados, na ordem em que foram emitidos (RNF07)."""

    def __init__(
        self, nivelamentos: RepositorioDeNivelamentos, materias: ConsultaDeMaterias
    ) -> None:
        self._nivelamentos = nivelamentos
        self._materias = materias

    def executar(self, usuario: Usuario) -> list[CertificadoDoAluno]:
        exigir_perfil(usuario, Perfil.ALUNO, "ver os próprios certificados")
        materias = {materia.id: materia for materia in self._materias.listar()}
        emitidos = certificados(
            self._nivelamentos.promocoes(usuario.id),
            self._nivelamentos.trilhas_concluidas(usuario.id),
            {materia.id: materia.nivel_maximo for materia in materias.values()},
        )
        return [
            CertificadoDoAluno(
                c.tipo, c.materia_id, materias[c.materia_id].nome, c.nivel, c.emitido_em
            )
            for c in emitidos
        ]
