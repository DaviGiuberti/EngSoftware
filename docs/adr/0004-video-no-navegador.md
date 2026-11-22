# ADR 0004 — Aula gravada aberta no navegador
Data: 2026-11-22
Status: Aceito

## Contexto
As aulas gravadas são vídeos do YouTube (não listados), e a visão falava em vídeo incorporado. O app é para computador, em PySide6 ([ADR 0001](0001-stack.md)). Para mostrar o vídeo dentro de uma tela, seria preciso o QtWebEngine, um navegador embutido no Qt.

## Decisão
O botão "Assistir" confere o acesso do aluno ao pacote (R12, R61) e abre o vídeo no navegador padrão do computador, pelo link do YouTube. O app não mostra o vídeo dentro da tela.

## Consequências
- O executável não leva o QtWebEngine, que o deixaria por volta de 150 MB maior.
- O YouTube às vezes recusa tocar o vídeo incorporado fora de um site (erro 153); no navegador, o vídeo toca como em qualquer link.
- O link fica visível para o aluno, que pode guardá-lo e assistir depois de o acesso vencer. Como os vídeos são não listados e o pagamento é simulado ([ADR 0003](0003-pagamento-simulado.md)), esse risco é aceito no MVP.
- Os testes de ponta a ponta conferem o link que o app pede para abrir, sem abrir o navegador.
