# Requisitos não funcionais

Tamanho do projeto: uma pessoa desenvolvendo, um aplicativo que roda num computador só e uma base de demonstração com até 100 alunos e 10 turmas. Os requisitos abaixo valem para esse tamanho. Cada um tem um número e um jeito de conferir.

## Uso

| # | Requisito | Como conferir |
|---|---|---|
| RNF01 | O app abre em até 10 segundos, e cada ação (salvar, abrir uma lista, corrigir o nivelamento) responde em até 1 segundo com a base de demonstração. | Cronometrar no ensaio da demo. |
| RNF02 | Todas as telas e mensagens estão em português e usam os termos do [CONTEXT.md](../CONTEXT.md). Toda recusa de regra diz o motivo (por exemplo, "Turma cheia: você entrou na lista de espera"). | Testes que conferem a mensagem de cada recusa e revisão das telas no PR. |
| RNF03 | Roda no Windows 10 e 11 a partir do executável gerado pelo PyInstaller, sem instalar o Python. | Abrir o executável num computador sem Python. |
| RNF04 | Num clone novo, seguindo só o README, o app abre e os testes passam. | Clonar numa pasta nova e seguir o README. |

## Dados e segurança

| # | Requisito | Como conferir |
|---|---|---|
| RNF05 | Nenhuma operação fica pela metade: cada caso de uso grava tudo ou nada, numa transação. | Teste de integração que força um erro no meio do caso de uso e confere que o banco não mudou. |
| RNF06 | Senha com no mínimo 8 caracteres, guardada só como hash com sal, nunca como texto. | Testes: senha de 7 caracteres é recusada e de 8 é aceita; o valor salvo no banco é diferente da senha. |
| RNF07 | Todo caso de uso confere o perfil do usuário e, quando houver, o dono do recurso. Esconder o botão na tela não basta. | Testes: aluno chamando um caso de uso de ADM é recusado; professor lançando nota na turma de outro professor é recusado. |
| RNF08 | Todo SQL usa parâmetros (`?`). Texto digitado pelo usuário nunca é colado dentro da consulta. | Teste que salva um nome com aspas e `;` e lê o mesmo texto de volta, e review do PR. |
| RNF09 | Nenhuma dependência com vulnerabilidade conhecida. | `pip-audit` na CI e Dependabot toda semana. |
| RNF10 | Um erro inesperado mostra uma mensagem curta em português, sem o traceback, e o detalhe vai para o log. | Teste que força uma exceção e confere a mensagem e o log. |

## Manutenção

| # | Requisito | Como conferir |
|---|---|---|
| RNF11 | Pelo menos 90% das linhas de `src/plataforma/modules/*/domain/` cobertas por testes. | `pytest --cov` na CI. |
| RNF12 | `domain/` não importa de `infra/` nem de `ui/`, nem usa `sqlite3` ou PySide6. | Teste de arquitetura (`lint-imports`) na CI. |
| RNF13 | Zero erros de lint e de typecheck. | `ruff check .` e `mypy src` na CI. |

## Log e versões

| # | Requisito | Como conferir |
|---|---|---|
| RNF14 | O app grava um log em arquivo, uma linha JSON por evento, com data, usuário, ação e resultado. Guarda no máximo 5 arquivos de 1 MB e nunca grava senha. | Teste que faz login e confere que a senha não aparece no log. |
| RNF15 | SLI: porcentagem das ações sem erro inesperado, contadas no log. SLO: 99% no mês. O error budget é o 1% que sobra: se ele acabar, as funcionalidades novas param até o app voltar a ficar estável. | Contagem dos erros no arquivo de log. |
| RNF16 | Toda versão é uma release no GitHub, com o executável gerado pela CI. Para voltar atrás, basta abrir o executável da release anterior. Antes de mudar a estrutura do banco, o app guarda uma cópia do arquivo do banco e mantém as 3 últimas, para que o executável e os dados voltem juntos. | Rollback testado pelo menos uma vez. |

## Fora do escopo

- Vários computadores usando os mesmos dados.
- Proteger o arquivo do banco de quem já tem acesso ao computador: quem abre o arquivo SQLite vê e altera os dados.
- Limite de tentativas de login.
- macOS e Linux.
