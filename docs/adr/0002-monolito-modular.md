# ADR 0002 — Monolito modular
Data: 2026-11-20
Status: Aceito

## Contexto
O sistema tem áreas com regras próprias: identidade e perfis, nivelamento, turmas, pacotes gravados e vendas ([regras.md](../regras.md)). É preciso decidir como dividir o código do app. Será feito um monolito modular primeiro, sem banco compartilhado entre módulos, com as dependências apontando para dentro.

## Decisão
Um único aplicativo, com um só executável, dividido em módulos por assunto do domínio, em `src/plataforma/modules/`:

| Módulo | Cuida de |
|---|---|
| `identidade` | login, perfis e permissões |
| `materias` | matérias, com os níveis, as faixas do nivelamento e a mensalidade |
| `nivelamento` | questões, teste de nivelamento, nível do aluno e promoção |
| `turmas` | turmas, matrícula, presença e notas |
| `catalogo` | pacotes e aulas gravadas |
| `vendas` | compra e reembolso |

Cada módulo tem quatro pastas:

- `domain/`: regras de negócio como funções puras, sem banco, sem PySide6 e sem ler o relógio (a data entra como parâmetro);
- `application/`: casos de uso e as interfaces (portas) de que eles precisam, como um repositório;
- `infra/`: implementações das portas, com o `sqlite3`;
- `ui/`: telas em PySide6, que só chamam os casos de uso.

O arquivo `src/plataforma/main.py` monta tudo: cria as implementações da `infra/`, passa para os casos de uso e abre a tela de login.

Regras:

- `domain/` nunca importa de `infra/` nem de `ui/`. Um teste de arquitetura (import-linter) roda na CI e falha se isso acontecer.
- Cada módulo cuida das próprias tabelas. Um módulo nunca consulta a tabela de outro: ele chama uma função pública do outro módulo.

## Consequências
- Um executável, um arquivo de banco e uma pipeline de CI só.
- As regras são testadas sem banco e sem mocks, porque são funções puras.
- Há mais pastas e arquivos (portas e implementações) do que num app simples dividido só por camadas.
- O import-linter também consegue proibir que um módulo importe a `infra/` de outro, o que protege a regra das tabelas. Se essa checagem vai entrar: A DEFINIR.

## Atualização de 2026-11-21: módulo materias
A Matéria ganhou um módulo próprio, `materias`, na fatia 2. Ela é usada pelo nivelamento (faixas), pelas turmas (nível máximo e mensalidade) e pelos pacotes, e o EventStorming já a tratava como um agregado próprio. Deixá-la no `nivelamento` faria as turmas e os pacotes perguntarem a mensalidade ao nivelamento. As questões ficam no `nivelamento`, como no agregado Nivelamento do EventStorming. Os outros módulos consultam a matéria por uma função pública do `materias`, sem ler as tabelas dele.
