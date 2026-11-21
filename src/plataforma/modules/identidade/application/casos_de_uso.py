"""Casos de uso da identidade: cadastrar aluno, criar o primeiro ADM e entrar (H38), e
cadastrar e habilitar professores (H29)."""

import secrets
from dataclasses import dataclass

from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.identidade.application.portas import (
    RepositorioDeProfessores,
    RepositorioDeUsuarios,
)
from plataforma.modules.identidade.domain.autorizacao import exigir_perfil
from plataforma.modules.identidade.domain.cadastro import (
    AlunoNaoEncontrado,
    exigir_email_livre,
    exigir_que_nao_haja_adm,
    normalizar_email,
    validar_email,
)
from plataforma.modules.identidade.domain.login import autenticar
from plataforma.modules.identidade.domain.professor import (
    Professor,
    ProfessorNaoEncontrado,
    habilitar,
)
from plataforma.modules.identidade.domain.senha import gerar_hash, validar_senha
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.materias.application.casos_de_uso import ConsultaDeMaterias

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


class ConsultaDeAlunos:
    """Os outros módulos acham um aluno pelo e-mail (ADR 0002)."""

    def __init__(self, usuarios: RepositorioDeUsuarios) -> None:
        self._usuarios = usuarios

    def obter_por_email(self, email: str) -> Usuario:
        credencial = self._usuarios.buscar_credencial(normalizar_email(email))
        if credencial is None or credencial.usuario.perfil != Perfil.ALUNO:
            raise AlunoNaoEncontrado()
        return credencial.usuario


class CadastrarProfessor:
    """O ADM cadastra o professor com e-mail e senha. Depois, ele entra como qualquer perfil."""

    def __init__(self, usuarios: RepositorioDeUsuarios, transacao: Transacao) -> None:
        self._usuarios = usuarios
        self._transacao = transacao

    def executar(self, usuario: Usuario, email: str, senha: str) -> Usuario:
        exigir_perfil(usuario, Perfil.ADM, "cadastrar professor")
        with self._transacao():
            return _adicionar_usuario(self._usuarios, email, senha, Perfil.PROFESSOR)


class ConsultaDeProfessores:
    """Leitura dos professores e das habilitações, para as telas e os outros módulos (ADR 0002).

    O e-mail do professor aparece nas turmas para qualquer perfil, então a consulta não confere
    o perfil.
    """

    def __init__(self, professores: RepositorioDeProfessores) -> None:
        self._professores = professores

    def listar(self) -> list[Professor]:
        return self._professores.listar()

    def obter(self, professor_id: int) -> Professor:
        professor = self._professores.buscar(professor_id)
        if professor is None:
            raise ProfessorNaoEncontrado()
        return professor


class HabilitarProfessor:
    """O ADM habilita o professor numa matéria, e ele passa a dar aula em todos os níveis dela
    (R11)."""

    def __init__(
        self,
        professores: RepositorioDeProfessores,
        materias: ConsultaDeMaterias,
        transacao: Transacao,
    ) -> None:
        self._professores = professores
        self._materias = materias
        self._transacao = transacao

    def executar(self, usuario: Usuario, professor_id: int, materia_id: int) -> Professor:
        """Devolve o professor com a habilitação nova."""
        exigir_perfil(usuario, Perfil.ADM, "habilitar professor")
        materia = self._materias.obter(materia_id)
        with self._transacao():
            professor = ConsultaDeProfessores(self._professores).obter(professor_id)
            habilitado = habilitar(professor, materia.id, materia.nome)
            self._professores.adicionar_habilitacao(professor.id, materia.id)
            return habilitado


@dataclass(frozen=True)
class CasosDeUsoDaIdentidade:
    """Os casos de uso do módulo, montados pelo main.py e entregues às telas."""

    cadastrar_aluno: CadastrarAluno
    entrar: Entrar
    criar_primeiro_adm: CriarPrimeiroAdm
    cadastrar_professor: CadastrarProfessor
    habilitar_professor: HabilitarProfessor
    consulta_de_professores: ConsultaDeProfessores


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
