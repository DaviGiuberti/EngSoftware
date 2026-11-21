# Plataforma de Ensino por Níveis

Projeto final de Engenharia de Software (UNIFESP). O aluno faz um teste de nivelamento, estuda em turmas ao vivo do seu nível ou com pacotes de aulas gravadas, e sobe um nível por vez.

É um aplicativo para Windows que roda num computador só: aluno, professor e ADM fazem login no mesmo app, e os dados ficam num arquivo SQLite local.

- **Download:** [Releases](https://github.com/DaviGiuberti/EngSoftware/releases)
- **Quadro Kanban:** [GitHub Projects](https://github.com/users/DaviGiuberti/projects/4)

Stack: Python 3.12, interface em PySide6, banco SQLite e executável gerado pelo PyInstaller. Testes com pytest e pytest-qt ([ADR 0001](docs/adr/0001-stack.md)).

> O executável aparece em Releases a partir da primeira versão. Até lá, rode pelo código ou gere o `.exe` na sua máquina (veja [Gerar o executável](#gerar-o-executável)).

## Como rodar

**Pelo executável:** baixe o `.exe` da última versão em [Releases](https://github.com/DaviGiuberti/EngSoftware/releases) e abra. Não precisa instalar o Python.

**Pelo código:** com o [Python 3.12](https://www.python.org/downloads/) instalado, prepare o ambiente uma vez, no PowerShell:

```powershell
git clone https://github.com/DaviGiuberti/EngSoftware.git
cd EngSoftware
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

O `py -3.12` cria o ambiente com o Python 3.12 mesmo que o computador tenha outras versões instaladas. O `py` vem junto com o instalador do python.org.

Se o PowerShell não deixar rodar o `Activate.ps1`, libere os scripts do seu usuário uma vez com `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Depois, o app abre com 1 comando:

```powershell
python -m plataforma
```

A janela mostra "Banco: ok" quando o banco foi criado ou atualizado e respondeu. Veja [onde ficam os dados](#onde-ficam-os-dados).

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

Os testes de ponta a ponta abrem as janelas sem mostrá-las na tela, por isso rodam também na CI, que não tem tela.

A CI ([ci.yml](.github/workflows/ci.yml)) roda esses mesmos comandos em todo PR, numa máquina Windows, e falha se o código de `domain/` tiver menos de 90% de cobertura (RNF11). Para conferir essa cobertura na sua máquina, depois do `pytest --cov`:

```powershell
coverage report --include="*/modules/*/domain/*" --fail-under=90
```

## Gerar o executável

Com o ambiente ativado:

```powershell
pyinstaller plataforma.spec --noconfirm
```

O `.exe` sai em `dist\plataforma.exe`. É um arquivo só, que abre sem console e já leva o Python, o Qt e as migrações.

## Onde ficam os dados

O banco fica em `%LOCALAPPDATA%\Plataforma\plataforma.db`. É o mesmo arquivo para o app rodando pelo código e para qualquer `.exe`, em qualquer pasta. Para abrir a pasta, aperte Win + R e digite `%LOCALAPPDATA%\Plataforma`. Os testes usam bancos temporários e não mexem nesse arquivo.

Ao abrir, o app aplica as migrações novas de `src/plataforma/migracoes/`. Antes de mudar um banco que já existia, ele guarda uma cópia em `%LOCALAPPDATA%\Plataforma\copias\`, com o nome `plataforma-antes-da-NNNN.db`, e mantém só as 3 mais recentes (RNF16).

**Para voltar uma versão:** feche o app e abra o `.exe` da release anterior. Se a versão nova mudou o banco, ela criou uma cópia em `copias\` na primeira vez que abriu (confira a data). Nesse caso, antes de abrir o `.exe` antigo, guarde o `plataforma.db` atual em outro lugar e ponha no lugar dele essa cópia, renomeada para `plataforma.db`. O que foi feito no app depois da atualização se perde.

## Estrutura de pastas

```text
.
├── README.md
├── CONTEXT.md                  glossário do domínio (linguagem ubíqua)
├── pyproject.toml              dependências e configuração das ferramentas
├── plataforma.spec             receita do PyInstaller para gerar o .exe
├── .github/                    CI e templates de PR e de issue de história
├── docs/
│   ├── visao.md                problema, métricas de outcome e escopo do MVP
│   ├── regras.md               regras de negócio (R01, R02...)
│   ├── historias.md            histórias de usuário e critérios de aceitação
│   ├── eventstorming.png       diagrama de EventStorming
│   ├── definition-of-done.md
│   ├── requisitos-nao-funcionais.md
│   ├── adr/                    decisões de arquitetura, uma por arquivo
│   └── ia/                     registros do uso de IA
├── src/plataforma/             código do app
│   ├── __main__.py             permite abrir com python -m plataforma
│   ├── main.py                 monta tudo e abre o app
│   ├── banco.py                migrações, cópias do banco e verificação
│   ├── janela_principal.py     janela principal
│   ├── migracoes/              migrações .sql numeradas (0001_inicial.sql, ...)
│   └── modules/<módulo>/
│       ├── domain/             regras de negócio como funções puras
│       ├── application/        casos de uso e interfaces
│       ├── infra/              banco (sqlite3)
│       └── ui/                 telas (PySide6)
└── tests/
    ├── integracao/             testes com um banco SQLite temporário
    └── e2e/                    testes das janelas com o pytest-qt
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
