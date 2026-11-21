"""Banco SQLite do app: migrações, cópias de segurança antes de migrar (RNF16), conexão,
transações e verificação."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

PASTA_MIGRACOES = Path(__file__).parent / "migracoes"
COPIAS_MANTIDAS = 3


def conectar(caminho_banco: Path) -> sqlite3.Connection:
    """Abre a conexão que o app usa, com as chaves estrangeiras ligadas.

    O sqlite3 não abre transações sozinho (isolation_level=None): cada caso de uso abre a
    sua com transacao(conexao).
    """
    conexao = sqlite3.connect(caminho_banco, isolation_level=None)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


@contextmanager
def transacao(conexao: sqlite3.Connection) -> Iterator[None]:
    """Grava tudo ou nada (RNF05): confirma no fim do bloco e desfaz se ele levantar erro."""
    conexao.execute("BEGIN")
    try:
        yield
    except BaseException:
        conexao.execute("ROLLBACK")
        raise
    conexao.execute("COMMIT")


def aplicar_migracoes(caminho_banco: Path, pasta_migracoes: Path, pasta_copias: Path) -> None:
    """Aplica, em ordem numérica, as migrações .sql que o banco ainda não tem.

    Cada migração roda numa transação: se falhar, ela é desfeita, a última aplicada não
    muda e o erro diz qual arquivo falhou. Antes de mudar um banco que já existia, guarda
    uma cópia dele em pasta_copias e mantém só as 3 mais recentes.
    """
    banco_ja_existia = caminho_banco.exists()
    migracoes = _ler_migracoes(pasta_migracoes)
    caminho_banco.parent.mkdir(parents=True, exist_ok=True)
    # isolation_level=None: o sqlite3 não abre transações sozinho; _aplicar controla cada uma.
    with closing(sqlite3.connect(caminho_banco, isolation_level=None)) as conexao:
        ultima = _ultima_aplicada(conexao)
        pendentes = [(numero, arquivo) for numero, arquivo in migracoes if numero > ultima]
        if not pendentes:
            return
        if banco_ja_existia:
            _guardar_copia(conexao, caminho_banco, pasta_copias, antes_da=pendentes[0][0])
        for numero, arquivo in pendentes:
            _aplicar(conexao, numero, arquivo)


def verificar_banco(caminho_banco: Path) -> bool:
    """Faz SELECT 1 no banco e diz se ele respondeu."""
    with closing(sqlite3.connect(caminho_banco)) as conexao:
        linha: tuple[int] | None = conexao.execute("SELECT 1").fetchone()
    return linha == (1,)


def _ler_migracoes(pasta_migracoes: Path) -> list[tuple[int, Path]]:
    """Lista as migrações como (número, arquivo), em ordem. O número vem do nome: 0003_x.sql."""
    migracoes = [
        (int(arquivo.name.split("_", 1)[0]), arquivo)
        for arquivo in pasta_migracoes.iterdir()
        if arquivo.suffix == ".sql"
    ]
    return sorted(migracoes)


def _ultima_aplicada(conexao: sqlite3.Connection) -> int:
    """Lê a última migração aplicada. Num banco novo, cria a tabela de controle com 0."""
    conexao.execute(
        "CREATE TABLE IF NOT EXISTS controle_migracao (ultima_aplicada INTEGER NOT NULL)"
    )
    linha = conexao.execute("SELECT ultima_aplicada FROM controle_migracao").fetchone()
    if linha is None:
        conexao.execute("INSERT INTO controle_migracao (ultima_aplicada) VALUES (0)")
        return 0
    return int(linha[0])


def _guardar_copia(
    conexao: sqlite3.Connection, caminho_banco: Path, pasta_copias: Path, antes_da: int
) -> None:
    """Copia o banco para pasta_copias e apaga as cópias mais antigas que as 3 últimas."""
    pasta_copias.mkdir(parents=True, exist_ok=True)
    nome = f"{caminho_banco.stem}-antes-da-{antes_da:04d}{caminho_banco.suffix}"
    with closing(sqlite3.connect(pasta_copias / nome)) as copia:
        conexao.backup(copia)
    # O número tem 4 dígitos, então a ordem alfabética dos nomes é a ordem das migrações.
    copias = sorted(pasta_copias.glob(f"{caminho_banco.stem}-antes-da-*{caminho_banco.suffix}"))
    for antiga in copias[:-COPIAS_MANTIDAS]:
        antiga.unlink()


def _aplicar(conexao: sqlite3.Connection, numero: int, arquivo: Path) -> None:
    """Roda uma migração e atualiza a última aplicada, tudo numa transação só."""
    sql = arquivo.read_text(encoding="utf-8")
    try:
        # O BEGIN vai dentro do script porque o executescript faz COMMIT antes de rodar.
        conexao.executescript("BEGIN;\n" + sql)
        conexao.execute("UPDATE controle_migracao SET ultima_aplicada = ?", (numero,))
        conexao.execute("COMMIT")
    except sqlite3.Error as erro:
        if conexao.in_transaction:
            conexao.execute("ROLLBACK")
        erro.add_note(f"Migração que falhou: {arquivo.name}")
        raise
