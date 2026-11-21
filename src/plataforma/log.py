"""Log do app (RNF14): uma linha JSON por ação, com data, usuário, ação e resultado.

Guarda no máximo 5 arquivos de 1 MB. Quem registra recebe só o e-mail do usuário, nunca a
senha.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

TAMANHO_MAXIMO_DO_ARQUIVO = 1_000_000
ARQUIVOS_ANTIGOS = 4  # com o arquivo atual, são 5
BRASILIA = timezone(timedelta(hours=-3))

_logger = logging.getLogger("plataforma")


class _LinhaJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        linha: dict[str, object] = {
            "data": datetime.fromtimestamp(record.created, BRASILIA).isoformat(timespec="seconds"),
            "usuario": getattr(record, "usuario", None),
            "acao": getattr(record, "acao", None),
            "resultado": getattr(record, "resultado", None),
        }
        motivo = getattr(record, "motivo", None)
        if motivo is not None:
            linha["motivo"] = motivo
        if record.exc_info:
            linha["detalhe"] = self.formatException(record.exc_info)
        return json.dumps(linha, ensure_ascii=False)


def configurar_log(pasta: Path, tamanho_maximo: int = TAMANHO_MAXIMO_DO_ARQUIVO) -> None:
    """Grava o log em pasta/plataforma.log e troca de arquivo a cada tamanho_maximo bytes."""
    fechar_log()
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = RotatingFileHandler(
        pasta / "plataforma.log",
        maxBytes=tamanho_maximo,
        backupCount=ARQUIVOS_ANTIGOS,
        encoding="utf-8",
    )
    arquivo.setFormatter(_LinhaJson())
    _logger.addHandler(arquivo)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


def fechar_log() -> None:
    """Fecha o arquivo do log. Sem isso, o Windows não deixa apagar a pasta."""
    for handler in list(_logger.handlers):
        _logger.removeHandler(handler)
        handler.close()


def registrar_acao(
    acao: str, usuario: str | None, resultado: str, motivo: str | None = None
) -> None:
    _logger.info(
        acao, extra={"acao": acao, "usuario": usuario, "resultado": resultado, "motivo": motivo}
    )


def registrar_erro(acao: str, usuario: str | None) -> None:
    """Chamado dentro de um except: grava o traceback no detalhe."""
    _logger.exception(acao, extra={"acao": acao, "usuario": usuario, "resultado": "erro"})
