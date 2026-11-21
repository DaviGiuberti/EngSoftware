"""Recusa de uma regra de negócio."""


class Recusa(Exception):
    """Uma regra recusou a ação. A mensagem diz o motivo e é mostrada na tela (RNF02)."""
