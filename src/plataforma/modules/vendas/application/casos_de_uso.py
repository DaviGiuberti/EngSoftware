"""Casos de uso das vendas (H15): o aluno compra o pacote publicado pelo preço do momento (R15,
R59), e a compra dá o acesso de 12 meses (R12, R60). O catalogo lê os acessos pela
ConsultaDeAcessos, ligada à porta Acessos dele no main.py (ADR 0002)."""

from dataclasses import dataclass
from datetime import date, datetime

from plataforma.compartilhado.relogio import Relogio
from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.catalogo.application.casos_de_uso import ConsultaDePacotes
from plataforma.modules.catalogo.domain.aulas_do_aluno import AcessoAoPacote
from plataforma.modules.catalogo.domain.pacote import EstadoPacote
from plataforma.modules.identidade.domain.autorizacao import exigir_perfil
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.vendas.application.portas import RepositorioDeCompras
from plataforma.modules.vendas.domain.compra import Compra, acesso, acesso_ate, nova_compra


@dataclass(frozen=True)
class CompraFeita:
    """A compra e o último dia do acesso que ela dá (R60)."""

    compra: Compra
    acesso_ate: date


class ConsultaDeAcessos:
    """O acesso do aluno a cada pacote que comprou, para o catalogo (ADR 0002)."""

    def __init__(self, compras: RepositorioDeCompras) -> None:
        self._compras = compras

    def do_aluno(self, aluno_id: int, agora: datetime) -> dict[int, AcessoAoPacote]:
        """O acesso de cada pacote vem da compra mais recente dele (R12)."""
        acessos: dict[int, AcessoAoPacote] = {}
        for compra in self._compras.do_aluno(aluno_id):
            acessos[compra.pacote_id] = acesso(compra, agora)
        return acessos


class ComprarPacote:
    """H15: o aluno compra o pacote publicado, com ou sem nivelamento (R31), pelo preço de agora.
    Com acesso ativo ao mesmo pacote, a compra é recusada (R12)."""

    def __init__(
        self,
        compras: RepositorioDeCompras,
        pacotes: ConsultaDePacotes,
        relogio: Relogio,
        transacao: Transacao,
    ) -> None:
        self._compras = compras
        self._pacotes = pacotes
        self._relogio = relogio
        self._transacao = transacao

    def executar(self, aluno: Usuario, pacote_id: int) -> CompraFeita:
        exigir_perfil(aluno, Perfil.ALUNO, "comprar pacote")
        agora = self._relogio.agora()
        with self._transacao():
            pacote = self._pacotes.obter(pacote_id)
            anteriores = [c for c in self._compras.do_aluno(aluno.id) if c.pacote_id == pacote.id]
            nova = nova_compra(
                aluno.id,
                pacote.id,
                pacote.preco_em_centavos or 0,
                publicado=pacote.estado == EstadoPacote.PUBLICADO,
                anteriores=anteriores,
                agora=agora,
            )
            compra = self._compras.adicionar(nova)
            return CompraFeita(compra, acesso_ate(compra.comprada_em))


@dataclass(frozen=True)
class CasosDeUsoDeVendas:
    """Os casos de uso do módulo, montados pelo main.py e entregues às telas."""

    comprar: ComprarPacote


def montar_casos_de_uso_de_vendas(
    compras: RepositorioDeCompras,
    pacotes: ConsultaDePacotes,
    relogio: Relogio,
    transacao: Transacao,
) -> CasosDeUsoDeVendas:
    return CasosDeUsoDeVendas(comprar=ComprarPacote(compras, pacotes, relogio, transacao))
