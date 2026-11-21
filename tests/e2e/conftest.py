"""Configuração dos testes de ponta a ponta, que abrem as janelas do app com o pytest-qt."""

import os

# Sem tela: a janela não aparece durante os testes, e o mesmo teste roda na CI.
# Para ver a janela, rode com a variável QT_QPA_PLATFORM=windows.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
