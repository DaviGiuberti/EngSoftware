"""Casos de uso das turmas: criar a turma, trocar o professor e o pedido de mudar o horário, que
é recusado (H30, H31), e ver as turmas, o ADM todas e o professor as dele (H20).

Os casos de uso do aluno, como a matrícula, ficam em matricula.py e usam as funções públicas
daqui: obter_turma, ocupacao e pode_oferecer_em.
"""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, time

from plataforma.compartilhado.relogio import Relogio
from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.application.casos_de_uso import ConsultaDeProfessores
from plataforma.modules.identidade.domain.autorizacao import exigir_perfil
from plataforma.modules.identidade.domain.professor import exigir_habilitacao
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias
from plataforma.modules.turmas.application.portas import RepositorioDeTurmas
from plataforma.modules.turmas.domain.horario import DiaDaSemana, Horario, novo_horario
from plataforma.modules.turmas.domain.lista_de_espera import (
    ListaDeEspera,
    reservadas,
    vencer_prazos,
)
from plataforma.modules.turmas.domain.matricula import (
    Matricula,
    matricula_aberta,
    vagas_livres,
)
from plataforma.modules.turmas.domain.turma import (
    Turma,
    TurmaNaoEncontrada,
    exigir_nivel_da_materia,
    exigir_professor_livre,
    mudar_horario,
    nova_turma,
    trocar_professor,
)


@dataclass(frozen=True)
class ResumoDaTurma:
    """Uma turma como as telas mostram: com o nome da matéria, o e-mail do professor e as aulas
    dadas da etapa até agora (R43)."""

    id: int
    materia_id: int
    nome_da_materia: str
    nivel: int
    professor_id: int
    email_do_professor: str
    horario: Horario
    inicio_da_etapa: datetime
    aulas_dadas: int
    vagas_livres: int


@dataclass(frozen=True)
class Ocupacao:
    """Quem ocupa as vagas da turma agora: os matriculados e a lista de espera, já sem as
    ofertas de vaga com prazo vencido (R35)."""

    matriculas: list[Matricula]
    lista: ListaDeEspera

    @property
    def vagas_livres(self) -> int:
        return vagas_livres(len(self.matriculas), reservadas(self.lista))


def obter_turma(turmas: RepositorioDeTurmas, turma_id: int) -> Turma:
    turma = turmas.buscar(turma_id)
    if turma is None:
        raise TurmaNaoEncontrada()
    return turma


def pode_oferecer_em(turma: Turma) -> Callable[[datetime], bool]:
    """R45: a vaga que abre só é oferecida à lista de espera antes da 13ª aula da etapa."""

    def pode_oferecer(momento: datetime) -> bool:
        return matricula_aberta(turma.aulas_dadas(momento))

    return pode_oferecer


def ocupacao(turmas: RepositorioDeTurmas, turma: Turma, agora: datetime) -> Ocupacao:
    """As matrículas e a lista de espera da turma, com os prazos vencidos até agora aplicados.

    Ninguém precisa olhar a lista na hora em que um prazo vence: o resultado é o mesmo em
    qualquer momento depois dele (R05, R35).
    """
    lista = vencer_prazos(turmas.lista_de_espera(turma.id), agora, pode_oferecer_em(turma))
    return Ocupacao(turmas.matriculas_da_turma(turma.id), lista)


def resumir(
    turma: Turma, ocupada: Ocupacao, nome_da_materia: str, email_do_professor: str, agora: datetime
) -> ResumoDaTurma:
    return ResumoDaTurma(
        id=turma.id,
        materia_id=turma.materia_id,
        nome_da_materia=nome_da_materia,
        nivel=turma.nivel,
        professor_id=turma.professor_id,
        email_do_professor=email_do_professor,
        horario=turma.horario,
        inicio_da_etapa=turma.inicio_da_etapa,
        aulas_dadas=turma.aulas_dadas(agora),
        vagas_livres=ocupada.vagas_livres,
    )


class CriarTurma:
    """O ADM cria a turma com matéria, nível inicial, professor, dias e horário (R24)."""

    def __init__(
        self,
        turmas: RepositorioDeTurmas,
        materias: ConsultaDeMaterias,
        professores: ConsultaDeProfessores,
        relogio: Relogio,
        transacao: Transacao,
    ) -> None:
        self._turmas = turmas
        self._materias = materias
        self._professores = professores
        self._relogio = relogio
        self._transacao = transacao

    def executar(
        self,
        usuario: Usuario,
        materia_id: int,
        nivel: int,
        professor_id: int,
        dias: Iterable[DiaDaSemana],
        inicio: time,
        fim: time,
    ) -> Turma:
        exigir_perfil(usuario, Perfil.ADM, "criar turma")
        horario = novo_horario(dias, inicio, fim)
        materia = self._materias.obter(materia_id)
        exigir_nivel_da_materia(nivel, materia.nivel_maximo, materia.nome)
        professor = self._professores.obter(professor_id)
        exigir_habilitacao(professor, materia.id, materia.nome)
        agora = self._relogio.agora()
        with self._transacao():
            ocupados = [turma.horario for turma in self._turmas.do_professor(professor.id)]
            exigir_professor_livre(professor.email, horario, ocupados)
            turma = nova_turma(materia.id, nivel, professor.id, horario, agora)
            return self._turmas.adicionar(turma)


class TrocarProfessor:
    """O ADM troca o professor da turma quando quiser (R26). O novo precisa estar habilitado na
    matéria (R11) e livre no horário da turma (R07)."""

    def __init__(
        self,
        turmas: RepositorioDeTurmas,
        materias: ConsultaDeMaterias,
        professores: ConsultaDeProfessores,
        transacao: Transacao,
    ) -> None:
        self._turmas = turmas
        self._materias = materias
        self._professores = professores
        self._transacao = transacao

    def executar(self, usuario: Usuario, turma_id: int, professor_id: int) -> Turma:
        exigir_perfil(usuario, Perfil.ADM, "trocar o professor da turma")
        with self._transacao():
            turma = obter_turma(self._turmas, turma_id)
            professor = self._professores.obter(professor_id)
            trocada = trocar_professor(turma, professor.id, professor.email)
            materia = self._materias.obter(turma.materia_id)
            exigir_habilitacao(professor, materia.id, materia.nome)
            ocupados = [
                outra.horario
                for outra in self._turmas.do_professor(professor.id)
                if outra.id != turma.id
            ]
            exigir_professor_livre(professor.email, turma.horario, ocupados)
            self._turmas.salvar(trocada)
            return trocada


class MudarHorario:
    """O ADM pede para mudar o horário, e o sistema recusa: o horário não muda durante a vida
    da turma (R24). Pedir o horário que a turma já tem não muda nada."""

    def __init__(self, turmas: RepositorioDeTurmas) -> None:
        self._turmas = turmas

    def executar(
        self,
        usuario: Usuario,
        turma_id: int,
        dias: Iterable[DiaDaSemana],
        inicio: time,
        fim: time,
    ) -> Turma:
        exigir_perfil(usuario, Perfil.ADM, "mudar o horário da turma")
        horario = novo_horario(dias, inicio, fim)
        return mudar_horario(obter_turma(self._turmas, turma_id), horario)


class _LeituraDasTurmas:
    """Dependências e o resumo comuns às listas de turmas."""

    def __init__(
        self,
        turmas: RepositorioDeTurmas,
        materias: ConsultaDeMaterias,
        professores: ConsultaDeProfessores,
        relogio: Relogio,
    ) -> None:
        self._turmas = turmas
        self._materias = materias
        self._professores = professores
        self._relogio = relogio

    def _resumir(self, turmas: Sequence[Turma]) -> list[ResumoDaTurma]:
        agora = self._relogio.agora()
        nomes = {materia.id: materia.nome for materia in self._materias.listar()}
        emails = {professor.id: professor.email for professor in self._professores.listar()}
        return [
            resumir(
                turma,
                ocupacao(self._turmas, turma, agora),
                nomes[turma.materia_id],
                emails[turma.professor_id],
                agora,
            )
            for turma in turmas
        ]


class VerTurmas(_LeituraDasTurmas):
    """O ADM vê todas as turmas."""

    def executar(self, usuario: Usuario) -> list[ResumoDaTurma]:
        exigir_perfil(usuario, Perfil.ADM, "ver todas as turmas")
        return self._resumir(self._turmas.listar())


class VerMinhasTurmas(_LeituraDasTurmas):
    """O professor vê só as turmas que o ADM atribuiu a ele, com nível, dias e horário (H20)."""

    def executar(self, usuario: Usuario) -> list[ResumoDaTurma]:
        exigir_perfil(usuario, Perfil.PROFESSOR, "ver as próprias turmas")
        return self._resumir(self._turmas.do_professor(usuario.id))


@dataclass(frozen=True)
class CasosDeUsoDeTurmas:
    """Os casos de uso do módulo, montados pelo main.py e entregues às telas."""

    criar_turma: CriarTurma
    trocar_professor: TrocarProfessor
    mudar_horario: MudarHorario
    ver_turmas: VerTurmas
    ver_minhas_turmas: VerMinhasTurmas
