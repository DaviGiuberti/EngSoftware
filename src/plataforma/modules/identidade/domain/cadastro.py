"""Cadastro de usuários (H38): uma conta por e-mail (R39) e o primeiro ADM."""

from plataforma.compartilhado.recusa import Recusa


class EmailInvalido(Recusa):
    mensagem = "Informe um e-mail válido, como ana@exemplo.com."


class EmailJaCadastrado(Recusa):
    mensagem = "Este e-mail já está cadastrado."


class PrimeiroAdmJaCriado(Recusa):
    mensagem = "O primeiro ADM já foi criado."


def normalizar_email(email: str) -> str:
    """Tira os espaços das pontas e passa para minúsculas, para comparar e-mails (R39)."""
    return email.strip().lower()


def validar_email(email: str) -> None:
    """Recusa o que não tem a forma nome@domínio, com um só @ e sem espaços."""
    # Sem @, o partition devolve o domínio vazio, e a primeira checagem já recusa.
    nome, _, dominio = email.partition("@")
    if not nome or not dominio or "@" in dominio or any(c.isspace() for c in email):
        raise EmailInvalido()


def exigir_email_livre(email_ja_cadastrado: bool) -> None:
    """R39: cada e-mail tem uma só conta."""
    if email_ja_cadastrado:
        raise EmailJaCadastrado()


def exigir_que_nao_haja_adm(ja_existe_adm: bool) -> None:
    """O primeiro ADM só é criado quando o app ainda não tem nenhum ADM."""
    if ja_existe_adm:
        raise PrimeiroAdmJaCriado()
