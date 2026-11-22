"""Consulta pública do nível do aluno em cada matéria, para os outros módulos (ADR 0002)."""

from plataforma.modules.nivelamento.application.portas import RepositorioDeNivelamentos


class ConsultaDeNiveis:
    """As turmas leem o nível do aluno para conferir a R06 sem ler as tabelas do nivelamento."""

    def __init__(self, nivelamentos: RepositorioDeNivelamentos) -> None:
        self._nivelamentos = nivelamentos

    def nivel_do_aluno(self, aluno_id: int, materia_id: int) -> int | None:
        """O nível do aluno na matéria, ou None se ele ainda não fez o nivelamento dela."""
        nivel = self._nivelamentos.nivel_do_aluno(aluno_id, materia_id)
        return None if nivel is None else nivel.nivel

    def niveis_do_aluno(self, aluno_id: int) -> dict[int, int]:
        """O nível do aluno em cada matéria em que ele tem nível, pelo id da matéria."""
        niveis = self._nivelamentos.niveis_do_aluno(aluno_id)
        return {nivel.materia_id: nivel.nivel for nivel in niveis}
