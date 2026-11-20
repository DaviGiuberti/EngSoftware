# ADR 0001 — Stack do projeto
Data: 2026-11-20
Status: Aceito

## Contexto
O projeto precisa de regras de negócio testadas, de uma interface interativa e de testes automatizados em três níveis: unidade, integração e ponta a ponta. É um aplicativo para computador, gerado com PyInstaller. A solução precisa caber no que uma pessoa consegue construir e manter.

## Decisão
Um aplicativo para Windows, em Python, que roda localmente. Os dados ficam num arquivo SQLite no próprio computador, e aluno, professor e ADM fazem login no mesmo app.

| Parte | Escolha |
|---|---|
| Linguagem | Python 3.12 |
| Interface | PySide6 (Qt) |
| Banco | SQLite, pelo módulo `sqlite3` da biblioteca padrão, com SQL escrito à mão e parâmetros (`?`). Migrações em arquivos `.sql` numerados |
| Executável | PyInstaller, gerado pela CI e publicado como release no GitHub |
| Testes | pytest (unidade e integração), pytest-qt (ponta a ponta, clicando nas telas) e pytest-cov (cobertura) |
| Qualidade | ruff (lint), mypy (typecheck), import-linter (teste de arquitetura) e pip-audit (dependências) |

Por quê:

- App local: não tem servidor nem hospedagem. O deploy vira uma release do executável no GitHub, gerada pela CI.
- PySide6: já traz tabelas e formulários, e o pytest-qt permite fazer os testes de ponta a ponta clicando nos botões, inclusive na CI sem tela.
- `sqlite3`: vem com o Python, sem dependência extra.
- ruff, mypy, import-linter e pip-audit: A DEFINIR.

## Alternativas consideradas
| Alternativa | Por que não foi escolhida |
|---|---|
| Site em TypeScript: Node + Fastify + Prisma + PostgreSQL e React + Vite | O autor não quer fazer site: exige servidor, hospedagem, deploy e telas em React. |
| Aplicação web rodando só no computador (`docker compose up`), sem site no ar | Continuaria com as telas em React. |
| App em Python com servidor central | Vários computadores usariam os mesmos dados, mas voltariam a ser necessários uma API hospedada, deploy e monitoramento. |
| CustomTkinter ou Tkinter na interface | Testar as telas automaticamente dá mais trabalho. |
| SQLAlchemy, um ORM | É mais uma biblioteca para aprender. |

## Consequências
- Não há servidor, hospedagem nem segredo de produção. A demo roda num computador só.
- Os testes de integração usam um SQLite temporário, sem Docker.
- Os dados ficam num computador só: dois alunos em computadores diferentes não veem as mesmas turmas. Na demo, os perfis se revezam no mesmo app, entrando e saindo.
- Quem tem acesso ao computador consegue abrir o arquivo do banco.
- O SQL de todas as tabelas e as migrações são escritos e mantidos à mão.
- O PyInstaller só gera o executável para o sistema em que roda, então a CI precisa de uma máquina Windows para gerar o `.exe`.
- Mostrar o vídeo do YouTube dentro do app exige o QtWebEngine, que deixa o executável bem maior.
