"""RNF06: senha com no mínimo 8 caracteres, guardada só como hash com sal."""

import hashlib
import hmac

from plataforma.compartilhado.recusa import Recusa

TAMANHO_MINIMO_DA_SENHA = 8


class SenhaCurta(Recusa):
    mensagem = f"A senha precisa ter pelo menos {TAMANHO_MINIMO_DA_SENHA} caracteres."


def validar_senha(senha: str) -> None:
    """Recusa a senha com menos de 8 caracteres."""
    if len(senha) < TAMANHO_MINIMO_DA_SENHA:
        raise SenhaCurta()


def gerar_hash(senha: str, sal: bytes) -> str:
    """Valor guardado no banco no lugar da senha: 'scrypt$<sal>$<hash>', em hexadecimal.

    O sal entra como parâmetro para a função continuar pura: quem chama sorteia um sal novo
    para cada senha. O custo do scrypt (n=2**14, r=8, p=1) gasta uns 16 MB e dezenas de
    milissegundos por senha, o que encarece adivinhar senhas em massa.
    """
    calculado = hashlib.scrypt(senha.encode(), salt=sal, n=2**14, r=8, p=1)
    return f"scrypt${sal.hex()}${calculado.hex()}"


def senha_confere(senha: str, hash_da_senha: str) -> bool:
    """Diz se a senha digitada gera o mesmo hash, usando o sal guardado junto dele."""
    _, sal, _ = hash_da_senha.split("$")
    return hmac.compare_digest(gerar_hash(senha, bytes.fromhex(sal)), hash_da_senha)
