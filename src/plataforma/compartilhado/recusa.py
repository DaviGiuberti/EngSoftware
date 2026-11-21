"""Recusa de uma regra de negócio."""


class Recusa(Exception):
    """Uma regra recusou a ação. A mensagem diz o motivo e é mostrada na tela (RNF02).

    Cada recusa declara a mensagem no atributo mensagem. Quando o texto depende da ação,
    como "Só o ADM pode cadastrar matéria.", quem recusa passa a mensagem ao criar a recusa.
    """

    mensagem: str = ""

    def __init__(self, mensagem: str | None = None) -> None:
        super().__init__(mensagem or self.mensagem)
