"""Casos de uso das vendas (H15, H17): o aluno compra o pacote publicado pelo preço do momento
(R15, R59), e a compra dá o acesso de 12 meses (R12, R60). Até as 23h59 do 7º dia, ele pede o
reembolso, que encerra o acesso e apaga as aulas concluídas do pacote (R13, R63). O catalogo lê os
acessos pela ConsultaDeAcessos, ligada à porta Acessos dele no main.py (ADR 0002)."""

from dataclasses import dataclass
from datetime import date, datetime

from plataforma.compartilhado.relogio import Relogio
from plataforma.compartilhado.transacao import Transacao
from plataforma.modules.catalogo.application.aulas_do_aluno import ApagarAulasConcluidas
from plataforma.modules.catalogo.application.casos_de_uso import ConsultaDePacotes
from plataforma.modules.catalogo.domain.aulas_do_aluno import AcessoAoPacote
from plataforma.modules.catalogo.domain.pacote import EstadoPacote
from plataforma.modules.identidade.domain.autorizacao import exigir_perfil
from plataforma.modules.identidade.domain.usuario import Perfil, Usuario
from plataforma.modules.vendas.application.portas import RepositorioDeCompras
from plataforma.modules.vendas.domain.compra import (
    Compra,
    SemCompra,
    acesso,
    acesso_ate,
    nova_compra,
    reembolsar,
)


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
            atual = acesso(compra, agora)
            # R63: se a compra mais recente foi reembolsada, o pacote sai de "Meus pacotes".
            if atual is None:
                acessos.pop(compra.pacote_id, None)
            else:
                acessos[compra.pacote_id] = atual
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


class PedirReembolso:
    """H17: o aluno pede o reembolso da compra mais recente do pacote, até as 23h59 do 7º dia, sem
    condição sobre o quanto assistiu (R13). O acesso acaba, e as aulas concluídas do pacote são
    apagadas na mesma transação (R63, RNF05)."""

    def __init__(
        self,
        compras: RepositorioDeCompras,
        apagar_concluidas: ApagarAulasConcluidas,
        relogio: Relogio,
        transacao: Transacao,
    ) -> None:
        self._compras = compras
        self._apagar_concluidas = apagar_concluidas
        self._relogio = relogio
        self._transacao = transacao

    def executar(self, aluno: Usuario, pacote_id: int) -> Compra:
        """Devolve a compra reembolsada, com o valor devolvido."""
        exigir_perfil(aluno, Perfil.ALUNO, "pedir reembolso")
        agora = self._relogio.agora()
        with self._transacao():
            do_pacote = [c for c in self._compras.do_aluno(aluno.id) if c.pacote_id == pacote_id]
            if not do_pacote:
                raise SemCompra()
            reembolsada = reembolsar(do_pacote[-1], agora)
            self._compras.reembolsar(reembolsada.id, agora)
            self._apagar_concluidas.executar(aluno.id, pacote_id)
            return reembolsada


@dataclass(frozen=True)
class CasosDeUsoDeVendas:
    """Os casos de uso do módulo, montados pelo main.py e entregues às telas."""

    comprar: ComprarPacote
    pedir_reembolso: PedirReembolso


def montar_casos_de_uso_de_vendas(
    compras: RepositorioDeCompras,
    pacotes: ConsultaDePacotes,
    apagar_concluidas: ApagarAulasConcluidas,
    relogio: Relogio,
    transacao: Transacao,
) -> CasosDeUsoDeVendas:
    return CasosDeUsoDeVendas(
        comprar=ComprarPacote(compras, pacotes, relogio, transacao),
        pedir_reembolso=PedirReembolso(compras, apagar_concluidas, relogio, transacao),
    )
