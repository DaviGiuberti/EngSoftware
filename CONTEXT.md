# Linguagem ubíqua

Glossário do domínio da plataforma de ensino por níveis. Cada termo tem um só significado, e o código usa o mesmo nome. As regras citadas estão em [docs/regras.md](docs/regras.md).

## Convenções de nome no código

- Nomes do domínio em português, sem acento: `Matricula`, `Promocao`, `Questao`.
- Entidades e tipos em PascalCase (`ListaDeEspera`). Campos, funções e valores em camelCase (`emRevisao`, `nivelMaximo`).
- Um termo novo entra aqui antes de entrar no código. Se um nome mudar, ele muda aqui e no código no mesmo commit.

## Pessoas e perfis

| Termo | Significado | Nome no código |
|---|---|---|
| Usuário | Pessoa com login (e-mail e senha) na plataforma. Tem um perfil. | `Usuario` |
| Perfil | Papel do usuário: aluno, professor ou ADM. Define o que ele pode fazer. | `Perfil` (`aluno`, `professor`, `adm`) |
| Aluno | Usuário com perfil de estudante. Faz o nivelamento, se matricula em turmas e compra pacotes. | `Aluno` |
| Professor | Usuário que dá aula nas turmas que o ADM atribui a ele, lança presença e nota e cria pacotes. | `Professor` |
| ADM | Usuário que administra a plataforma: matérias, professores, turmas, publicação de pacotes e métricas. | `Adm` |
| Habilitação | Permissão que o ADM dá ao professor para dar aula numa matéria, em todos os níveis dela (R11). | `Habilitacao` |

## Matérias, níveis e nivelamento

| Termo | Significado | Nome no código |
|---|---|---|
| Matéria | Assunto ensinado, como Física. Define quantos níveis tem, as faixas e as questões do nivelamento e o valor da mensalidade. | `Materia` |
| Nível | Degrau da trilha de uma matéria, do N1 até o nível máximo. O aluno tem um nível em cada matéria (R01). | `Nivel` |
| Nível máximo | Último nível de uma matéria. Ser aprovado nele conclui a trilha (R09). | `nivelMaximo` |
| Trilha | Sequência de níveis de uma matéria, do N1 ao nível máximo, percorrida um nível por vez (R09). | `Trilha` |
| Nivelamento | Prova de múltipla escolha, feita na plataforma uma vez por matéria, que define o nível inicial do aluno. Tem 60 minutos (R03, R30). | `Nivelamento` |
| Questão | Pergunta de múltipla escolha do nivelamento, com uma alternativa correta, cadastrada pelo ADM. | `Questao` |
| Faixa | Intervalo de nota do nivelamento ligado a um nível, como 40–69% → N2. O ADM cadastra as faixas de cada matéria (R02). | `Faixa` |

## Turmas e etapas

| Termo | Significado | Nome no código |
|---|---|---|
| Turma | Grupo de alunos que estuda uma matéria ao vivo com um professor, em dias e horário fixos, com até 12 vagas. É contínua: começa no nível que o ADM escolhe e passa para o nível seguinte a cada etapa, até concluir o nível máximo (R04, R24, R25). | `Turma` |
| Horário | Dias da semana (1 ou 2) e horas de início e de fim das aulas de uma turma. Não muda durante a vida da turma (R04, R24). | `Horario` |
| Vaga | Lugar de um aluno numa turma. Cada turma tem 12. | `vagas` |
| Etapa | Período de 24 aulas da turma num nível. Termina depois da 24ª aula, com a prova final (R17). | `Etapa` |
| Aula | Encontro ao vivo da turma, no horário dela, pelo link do Google Meet. Numerada de 1 a 24 dentro da etapa. | `Aula` |
| Aula não realizada | Aula que não aconteceu (feriado, professor doente). Não conta nas 24 e é reposta no fim da etapa, no mesmo horário (R18). | `naoRealizada` (situação da `Aula`) |
| Matrícula | Vínculo do aluno com uma turma. Começa com o pagamento da primeira mensalidade, só antes da 13ª aula da etapa, e guarda a aula de entrada, a partir da qual as faltas contam (R08, R19, R27). | `Matricula` |
| Lista de espera | Lista, em ordem de entrada, dos alunos que esperam vaga numa turma cheia. Quando abre vaga, o 1º tem 72 horas para confirmar (R05). | `ListaDeEspera` |
| Presença | Registro, por aula e por aluno, de que ele esteve presente ou ausente. Lançado pelo professor da turma ou pelo ADM (R10). | `Presenca` |
| Falta | Presença marcada como ausente. Só conta a partir da entrada do aluno na turma; o limite é de 6 por etapa (R08). | `Presenca` com `presente: false` |
| Prova final | Prova do fim da etapa, aplicada pelo professor fora da plataforma. O professor lança a nota (R20). | `ProvaFinal` |
| Correção | Mudança de uma presença ou nota já lançada. O professor corrige até 72 horas depois do lançamento; depois, só o ADM, e o nível só muda para cima (R22). | `Correcao` |

## Resultado e promoção

| Termo | Significado | Nome no código |
|---|---|---|
| Resultado da etapa | Situação do aluno no fim da etapa: aprovado (no máximo 6 faltas e nota ≥ 7), reprovado ou pendente, quando a nota ainda não foi lançada (R08, R23). | `ResultadoEtapa` (`aprovado`, `reprovado`, `pendente`) |
| Promoção | Subida de exatamente um nível no fim da etapa, para o aluno aprovado. Nas regras também aparece como "subir de nível" (R08, R09). | `Promocao` |
| Certificado | Documento emitido pela plataforma: de nível, na promoção; de trilha, ao concluir o nível máximo; de pacote, fora do MVP (R16, R33). | `Certificado` (`nivel`, `trilha`, `pacote`) |

## Mensalidade

| Termo | Significado | Nome no código |
|---|---|---|
| Mensalidade | Valor mensal da turma, definido por matéria. A primeira é paga na matrícula, e as seguintes vencem todo mês no dia da matrícula (R27). | `Mensalidade` |
| Vencimento | Data em que uma mensalidade deve ser paga. | `vencimento` |
| Tolerância | Os 7 dias depois do vencimento em que o aluno com mensalidade atrasada ainda mantém a vaga (R28). | `tolerancia` |
| Pagamento | Pagamento simulado de uma mensalidade ou de uma compra. Não há gateway no MVP. | `Pagamento` |

## Pacotes gravados

| Termo | Significado | Nome no código |
|---|---|---|
| Pacote | Conjunto de aulas gravadas de uma matéria e um nível, vendido junto. Criado pelo professor (R15). | `Pacote` |
| Estado do pacote | Ponto do pacote no fluxo rascunho → em revisão → publicado → arquivado. O professor envia para revisão; o ADM publica ou devolve, e pode publicar de novo um pacote arquivado (R15). | `EstadoPacote` (`rascunho`, `emRevisao`, `publicado`, `arquivado`) |
| Aula gravada | Vídeo de um pacote, incorporado do YouTube (não listado). | `AulaGravada` |
| Aula concluída | Marcação do aluno de que terminou uma aula gravada. Conta como atividade de estudo. | `AulaConcluida` |
| Vitrine | Lista dos pacotes publicados, de todos os níveis, com destaque para os do nível do aluno (R31). | `Vitrine` |
| Preço | Valor de um pacote. Só o ADM define e altera (R15). | `preco` |
| Compra | Aquisição simulada de um pacote, que cria um acesso (R12). | `Compra` |
| Acesso | Direito de assistir a um pacote por 12 meses a partir da compra. Enquanto está ativo, o aluno não compra o mesmo pacote de novo (R12). | `Acesso` |
| Reembolso | Devolução do valor de uma compra de pacote, pedida até as 23h59 do 7º dia depois da compra (R13). Não existe para mensalidade (R29). | `Reembolso` |
| Cupom | Código de desconto percentual, de até 50%, só para pacotes. Fora do MVP (R14). | `Cupom` |
| Simulado | Prova de múltipla escolha de um pacote, liberada depois de 100% das aulas, que dá o certificado de pacote. Fora do MVP (R16). | `Simulado` |

## Métricas

| Termo | Significado | Nome no código |
|---|---|---|
| Atividade de estudo | Presença numa aula da turma ou aula gravada concluída. É o que as métricas contam. | `AtividadeDeEstudo` |
| M1, taxa de progressão | Porcentagem dos alunos que concluíram o nivelamento no período e foram promovidos pelo menos uma vez em até 6 meses. | `taxaDeProgressao` |
| M2, continuidade na trilha | Porcentagem dos alunos com nivelamento feito há pelo menos 4 semanas que tiveram atividade de estudo na 4ª semana. | `continuidadeNaTrilha` |
| M3, tempo até estudar no nível certo | Mediana dos dias entre o nivelamento e a primeira atividade de estudo no nível recebido. | `tempoAteNivelCerto` |

## Termos que não usamos

| Não use | Use | Por quê |
|---|---|---|
| teste avulso | nivelamento | O nome surgiu na entrevista de regras e foi entendido de jeitos diferentes por quatro rodadas. Não existe outra prova de nível além do nivelamento e da prova final. |
| frequência, % de presença | faltas | A R08 conta faltas (no máximo 6), e as aulas antes da entrada do aluno contam como presença. Uma porcentagem esconde isso. |
| o nível termina, fim do nível | fim da etapa | O nível é do aluno. Quem termina é a etapa da turma. |
| inscrição | matrícula | O aluno se matricula numa turma. Não existe inscrição em aula avulsa. |
| fila | lista de espera | Um nome só para a mesma coisa. |
| curso | turma ou pacote | "Curso" não diz se o estudo é ao vivo ou gravado. |
