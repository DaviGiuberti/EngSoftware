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

## Atualização de 2026-11-22: catalogo e vendas
Na fatia 12, a vitrine, as aulas que o aluno assiste e as aulas concluídas ficam no `catalogo`, e a compra e o acesso ficam no `vendas`. O `vendas` lê os pacotes pela consulta pública do `catalogo` para vender só os publicados, pelo preço do momento. O `catalogo` precisa saber se o aluno tem acesso ao pacote, mas não importa o `vendas`: ele declara uma porta, `Acessos`, e o `main.py` liga a ela a consulta de acessos do `vendas`. Assim a dependência entre os dois módulos tem um sentido só, do `vendas` para o `catalogo`.

## Atualização de 2026-11-22: módulo metricas
As métricas M1, M2 e M3 ganharam um módulo próprio, `metricas`, na fatia 14. Elas cruzam dados de três módulos: os nivelamentos e as promoções do `nivelamento`, as presenças das `turmas` e as aulas concluídas do `catalogo`. Cada um desses módulos ganhou uma consulta pública só de leitura, e o `metricas` as usa sem ler as tabelas de ninguém. Nenhum módulo importa o `metricas`, e ele não tem tabela própria: os números são calculados na hora, a partir do que os outros já guardam.
