# Histórias de usuário

Histórias da plataforma, escritas a partir do [regras.md](regras.md) e do [visao.md](visao.md). Os termos seguem o glossário [CONTEXT.md](../CONTEXT.md).

Formato: Como [perfil], quero [ação] para [benefício]. Cada história tem prioridade e cita as regras que usa.

Prioridade:

- **Alta:** faz parte do caminho principal da hipótese (nivelamento → turma → presença e prova final → promoção; compra e estudo de pacotes; métricas). Sem ela, uma fatia do MVP não funciona de ponta a ponta.
- **Média:** está no MVP, mas trata prazos, exceções e correções em volta do caminho principal.
- **Baixa:** fica fora do MVP (R14 e R16).

## Critérios de aceitação

Cada história tem de 2 a 5 critérios no formato Dado / Quando / Então. Cada critério vira um teste automático quase palavra por palavra, e o nome do cenário começa pela regra que ele testa.

Dados usados nos exemplos, quando o critério não diz outra coisa:

- **Física:** 3 níveis (N1 a N3), faixas 0–39% → N1, 40–69% → N2 e 70–100% → N3, mensalidade de R$ 200.
- **Matemática:** 5 níveis (N1 a N5), faixas 0–19% → N1, 20–39% → N2, 40–59% → N3, 60–79% → N4 e 80–100% → N5, mensalidade de R$ 250.
- **Professores:** Carlos, habilitado em Física; Dora, habilitada em Física e Matemática.
- **Alunos:** Ana e Bruno, no N2 de Física.
- **Datas e horas:** datas sem ano são do mesmo ano; horários de Brasília.

## Aluno

### H01 · Fazer o nivelamento

Como aluno, quero fazer o teste de nivelamento de uma matéria para começar no nível certo. Prioridade: Alta. Regras: R01, R02, R03, R30, R34.

```gherkin
Cenário: R02 — 39% coloca o aluno no N1
  Dado um aluno sem nível em Física
  Quando ele conclui o nivelamento de Física com 39%
  Então o nível dele em Física passa a ser N1

Cenário: R02 — 40% coloca o aluno no N2
  Dado um aluno sem nível em Física
  Quando ele conclui o nivelamento de Física com 40%
  Então o nível dele em Física passa a ser N2

Cenário: R01 — o nível de uma matéria não muda o de outra
  Dado um aluno no N3 de Física e sem nível em Matemática
  Quando ele conclui o nivelamento de Matemática com 25%
  Então ele fica no N2 de Matemática
  E continua no N3 de Física

Cenário: R03 — o nivelamento é feito uma vez por matéria
  Dado um aluno que já tem nível em Física
  Quando ele tenta iniciar o nivelamento de Física
  Então o sistema recusa, informando que o nivelamento de Física já foi feito

Cenário: R34 — os 60 minutos acabam
  Dado um aluno no nivelamento de Física com 18 de 30 questões respondidas e 60 minutos usados
  Quando o tempo acaba
  Então o teste é encerrado e corrigido com as 18 respostas dadas
  E as 12 questões sem resposta contam como erro
```

### H02 · Retomar o nivelamento

Como aluno, quero retomar o nivelamento de onde parei se fechar o navegador ou a conexão cair, para não perder o tempo e as respostas que já dei. Prioridade: Média. Regras: R30.

```gherkin
Cenário: R30 — as respostas dadas continuam salvas
  Dado um aluno que respondeu 10 das 30 questões do nivelamento de Física
  Quando ele fecha o navegador e abre o nivelamento de novo
  Então as 10 respostas continuam marcadas
  E ele continua o teste de onde parou

Cenário: R30 — o tempo só corre com o teste aberto
  Dado um aluno que fechou o nivelamento de Física com 25 minutos usados
  Quando ele reabre o teste dois dias depois
  Então ele tem 35 minutos restantes
```

### H03 · Ver meu nível

Como aluno, quero ver meu nível em cada matéria para saber em que ponto da trilha estou. Prioridade: Alta. Regras: R01, R09.

```gherkin
Cenário: R01 — um nível por matéria
  Dado um aluno no N2 de Física e no N4 de Matemática
  Quando ele abre o perfil
  Então ele vê "Física: N2" e "Matemática: N4"

Cenário: R01 — matéria sem nivelamento
  Dado um aluno no N2 de Física que não fez o nivelamento de Matemática
  Quando ele abre o perfil
  Então ele vê Matemática sem nível, com a opção de fazer o nivelamento

Cenário: R09 — trilha concluída
  Dado um aluno aprovado na etapa do N3 de Física, o nível máximo da matéria
  Quando ele abre o perfil
  Então ele vê a trilha de Física como concluída
```

### H04 · Matricular-se numa turma

Como aluno, quero ver as turmas do meu nível numa matéria e me matricular em uma, pagando a primeira mensalidade, para estudar ao vivo com professor. Prioridade: Alta. Regras: R06, R07, R19, R27.

```gherkin
Cenário: R27 — a matrícula começa com o pagamento da primeira mensalidade
  Dado um aluno no N2 de Física
  E uma turma de Física do N2 com vaga
  Quando ele se matricula em 10/03 e paga a primeira mensalidade de R$ 200
  Então ele fica matriculado na turma
  E a próxima mensalidade vence em 10/04

Cenário: R06 — só turma do nível do aluno
  Dado um aluno no N2 de Física
  Quando ele tenta se matricular numa turma de Física do N3
  Então o sistema recusa a matrícula

Cenário: R07 — horário que se sobrepõe
  Dado um aluno matriculado numa turma de Matemática às terças, das 19h às 20h30
  Quando ele tenta se matricular numa turma de Física às terças e quintas, das 20h às 21h30
  Então o sistema recusa a matrícula por conflito de horário

Cenário: R19 — matrícula antes da 13ª aula
  Dada uma turma de Física do N2 que já deu 12 aulas da etapa
  Quando um aluno no N2 de Física se matricula
  Então a matrícula é aceita, e ele fará da 13ª à 24ª aula

Cenário: R19 — matrícula depois da 13ª aula
  Dada uma turma de Física do N2 que já deu 13 aulas da etapa
  Quando um aluno no N2 de Física tenta se matricular
  Então o sistema recusa a matrícula
```

### H05 · Entrar na lista de espera

Como aluno, quero entrar na lista de espera de uma turma cheia para conseguir uma vaga quando alguém sair. Prioridade: Média. Regras: R04, R05, R06.

```gherkin
Cenário: R04 — turma cheia recusa matrícula
  Dada uma turma de Física do N2 com 12 alunos
  Quando um aluno no N2 de Física tenta se matricular
  Então o sistema recusa a matrícula e oferece a lista de espera da turma

Cenário: R05 — a lista segue a ordem de entrada
  Dada uma turma cheia com Ana em 1º lugar na lista de espera
  Quando Bruno entra na lista de espera
  Então Bruno fica em 2º lugar

Cenário: R06 — a lista de espera também exige o nível da turma
  Dado um aluno no N1 de Física
  Quando ele tenta entrar na lista de espera de uma turma cheia de Física do N2
  Então o sistema recusa

Cenário: R05 — turma com vaga não tem lista de espera
  Dada uma turma de Física do N2 com 11 alunos
  Quando um aluno no N2 de Física tenta entrar na lista de espera
  Então o sistema recusa e oferece a matrícula
```

### H06 · Confirmar a vaga da lista de espera

Como aluno na lista de espera, quero ser avisado na plataforma quando abrir uma vaga e confirmá-la em até 72 horas para não perder a minha vez. Prioridade: Média. Regras: R05, R35.

```gherkin
Cenário: R05 — abre vaga e o 1º da lista é avisado
  Dada uma turma cheia com Ana em 1º e Bruno em 2º na lista de espera
  Quando um aluno sai da turma em 10/03 às 14h
  Então Ana recebe um aviso na plataforma para confirmar a vaga até 13/03 às 14h

Cenário: R05 — a vaga fica reservada durante o prazo
  Dada uma turma com 11 alunos e uma vaga que Ana pode confirmar até 13/03 às 14h
  Quando outro aluno tenta se matricular na turma em 11/03
  Então o sistema recusa a matrícula, porque a vaga está reservada

Cenário: R05 — confirmação dentro do prazo
  Dado que Ana pode confirmar uma vaga até 13/03 às 14h
  Quando ela confirma em 13/03 às 13h59
  Então ela fica matriculada na turma
  E sai da lista de espera

Cenário: R05 — o prazo vence e a vaga passa para o próximo
  Dado que Ana podia confirmar uma vaga até 13/03 às 14h e não confirmou
  Quando o prazo termina
  Então Bruno recebe o aviso para confirmar a vaga até 16/03 às 14h
  E Ana sai da lista de espera
```

### H07 · Pagar a mensalidade

Como aluno, quero pagar a mensalidade da turma e ver quando vence a próxima para não perder a vaga por atraso. Prioridade: Média. Regras: R27, R28, R37.

```gherkin
Cenário: R27 — vencimento no dia da matrícula
  Dado um aluno que se matriculou em 10/03 numa turma de Física
  Quando ele abre a turma em 20/03
  Então ele vê a próxima mensalidade, de R$ 200, com vencimento em 10/04

Cenário: R27 — pagamento em dia
  Dada a mensalidade de 10/04 em aberto
  Quando o aluno paga em 08/04
  Então a mensalidade fica paga
  E a próxima vence em 10/05

Cenário: R28 — pagamento atrasado dentro da tolerância
  Dada a mensalidade de 10/04 sem pagamento
  Quando o aluno paga em 17/04 às 23h
  Então ele continua na turma
  E a próxima mensalidade vence em 10/05

Cenário: R28 — atraso além da tolerância
  Dada a mensalidade de 10/04 sem pagamento até 17/04 às 23h59
  Quando chega 18/04
  Então o aluno perde a vaga e sai da turma
```

### H08 · Acompanhar faltas e nota

Como aluno, quero acompanhar minhas faltas e minha nota na etapa para saber se vou ser promovido. Prioridade: Média. Regras: R08, R17.

```gherkin
Cenário: R08 — faltas e aulas da etapa
  Dado um aluno com 4 faltas nas 15 aulas já dadas da etapa
  Quando ele abre a turma
  Então ele vê "4 de 6 faltas permitidas" e "aula 15 de 24"

Cenário: R08 — faltas contam só a partir da entrada
  Dado um aluno que entrou na turma antes da 10ª aula da etapa e faltou a 2 aulas desde então
  Quando ele abre a turma
  Então ele vê 2 faltas
  E as 9 aulas anteriores à entrada contam como presença

Cenário: R08 — limite de faltas ultrapassado
  Dado um aluno com 7 faltas na etapa
  Quando ele abre a turma
  Então ele vê o aviso de que passou do limite de 6 faltas e não será promovido nesta etapa
```

### H09 · Promoção de nível

Como aluno, quero ser promovido ao próximo nível no fim da etapa quando cumprir os requisitos, para avançar na trilha. Prioridade: Alta. Regras: R08, R09, R17.

```gherkin
Cenário: R08 — 6 faltas e nota 7 promovem
  Dado um aluno no N2 de Física com 6 faltas na etapa e nota 7 na prova final
  Quando a etapa termina
  Então ele é aprovado e promovido para o N3 de Física

Cenário: R08 — nota abaixo de 7 reprova
  Dado um aluno no N2 de Física com 2 faltas na etapa e nota 6,5 na prova final
  Quando a etapa termina
  Então ele é reprovado e continua no N2 de Física

Cenário: R08 — mais de 6 faltas reprovam
  Dado um aluno no N2 de Física com 7 faltas na etapa e nota 9 na prova final
  Quando a etapa termina
  Então ele é reprovado e continua no N2 de Física

Cenário: R09 — nunca se pula nível
  Dado um aluno no N1 de Física sem faltas e com nota 10 na prova final
  Quando a etapa termina
  Então ele é promovido para o N2 de Física, e não para o N3

Cenário: R09 — aprovação no nível máximo conclui a trilha
  Dado um aluno no N3 de Física, o nível máximo, com 3 faltas e nota 8 na prova final
  Quando a etapa termina
  Então ele continua no N3 de Física
  E a trilha de Física dele fica concluída
```

### H10 · Seguir com a mesma turma

Como aluno, quero que minha turma avance de nível comigo, com o mesmo professor, até o fim da trilha, para seguir com o mesmo grupo sem procurar turma nova a cada nível. Prioridade: Alta. Regras: R04, R09, R25, R26.

```gherkin
Cenário: R04 e R26 — a turma passa para o nível seguinte com o mesmo professor
  Dada uma turma de Física no N2, do professor Carlos, às terças e quintas das 19h às 20h30
  Quando a etapa do N2 termina
  Então a turma passa para o N3, com o mesmo professor, nos mesmos dias e horário
  E começa uma etapa nova, a partir da 1ª aula

Cenário: R04 — o aluno promovido continua na turma
  Dado que Ana foi promovida para o N3 na etapa da sua turma
  Quando a turma passa para o N3
  Então Ana continua matriculada, sem nova matrícula

Cenário: R09 — a turma encerra depois do nível máximo
  Dada uma turma de Física no N3, o nível máximo
  Quando a etapa do N3 termina
  Então a turma é encerrada

Cenário: R25 — o ADM não encerra turma aberta
  Dada uma turma de Física no N2
  Quando o ADM tenta encerrá-la
  Então o sistema recusa

Cenário: R25 — turma sem alunos continua aberta
  Dada uma turma de Física no N2 com um único aluno
  Quando esse aluno sai da turma
  Então a turma continua aberta, com 12 vagas livres
```

### H11 · Recomeçar o nível em outra turma

Como aluno reprovado na etapa, quero encontrar outra turma do mesmo nível para recomeçar o nível sem sair da trilha. Prioridade: Média. Regras: R06, R08, R19, R21, R23.

```gherkin
Cenário: R23 — o reprovado fica na turma durante as 72 horas de correção
  Dado um aluno com nota 5 na prova final do N2, lançada em 10/03 às 10h
  Quando chega 12/03 às 10h
  Então ele continua na turma, ocupando a vaga

Cenário: R21 — sem correção, o reprovado sai da turma
  Dado um aluno com nota 5 na prova final do N2, lançada em 10/03 às 10h e não corrigida
  Quando chega 13/03 às 10h01
  Então ele sai da turma
  E continua no N2 de Física

Cenário: R19 e R21 — o reprovado entra em outra turma do mesmo nível no meio da etapa
  Dado um aluno no N2 de Física que saiu da turma por reprovação
  E outra turma de Física do N2 que já deu 8 aulas da etapa
  Quando ele se matricula nessa turma
  Então a matrícula é aceita
  E as faltas dele contam a partir da 9ª aula
```

### H12 · Receber certificados de nível e de trilha

Como aluno, quero receber um certificado ao ser promovido e outro ao concluir a trilha, para comprovar meu progresso. Prioridade: Média. Regras: R33, R36.

```gherkin
Cenário: R33 — certificado de nível na promoção
  Dado um aluno no N1 de Física
  Quando ele é promovido para o N2
  Então ele recebe o certificado de nível do N1 de Física

Cenário: R36 — certificados no nível máximo
  Dado um aluno no N3 de Física, o nível máximo
  Quando ele é aprovado na etapa do N3
  Então ele recebe o certificado de nível do N3 e o certificado de trilha de Física

Cenário: R33 — reprovação não gera certificado
  Dado um aluno no N2 de Física
  Quando ele é reprovado na etapa
  Então ele não recebe certificado

Cenário: R33 — o nivelamento não gera certificado
  Dado um aluno que ficou no N3 de Física pelo nivelamento
  Quando ele abre os seus certificados
  Então ele não tem certificado do N1 nem do N2 de Física
```

### H13 · Sair da turma

Como aluno, quero sair de uma turma por vontade própria para liberar meu horário quando não puder mais continuar. Prioridade: Média. Regras: R05, R29.

```gherkin
Cenário: R29 — saída sem reembolso da mensalidade
  Dado um aluno no N2 de Física que pagou a mensalidade de 10/03
  Quando ele sai da turma em 20/03
  Então ele deixa de estar matriculado
  E não recebe reembolso da mensalidade
  E continua no N2 de Física

Cenário: R05 — a vaga aberta vai para o 1º da lista de espera
  Dada uma turma cheia com Ana em 1º na lista de espera
  Quando um aluno sai da turma
  Então Ana recebe o aviso para confirmar a vaga em até 72 horas
```

### H14 · Ver a vitrine de pacotes

Como aluno, quero ver a vitrine de pacotes gravados de qualquer nível, com destaque para os do meu nível, para escolher conteúdo que não seja fácil nem difícil demais. Prioridade: Alta. Regras: R15, R31.

```gherkin
Cenário: R15 — só pacotes publicados aparecem
  Dados pacotes de Física em rascunho, em revisão, publicado e arquivado
  Quando um aluno abre a vitrine
  Então ele vê só o pacote publicado

Cenário: R31 — todos os níveis aparecem, com destaque para o do aluno
  Dado um aluno no N2 de Física
  E pacotes publicados de Física do N1, do N2 e do N3
  Quando ele abre a vitrine
  Então os pacotes do N2 de Física aparecem em destaque
  E os do N1 e do N3 também aparecem

Cenário: R31 — aluno sem nível vê todos os pacotes
  Dado um aluno sem nível em nenhuma matéria
  Quando ele abre a vitrine
  Então ele vê todos os pacotes publicados, sem destaque
```

### H15 · Comprar um pacote

Como aluno, quero comprar um pacote gravado, mesmo sem ter feito o nivelamento, para estudar no meu ritmo. Prioridade: Alta. Regras: R12, R15, R31.

```gherkin
Cenário: R31 — compra sem nivelamento
  Dado um aluno sem nível em Física
  E um pacote publicado de Física do N3
  Quando ele compra o pacote em 10/03/2027
  Então ele tem acesso ao pacote até 10/03/2028

Cenário: R12 — compra bloqueada com acesso ativo
  Dado um aluno com acesso ativo a um pacote
  Quando ele tenta comprar o mesmo pacote
  Então o sistema recusa a compra

Cenário: R12 — nova compra depois que o acesso vence
  Dado um aluno cujo acesso a um pacote venceu em 10/03/2028
  Quando ele compra o pacote de novo em 15/03/2028
  Então ele tem acesso ao pacote até 15/03/2029

Cenário: R15 — pacote arquivado não é vendido
  Dado um pacote arquivado
  Quando um aluno tenta comprá-lo
  Então o sistema recusa a compra
```

### H16 · Assistir e concluir aulas gravadas

Como aluno, quero assistir às aulas de um pacote e marcar cada uma como concluída para acompanhar meu progresso. Prioridade: Alta. Regras: R12, R32.

```gherkin
Cenário: R12 — com acesso, o aluno marca a aula como concluída
  Dado um aluno com acesso ativo a um pacote de 10 aulas
  Quando ele marca a 3ª aula como concluída
  Então o pacote mostra 1 de 10 aulas concluídas

Cenário: R12 — acesso vencido bloqueia as aulas
  Dado um aluno cujo acesso a um pacote venceu ontem
  Quando ele tenta abrir uma aula do pacote
  Então o sistema bloqueia a aula

Cenário: R12 — pacote arquivado continua acessível a quem comprou
  Dado um aluno que comprou um pacote há 3 meses
  E o pacote foi arquivado depois da compra
  Quando ele abre uma aula do pacote
  Então ele assiste normalmente

Cenário: R32 — concluir um pacote não promove
  Dado um aluno no N1 de Física que concluiu todas as aulas de um pacote de Física do N1
  Quando ele abre o perfil
  Então ele continua no N1 de Física
```

### H17 · Pedir reembolso de um pacote

Como aluno, quero pedir reembolso de um pacote até o 7º dia depois da compra para recuperar o dinheiro se ele não me servir. Prioridade: Média. Regras: R12, R13.

```gherkin
Cenário: R13 — pedido no último minuto do 7º dia
  Dado um aluno que comprou um pacote em 10/03 às 15h
  Quando ele pede reembolso em 17/03 às 23h59
  Então o reembolso é aceito

Cenário: R13 — pedido depois do 7º dia
  Dado um aluno que comprou um pacote em 10/03 às 15h
  Quando ele pede reembolso em 18/03 às 0h
  Então o sistema recusa o reembolso

Cenário: R13 — o reembolso não depende do quanto foi assistido
  Dado um aluno que comprou um pacote em 10/03 e concluiu todas as aulas
  Quando ele pede reembolso em 12/03
  Então o reembolso é aceito

Cenário: R12 — o reembolso encerra o acesso
  Dado um aluno com reembolso aceito de um pacote
  Quando ele tenta abrir uma aula do pacote
  Então o sistema bloqueia a aula

Cenário: R13 — recompra sem direito a reembolso
  Dado um aluno reembolsado que comprou o mesmo pacote de novo em 20/03
  Quando ele pede reembolso em 21/03
  Então o sistema recusa o reembolso
```

### H18 · Usar cupom

Como aluno, quero usar um cupom na compra de um pacote para pagar menos. Prioridade: Baixa **[Fora do MVP]**. Regras: R14.

```gherkin
Cenário: R14 — desconto percentual
  Dado um pacote de R$ 100 e um cupom válido de 20%
  Quando o aluno compra o pacote com o cupom
  Então ele paga R$ 80

Cenário: R14 — cupom vencido
  Dado um cupom válido até 31/03
  Quando o aluno tenta usá-lo em 05/04
  Então o sistema recusa o cupom

Cenário: R14 — um uso por aluno
  Dado um aluno que já usou o cupom "FISICA20"
  Quando ele tenta usar o mesmo cupom em outra compra
  Então o sistema recusa o cupom

Cenário: R14 — cupons não acumulam
  Dado um aluno que já aplicou um cupom na compra
  Quando ele tenta aplicar um segundo cupom
  Então o sistema recusa o segundo cupom
```

### H19 · Fazer o simulado e receber o certificado de pacote

Como aluno, quero fazer o simulado de um pacote e receber o certificado para comprovar que concluí o conteúdo. Prioridade: Baixa **[Fora do MVP]**. Regras: R16.

```gherkin
Cenário: R16 — simulado só depois de 100% das aulas
  Dado um aluno que concluiu 9 de 10 aulas de um pacote
  Quando ele tenta abrir o simulado
  Então o sistema recusa

Cenário: R16 — nota 6 dá o certificado
  Dado um aluno que concluiu todas as aulas de um pacote
  Quando ele tira 6 no simulado
  Então ele recebe o certificado do pacote

Cenário: R16 — tentativa única
  Dado um aluno que tirou 5 no simulado de um pacote
  Quando ele tenta fazer o simulado de novo
  Então o sistema recusa, até o ADM liberar uma nova tentativa

Cenário: R16 — aula nova não invalida certificado emitido
  Dado um aluno com o certificado de um pacote de 10 aulas
  Quando o professor adiciona a 11ª aula ao pacote
  Então o certificado do aluno continua valendo
```

## Professor

### H20 · Ver minhas turmas

Como professor, quero ver as turmas que o ADM me atribuiu, com dias e horários, para organizar minha agenda. Prioridade: Média. Regras: R24, R26.

```gherkin
Cenário: R24 — o professor vê só as turmas atribuídas a ele
  Dado o professor Carlos com duas turmas de Física
  E a professora Dora com uma turma de Matemática
  Quando Carlos abre as suas turmas
  Então ele vê só as duas turmas de Física, com nível, dias e horário de cada uma

Cenário: R26 — a turma continua com o professor quando muda de nível
  Dada uma turma de Física do Carlos que passou do N2 para o N3
  Quando Carlos abre as suas turmas
  Então ele vê a mesma turma, agora no N3, nos mesmos dias e horário
```

### H21 · Lançar presença

Como professor, quero lançar a presença dos alunos em cada aula para registrar a frequência da turma. Prioridade: Alta. Regras: R08, R10.

```gherkin
Cenário: R10 — lançar presença na própria turma
  Dada a turma de Física do Carlos
  Quando Carlos lança a 5ª aula com Ana presente e Bruno ausente
  Então Ana fica com presença na 5ª aula
  E Bruno fica com 1 falta na etapa

Cenário: R10 — presença em turma de outro professor
  Dada a turma de Física do Carlos
  Quando a professora Dora tenta lançar presença nessa turma
  Então o sistema recusa
```

### H22 · Marcar aula não realizada

Como professor, quero marcar uma aula como não realizada para que ela seja reposta no fim da etapa e não conte nas 24. Prioridade: Média. Regras: R17, R18.

```gherkin
Cenário: R17 e R18 — aula não realizada não conta nas 24
  Dada uma turma de Física que já deu 9 aulas da etapa
  Quando o professor marca a aula de 13/04 como não realizada
  Então a próxima aula continua sendo a 10ª da etapa

Cenário: R18 — reposição no fim da etapa, no mesmo horário
  Dada uma turma às terças e quintas cuja 24ª aula seria numa terça
  Quando uma aula da etapa é marcada como não realizada
  Então a 24ª aula passa para a quinta seguinte, no mesmo horário

Cenário: R18 — aula não realizada não recebe presença
  Dada uma aula marcada como não realizada
  Quando o professor tenta lançar presença nela
  Então o sistema recusa
```

### H23 · Lançar a nota da prova final

Como professor, quero lançar a nota da prova final, aplicada fora da plataforma, para que o sistema decida quem é promovido. Prioridade: Alta. Regras: R10, R17, R20, R23.

```gherkin
Cenário: R20 — lançar a nota depois da 24ª aula
  Dada uma turma do Carlos que já deu as 24 aulas da etapa
  Quando Carlos lança nota 8 para Ana em 10/03 às 10h
  Então a nota de Ana fica registrada, com a data e a hora do lançamento

Cenário: R17 — nota antes do fim da etapa
  Dada uma turma do Carlos que deu 20 aulas da etapa
  Quando Carlos tenta lançar a nota da prova final
  Então o sistema recusa

Cenário: R10 — nota em turma de outro professor
  Dada uma turma de Física do Carlos que já deu as 24 aulas da etapa
  Quando a professora Dora tenta lançar nota nessa turma
  Então o sistema recusa

Cenário: R23 — aluno sem nota continua na turma
  Dado que a etapa do N2 terminou e Carlos ainda não lançou a nota de Ana
  Quando a turma passa para o N3
  Então Ana continua na turma, ocupando a vaga, com o resultado pendente
```

### H24 · Corrigir presença ou nota

Como professor, quero corrigir uma presença ou nota até 72 horas depois de lançá-la para consertar um erro sem depender do ADM. Prioridade: Média. Regras: R22.

```gherkin
Cenário: R22 — correção dentro de 72 horas
  Dado que Carlos lançou nota 6 para Ana em 10/03 às 10h
  Quando ele corrige a nota para 7 em 13/03 às 9h59
  Então a nota de Ana passa a ser 7

Cenário: R22 — correção depois de 72 horas
  Dado que Carlos lançou nota 6 para Ana em 10/03 às 10h
  Quando ele tenta corrigir a nota em 13/03 às 10h01
  Então o sistema recusa, informando que só o ADM pode corrigir

Cenário: R22 — o prazo de 72 horas vale também para presença
  Dado que Carlos lançou falta para Bruno na 5ª aula em 01/03 às 20h30
  Quando ele tenta corrigir para presença em 05/03
  Então o sistema recusa, informando que só o ADM pode corrigir

Cenário: R22 — correção para baixo dentro do prazo
  Dado que Carlos lançou nota 7 para Ana em 10/03 às 10h
  Quando ele corrige a nota para 6 em 11/03
  Então Ana fica reprovada na etapa
```

### H25 · Criar pacote e enviar para revisão

Como professor, quero criar um pacote gravado e enviá-lo para revisão para vendê-lo na plataforma. Prioridade: Alta. Regras: R15.

```gherkin
Cenário: R15 — pacote novo começa em rascunho
  Dado o professor Carlos
  Quando ele cria o pacote "Cinemática", de Física, do N1
  Então o pacote fica em rascunho

Cenário: R15 — enviar para revisão
  Dado o pacote "Cinemática" em rascunho
  Quando Carlos o envia para revisão
  Então o pacote fica em revisão

Cenário: R15 — o professor não define preço
  Dado o pacote "Cinemática" em rascunho
  Quando Carlos tenta definir o preço
  Então o sistema recusa

Cenário: R15 — o professor não publica
  Dado o pacote "Cinemática" em revisão
  Quando Carlos tenta publicá-lo
  Então o sistema recusa
```

### H26 · Editar pacote publicado

Como professor, quero editar um pacote já publicado para corrigir ou acrescentar aulas sem passar por nova revisão. Prioridade: Média. Regras: R15.

```gherkin
Cenário: R15 — edição sem nova revisão
  Dado o pacote "Cinemática" publicado
  Quando Carlos adiciona uma aula
  Então o pacote continua publicado
  E a aula nova já aparece para quem tem acesso

Cenário: R15 — o preço continua com o ADM
  Dado o pacote "Cinemática" publicado por R$ 120
  Quando Carlos tenta mudar o preço
  Então o sistema recusa
```

## ADM

### H27 · Cadastrar matéria

Como ADM, quero cadastrar uma matéria com seus níveis, as faixas de nota do nivelamento e o valor da mensalidade para que o teste coloque o aluno no nível certo e as turmas possam ser cobradas. Prioridade: Alta. Regras: R01, R02, R27, R40.

```gherkin
Cenário: R01 — cada matéria define quantos níveis tem
  Dado o ADM
  Quando ele cadastra Matemática com 5 níveis
  Então Matemática passa a ter os níveis N1 a N5

Cenário: R02 — faixas próprias da matéria
  Dada Matemática com as faixas 0–19% → N1, 20–39% → N2, 40–59% → N3, 60–79% → N4 e 80–100% → N5
  Quando um aluno conclui o nivelamento de Matemática com 45%
  Então ele fica no N3 de Matemática

Cenário: R27 — mensalidade por matéria
  Dadas as mensalidades de R$ 200 em Física e de R$ 250 em Matemática
  Quando um aluno se matricula numa turma de Matemática
  Então a primeira mensalidade cobrada é de R$ 250

Cenário: R40 — nota mínima fora de ordem
  Dado o ADM cadastrando Física com 3 níveis
  Quando ele define a nota mínima do N2 em 70% e a do N3 em 40%
  Então o sistema recusa, informando que a nota mínima do N3 precisa ser maior que a do N2
```

### H28 · Cadastrar questões do nivelamento

Como ADM, quero cadastrar as questões do nivelamento de cada matéria para que o aluno tenha um teste para fazer. Prioridade: Alta. Regras: R02, R41.

```gherkin
Cenário: cadastro de questão
  Dado o ADM
  Quando ele cadastra uma questão de Física com 5 alternativas e marca a correta
  Então a questão passa a fazer parte do nivelamento de Física

Cenário: R41 — questão com 4 alternativas
  Dado o ADM
  Quando ele tenta cadastrar uma questão de Física com 4 alternativas
  Então o sistema recusa, informando que a questão precisa ter 5 alternativas

Cenário: R02 — correção automática pela porcentagem de acertos
  Dado o nivelamento de Física com 20 questões
  Quando um aluno acerta 8
  Então a nota dele é 40% e ele fica no N2 de Física

Cenário: matéria sem questões
  Dada uma matéria sem questões de nivelamento
  Quando um aluno tenta iniciar o nivelamento dela
  Então o sistema recusa, informando que o nivelamento ainda não está disponível
```

### H29 · Cadastrar e habilitar professores

Como ADM, quero cadastrar professores e habilitá-los por matéria para que cada um só dê aula do que domina. Prioridade: Alta. Regras: R11.

```gherkin
Cenário: cadastro de professor
  Dado o ADM
  Quando ele cadastra a professora Dora com e-mail e senha
  Então Dora consegue entrar na plataforma com o perfil de professor

Cenário: R11 — habilitado na matéria, dá aula em todos os níveis
  Dado o professor Carlos, habilitado em Física
  Quando o ADM cria uma turma de Física no N3 com Carlos
  Então a turma é criada

Cenário: R11 — sem habilitação na matéria
  Dado o professor Carlos, habilitado só em Física
  Quando o ADM tenta criar uma turma de Matemática com Carlos
  Então o sistema recusa
```

### H30 · Criar turma

Como ADM, quero criar uma turma com matéria, nível inicial, professor, dias e horário para oferecer aulas ao vivo. Prioridade: Alta. Regras: R04, R07, R11, R24, R43.

```gherkin
Cenário: R11 e R24 — turma nova com professor habilitado
  Dado o professor Carlos, habilitado em Física
  Quando o ADM cria uma turma de Física com nível inicial N2 e Carlos, às terças e quintas, das 19h às 20h30
  Então a turma é criada no N2, antes da 1ª aula da etapa, com 12 vagas

Cenário: R43 — a 1ª aula é no primeiro dia da turma depois da criação
  Dado o ADM na segunda-feira, 23/11, às 14h
  Quando ele cria uma turma às terças e quintas, das 19h às 20h30
  Então a 1ª aula da etapa é na terça-feira, 24/11, às 19h

Cenário: R07 — conflito de horário do professor
  Dado o professor Carlos com uma turma às terças, das 19h às 20h30
  Quando o ADM tenta criar outra turma com Carlos às terças, das 20h às 21h30
  Então o sistema recusa

Cenário: R04 — no máximo 2 aulas por semana
  Dado o ADM
  Quando ele tenta criar uma turma com aulas às segundas, quartas e sextas
  Então o sistema recusa

Cenário: R24 — o horário não muda
  Dada uma turma às terças e quintas, das 19h às 20h30
  Quando o ADM tenta mudar o horário para as 18h
  Então o sistema recusa
```

### H31 · Trocar o professor de uma turma

Como ADM, quero trocar o professor de uma turma quando achar necessário, como quando ele sai ou é desligado, para que a turma nunca fique sem responsável. Prioridade: Média. Regras: R07, R11, R26.

```gherkin
Cenário: R26 — o ADM troca o professor quando quiser
  Dada uma turma de Física do Carlos
  E a professora Dora, habilitada em Física e sem turma nesse horário
  Quando o ADM troca o professor da turma para Dora
  Então Dora passa a ser a professora da turma

Cenário: R11 — o novo professor precisa estar habilitado
  Dada uma turma de Física do Carlos
  Quando o ADM tenta trocar para um professor habilitado só em Matemática
  Então o sistema recusa

Cenário: R07 — o novo professor não pode ter conflito de horário
  Dada uma turma de Física do Carlos às terças, das 19h às 20h30
  E a professora Dora com outra turma às terças, das 19h às 20h30
  Quando o ADM tenta trocar o professor da turma para Dora
  Então o sistema recusa
```

### H32 · Lançar e corrigir presença e nota em qualquer turma

Como ADM, quero lançar e corrigir presença e nota em qualquer turma para resolver lançamentos que o professor esqueceu ou errou. Prioridade: Média. Regras: R10, R22, R23.

```gherkin
Cenário: R10 — o ADM lança presença em qualquer turma
  Dada a turma de Física do Carlos
  Quando o ADM lança a presença da 5ª aula
  Então a presença fica registrada

Cenário: R23 — o ADM lança a nota que o professor não lançou
  Dado que a etapa terminou há 10 dias e Ana continua sem nota
  Quando o ADM lança nota 8 para Ana
  Então a nota de Ana fica registrada

Cenário: R22 — correção do ADM que aprova o aluno
  Dado que Ana, do N2 de Física, foi reprovada com nota 6, lançada em 10/03, e saiu da turma
  Quando o ADM corrige a nota para 7 em 20/03
  Então Ana é promovida para o N3 de Física

Cenário: R22 — correção do ADM que reprova quem já foi promovido
  Dado que Ana foi promovida do N2 para o N3 de Física com nota 8, lançada em 10/03
  Quando o ADM corrige a nota para 5 em 20/03
  Então a nota de Ana passa a ser 5
  E ela continua no N3 de Física
```

### H33 · Abrir exceções no nivelamento

Como ADM, quero liberar que um aluno refaça o nivelamento ou dar mais tempo a ele para resolver casos excepcionais, como um problema técnico durante o teste. Prioridade: Média. Regras: R03, R30, R42.

```gherkin
Cenário: R30 — mais tempo de prova
  Dado um aluno no nivelamento de Física com 5 minutos restantes
  Quando o ADM dá 20 minutos a mais a ele
  Então o aluno passa a ter 25 minutos restantes

Cenário: R03 — o ADM libera refazer
  Dado um aluno que ficou no N1 de Física pelo nivelamento e não está em turma de Física
  Quando o ADM libera que ele refaça o nivelamento e ele tira 75%
  Então o nível dele em Física passa a ser N3

Cenário: R03 — a liberação vale para uma tentativa
  Dado um aluno que refez o nivelamento de Física depois da liberação do ADM
  Quando ele tenta fazer o nivelamento de Física de novo
  Então o sistema recusa

Cenário: R42 — resultado menor no nivelamento refeito
  Dado um aluno que ficou no N2 de Física pelo nivelamento
  Quando o ADM libera que ele refaça o nivelamento e ele tira 30%
  Então ele continua no N2 de Física
```

### H34 · Revisar e publicar pacote

Como ADM, quero revisar um pacote enviado, definir o preço e publicá-lo ou devolvê-lo ao professor para garantir a qualidade do que é vendido. Prioridade: Alta. Regras: R15, R38.

```gherkin
Cenário: R15 — o ADM define o preço e publica
  Dado o pacote "Cinemática" em revisão
  Quando o ADM define o preço de R$ 120 e publica o pacote
  Então o pacote fica publicado e aparece na vitrine por R$ 120

Cenário: R38 — o ADM devolve o pacote
  Dado o pacote "Cinemática" em revisão
  Quando o ADM devolve o pacote
  Então o pacote volta para rascunho
  E Carlos pode editá-lo e enviá-lo de novo

Cenário: R15 — só pacote em revisão é publicado
  Dado o pacote "Cinemática" em rascunho
  Quando o ADM tenta publicá-lo
  Então o sistema recusa

Cenário: R15 — o ADM altera o preço
  Dado o pacote "Cinemática" publicado por R$ 120
  Quando o ADM muda o preço para R$ 100
  Então as compras seguintes custam R$ 100
```

### H35 · Arquivar e publicar de novo

Como ADM, quero arquivar um pacote e, se quiser, publicá-lo de novo, para tirá-lo da vitrine sem prejudicar quem já comprou. Prioridade: Média. Regras: R12, R15.

```gherkin
Cenário: R15 — pacote arquivado sai da vitrine
  Dado o pacote "Cinemática" publicado
  Quando o ADM o arquiva
  Então o pacote some da vitrine

Cenário: R12 — quem comprou mantém o acesso
  Dado um aluno que comprou o pacote "Cinemática" em 10/03/2027
  Quando o ADM arquiva o pacote em 01/06/2027
  Então o aluno continua com acesso até 10/03/2028

Cenário: R15 — o ADM publica de novo um pacote arquivado
  Dado o pacote "Cinemática" arquivado
  Quando o ADM o publica de novo
  Então o pacote volta para a vitrine
```

### H36 · Ver as métricas

Como ADM, quero ver as métricas M1, M2 e M3 do período para saber se a plataforma está resolvendo o problema do aluno. Prioridade: Alta. Regras: nenhuma (vem da seção 4 do visao.md).

```gherkin
Cenário: M1 — taxa de progressão
  Dados 10 alunos que concluíram o nivelamento de Física em março
  E 3 deles promovidos em até 6 meses depois do nivelamento
  Quando o ADM abre as métricas de março
  Então ele vê M1 = 30%

Cenário: M2 — continuidade na trilha
  Dados 10 alunos que fizeram o nivelamento há mais de 4 semanas
  E 5 deles com uma presença ou uma aula gravada concluída na 4ª semana depois do nivelamento
  Quando o ADM abre as métricas
  Então ele vê M2 = 50%

Cenário: M3 — tempo até estudar no nível certo
  Dados 3 alunos cuja primeira atividade de estudo no nível recebido veio 1, 2 e 6 dias depois do nivelamento
  Quando o ADM abre as métricas
  Então ele vê M3 = 2 dias

Cenário: M3 — atividade em outro nível não conta
  Dado um aluno que ficou no N2 de Física pelo nivelamento
  E que só concluiu aulas de um pacote de Física do N1
  Quando o ADM abre as métricas
  Então esse aluno ainda não entra no cálculo da M3
```

### H37 · Criar cupons

Como ADM, quero criar cupons de desconto percentual com validade e limite de usos para fazer promoções. Prioridade: Baixa **[Fora do MVP]**. Regras: R14.

```gherkin
Cenário: R14 — cupom válido
  Dado o ADM
  Quando ele cria o cupom "FISICA20" de 20%, válido até 31/03, com limite de 100 usos
  Então o cupom fica disponível para qualquer pacote

Cenário: R14 — desconto acima de 50%
  Dado o ADM
  Quando ele tenta criar um cupom de 60%
  Então o sistema recusa

Cenário: R14 — só o ADM cria cupons
  Dado o professor Carlos
  Quando ele tenta criar um cupom
  Então o sistema recusa
```

## Todos os perfis

### H38 · Cadastrar-se e entrar na plataforma

Como aluno, quero me cadastrar com e-mail e senha e entrar na plataforma para fazer o nivelamento e estudar no meu nível. Professor e ADM entram do mesmo jeito, e o primeiro ADM é criado na primeira vez que o app abre. Prioridade: Alta. Regras: R39, RNF06, RNF07.

```gherkin
Cenário: RNF06 — senha com menos de 8 caracteres
  Dado um visitante na tela de cadastro
  Quando ele tenta se cadastrar como aluno com a senha "abc1234", de 7 caracteres
  Então o sistema recusa, informando que a senha precisa ter pelo menos 8 caracteres

Cenário: RNF06 — senha com 8 caracteres
  Dado um visitante na tela de cadastro
  Quando ele se cadastra como aluno com o e-mail "ana@exemplo.com" e a senha "abcd1234", de 8 caracteres
  Então ele entra na plataforma com esse e-mail e essa senha, com o perfil de aluno
  E o valor guardado no banco para a senha é diferente de "abcd1234"

Cenário: R39 — e-mail já cadastrado
  Dada Ana, cadastrada com o e-mail "ana@exemplo.com"
  Quando alguém tenta se cadastrar com o e-mail "Ana@Exemplo.com"
  Então o sistema recusa, informando que o e-mail já está cadastrado

Cenário: RNF07 — aluno chamando caso de uso do ADM
  Dada Ana, que entrou na plataforma como aluno
  Quando ela tenta usar uma ação do ADM, como cadastrar matéria
  Então o sistema recusa, informando que só o ADM pode cadastrar matéria

Cenário: primeiro ADM
  Dado o app aberto pela primeira vez, sem nenhum ADM
  Quando a pessoa define o e-mail "adm@exemplo.com" e a senha "admin123"
  Então ela entra na plataforma com o perfil de ADM
  E, nas próximas vezes, o app abre direto na tela de entrar
```

## Rastreabilidade

Toda regra do regras.md é testada por pelo menos um critério.

| Regra | Histórias |
|---|---|
| R01 | H01, H03, H27 |
| R02 | H01, H27, H28 |
| R03 | H01, H33 |
| R04 | H05, H10, H30 |
| R05 | H05, H06, H13 |
| R06 | H04, H05, H11 |
| R07 | H04, H30, H31 |
| R08 | H08, H09, H11, H21 |
| R09 | H03, H09, H10 |
| R10 | H21, H23, H32 |
| R11 | H29, H30, H31 |
| R12 | H15, H16, H17, H35 |
| R13 | H17 |
| R14 | H18, H37 |
| R15 | H14, H15, H25, H26, H34, H35 |
| R16 | H19 |
| R17 | H08, H09, H22, H23 |
| R18 | H22 |
| R19 | H04, H11 |
| R20 | H23 |
| R21 | H11 |
| R22 | H24, H32 |
| R23 | H11, H23, H32 |
| R24 | H20, H30 |
| R25 | H10 |
| R26 | H10, H20, H31 |
| R27 | H04, H07, H27 |
| R28 | H07 |
| R29 | H13 |
| R30 | H01, H02, H33 |
| R31 | H14, H15 |
| R32 | H16 |
| R33 | H12 |
| R34 | H01 |
| R35 | H06 |
| R36 | H12 |
| R37 | H07 |
| R38 | H34 |
| R39 | H38 |
| R40 | H27 |
| R41 | H28 |
| R42 | H33 |
| R43 | H30 |
