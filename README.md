# Plataforma de Ensino por Níveis

Projeto final de Engenharia de Software (UNIFESP). O aluno faz um teste de nivelamento, estuda em turmas ao vivo do seu nível ou com pacotes de aulas gravadas, e sobe um nível por vez.

É um aplicativo para Windows que roda num computador só: aluno, professor e ADM fazem login no mesmo app, e os dados ficam num arquivo SQLite local.

- **Download:** [Releases](https://github.com/DaviGiuberti/EngSoftware/releases)
- **Quadro Kanban:** [GitHub Projects](https://github.com/users/DaviGiuberti/projects/4)

Stack: Python 3.12, interface em PySide6, banco SQLite e executável gerado pelo PyInstaller. Testes com pytest e pytest-qt ([ADR 0001](docs/adr/0001-stack.md)).

> O código ainda não existe: o repositório tem só a documentação. Os comandos de "Como rodar" e "Como testar" passam a funcionar quando o esqueleto do sistema entrar na `main`, e o executável aparece em Releases a partir da primeira versão.

## Como rodar

**Pelo executável:** baixe o `.exe` da última versão em [Releases](https://github.com/DaviGiuberti/EngSoftware/releases) e abra. Não precisa instalar o Python.

**Pelo código:** com o [Python 3.12](https://www.python.org/downloads/) instalado, prepare o ambiente uma vez, no PowerShell:

```powershell
git clone https://github.com/DaviGiuberti/EngSoftware.git
cd EngSoftware
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Se o PowerShell não deixar rodar o `Activate.ps1`, libere os scripts do seu usuário uma vez com `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Depois, o app abre com 1 comando:

```powershell
python -m plataforma
```

## Como testar

Com o ambiente ativado (`.venv\Scripts\Activate.ps1`):

```powershell
pytest            # todos os testes
pytest --cov      # testes com relatório de cobertura
ruff check .      # lint
mypy src          # typecheck
lint-imports      # teste de arquitetura: domain/ não pode importar a infraestrutura
pip-audit         # dependências com vulnerabilidade conhecida
```

## Estrutura de pastas

```text
.
├── README.md
├── CONTEXT.md                  glossário do domínio (linguagem ubíqua)
├── pyproject.toml              dependências e configuração das ferramentas (a criar)
├── .github/                    templates de PR e de issue de história
├── docs/
│   ├── visao.md                problema, métricas de outcome e escopo do MVP
│   ├── regras.md               regras de negócio (R01, R02...)
│   ├── historias.md            histórias de usuário e critérios de aceitação
│   ├── eventstorming.png       diagrama de EventStorming
│   ├── definition-of-done.md
│   ├── requisitos-nao-funcionais.md
│   ├── adr/                    decisões de arquitetura, uma por arquivo
│   └── ia/                     registros do uso de IA
├── src/plataforma/             código do app (a criar)
│   ├── main.py                 monta tudo e abre o app
│   └── modules/<módulo>/
│       ├── domain/             regras de negócio como funções puras
│       ├── application/        casos de uso e interfaces
│       ├── infra/              banco (sqlite3)
│       └── ui/                 telas (PySide6)
└── tests/                      testes automatizados (a criar)
```

## Documentação

- [Visão do produto](docs/visao.md)
- [Regras de negócio](docs/regras.md)
- [Histórias de usuário](docs/historias.md)
- [Glossário do domínio](CONTEXT.md)
- [EventStorming](docs/eventstorming.png)
- [Definition of Done](docs/definition-of-done.md)
- [Requisitos não funcionais](docs/requisitos-nao-funcionais.md)
- Decisões de arquitetura: [0001 Stack](docs/adr/0001-stack.md), [0002 Monolito modular](docs/adr/0002-monolito-modular.md), [0003 Pagamento simulado](docs/adr/0003-pagamento-simulado.md)
- [Registros do uso de IA](docs/ia/README.md)

## Equipe e processo

Projeto individual. Davi Giuberti faz os três papéis:

- **PO:** ordena o backlog, decide a prioridade e aceita as entregas.
- **SM:** cuida do quadro, do limite de WIP e dos rituais.
- **Dev:** escreve os testes e o código e abre os PRs.

O trabalho segue Kanban contínuo, sem sprints, num quadro do GitHub Projects com limite de WIP (1 em Fazendo, 2 em Em review). Toda mudança entra na `main` por PR, e uma história só está pronta quando cumpre a [Definition of Done](docs/definition-of-done.md).
