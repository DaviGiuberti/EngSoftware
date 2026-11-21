"""Horário do app: tudo no horário de Brasília (visão, seção 5)."""

from datetime import timedelta, timezone

# O Brasil não tem mais horário de verão desde 2019, então o fuso é fixo em -03:00. Com um
# fuso fixo, o app não depende do banco de fusos horários, que o Windows não traz.
BRASILIA = timezone(timedelta(hours=-3))
