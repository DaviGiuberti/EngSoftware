# Grill-Me das regras de negócio

Registro da entrevista feita com IA (Claude Code) para levantar as regras de negócio antes de escrever código. Data: 16/11/2026.

## Como foi feito

- O ponto de partida foram as 16 regras abaixo, escritas pelo autor do projeto.
- A IA perguntou sobre casos que as regras não cobriam: empates, limites, cancelamentos, datas, permissões e o que acontece quando algo dá errado. Ela não decidia nada. Cada pergunta trazia opções, e o autor escolhia uma ou escrevia a própria resposta.
- A rodada 1 foi uma pergunta única, em texto. Da rodada 2 em diante, cada rodada teve até 4 perguntas na ferramenta de perguntas do Claude Code.
- Quando uma resposta abria uma dúvida nova, ela virava pergunta na rodada seguinte.
- As regras que a IA achou úteis entraram como sugestões (S01 a S17) em [regras.md](../regras.md), aguardando decisão do autor.

Nas respostas, *(resposta livre)* indica que o autor escreveu a própria resposta em vez de escolher uma das opções.

## Regras de partida

- **R01** O nível do aluno é separado por matéria.
- **R02** A nota do nivelamento define o nível inicial por faixa (0–39% → N1, 40–69% → N2, 70–100% → N3).
- **R03** O aluno só pode refazer o nivelamento da mesma matéria depois de 30 dias.
- **R04** Cada turma tem matéria, nível, professor, horário e no máximo 12 vagas.
- **R05** Turma cheia: o aluno entra numa lista de espera. Se alguém sair, o primeiro da fila entra.
- **R06** O aluno só se matricula em turma do seu nível naquela matéria.
- **R07** Nem o aluno nem o professor podem ter duas turmas no mesmo horário.
- **R08** O aluno sobe 1 nível se tiver frequência ≥ 75% e nota ≥ 7 na prova final do nível.
- **R09** Nunca se pula nível. No nível máximo, a trilha é concluída.
- **R10** O professor só lança presença e nota nas próprias turmas.
- **R11** O professor só dá aula nas matérias e níveis em que o ADM o habilitou.
- **R12** A compra de um pacote libera o acesso por 12 meses.
- **R13** Reembolso só até 7 dias depois da compra e com menos de 30% do pacote assistido.
- **R14** Cupom tem validade, limite de usos, não acumula e tem desconto máximo.
- **R15** Pacote passa por rascunho → em revisão → publicado → arquivado. Só o ADM publica.
- **R16** Certificado só com 100% das aulas assistidas e nota mínima 6 no simulado.

## Rodadas

### Rodada 1: duração da turma

**1.1** (R04, R08) A turma tem começo e fim definidos, como um ciclo com número fixo de aulas que termina na prova final? Ou é contínua, e o aluno entra e sai a qualquer momento?
Resposta *(resposta livre)*: a turma é contínua. Existem várias turmas, cada uma num horário, e o aluno entra em qualquer uma quando quiser. A frequência é calculada dentro da etapa de cada nível: quando a turma vai do N2 para o N3, a etapa do N2 acaba. O mesmo professor acompanha a turma do início ao fim; só troca se sair ou for demitido. Os alunos podem mudar.

Sugestão adicionada depois desta rodada: S01.

### Rodada 2: etapa, reprovação e entrada no meio

**2.1** (R04, R08) A turma avança de nível junto. Quem ou o que decide o momento em que a etapa termina e a turma sobe?
Opções: data definida pelo ADM · o professor encerra · número fixo de aulas
Resposta: **número fixo de aulas.**

**2.2** (R06, R08) Quando a turma sobe de N2 para N3, o que acontece com o aluno que não cumpriu a R08?
Opções: sai e procura turma N2 · o sistema move para uma turma N2 · fica na turma, como exceção à R06
Resposta: **sai e procura sozinho uma turma do N2.**

**2.3** (R08) Se o aluno entra no meio da etapa, sobre quais aulas se calculam os 75% de frequência?
Opções: só desde a entrada · todas as aulas da etapa · entrada com prazo limite
Resposta *(resposta livre)*: contam só as faltas desde a entrada; as aulas anteriores contam como presença. Cada nível tem um limite de faltas, e quem não passou desse limite está aprovado na frequência.

**2.4** (R11) O professor acompanha a turma do início ao fim. O que acontece quando a turma vai subir para um nível em que ele não está habilitado?
Opções: só abre turma quem é habilitado em todos os níveis · o ADM troca o professor · a turma fica bloqueada
Resposta *(resposta livre)*: esquecer essa regra; o professor tem que estar habilitado em todos os níveis.

Sugestão adicionada depois desta rodada: S02.

### Rodada 3: número de aulas, faltas e novo nivelamento

**3.1** Como é definido o número fixo de aulas da etapa?
Opções: o ADM define por nível · igual para todos os níveis · definido na turma
Resposta: **igual para todos os níveis.**

**3.2** (R08) Como é definido o limite de faltas?
Opções: 25% das aulas da etapa · número fixo por nível
Resposta: **25% das aulas da etapa.**

**3.3** (R03, R09) Um aluno no N1 refaz o nivelamento depois de 30 dias e tira 80% (faixa do N3). O que acontece? E se cair numa faixa abaixo do nível atual?
Opções: o novo resultado sempre vale · só vale se for maior · sobe no máximo 1 nível · refazer só serve para quem ainda não tem nível
Resposta *(resposta livre)*: o teste só serve para subir para o próximo nível. O teste do N1 tem questões do N1, para ver se o aluno sabe o suficiente para ir ao N2. A prova que define o nível da pessoa é feita uma vez só.

**3.4** (R11) A habilitação passa a ser só por matéria (habilitado na matéria = pode dar aula em todos os níveis dela)?
Opções: sim, só por matéria · não há habilitação
Resposta: **sim, só por matéria.**

### Rodada 4: prova final, alunos sem turma e níveis

**4.1** (R08) Como é feita a prova final do nível?
Opções: na plataforma, com correção automática · fora da plataforma, e o professor lança a nota
Resposta: **fora da plataforma; o professor lança a nota.**

**4.2** (R03) Um aluno que estuda só com pacotes gravados consegue subir de nível? E a espera de 30 dias ainda vale para alguma coisa?
Opções: só sobe pela turma e a R03 sai · teste avulso, refeito após 30 dias · teste avulso, sem espera
Resposta *(resposta livre)*: teste avulso, refeito após 30 dias. Além disso, o aluno pode comprar pacotes gravados de qualquer nível, e quem só quer aulas gravadas nem precisa fazer o nivelamento.

**4.3** Quantas aulas tem cada etapa? (O limite de faltas é 25% disso.)
Opções: 16 · 20 · 24
Resposta: **24 aulas (limite de 6 faltas).**

**4.4** (R02, R09) Quantos níveis existem em cada matéria?
Opções: 3 níveis · mais níveis acima do N3 · cada matéria define
Resposta: **cada matéria define.**

Sugestões adicionadas depois desta rodada: S03 e S04.

### Rodada 5: pagamento da turma, faixas e prova perdida

**5.1** Como o aluno paga pelas turmas?
Opções: mensalidade · por etapa · sem cobrança
Resposta: **mensalidade.**

**5.2** (R02) Como funcionam as faixas do nivelamento numa matéria com 2 ou 5 níveis?
Opções: faixas fixas, com mínimo de 3 níveis · o ADM define por matéria · divisão igual de 0–100%
Resposta: **o ADM define as faixas de cada matéria.**

**5.3** Um aluno matriculado em turma pode fazer o teste avulso sem esperar o fim da etapa?
Opções: não, só quem está sem turma · sim, e se passar sai da turma
Resposta: **sim, e se passar sai da turma.** (Mudou na rodada 7.)

**5.4** (R08) Se o aluno falta à prova final, o que acontece?
Opções: nota 0 e não sobe · segunda chamada · o professor decide
Resposta: **o professor decide; o sistema não impõe regra.**

Sugestão adicionada depois desta rodada: S05.

### Rodada 6: inadimplência, nota pendente e lista de espera

**6.1** O aluno não pagou a mensalidade. O que acontece?
Opções: perde a vaga na hora · tem prazo de tolerância · fica bloqueado, mas mantém a vaga
Resposta: **prazo de tolerância.**

**6.2** (R08) A turma terminou as 24 aulas, mas falta a nota de um aluno. O que acontece?
Opções: a turma espera todas as notas · sem nota, não sobe · o aluno fica pendente na turma
Resposta: **fica pendente na turma até a nota sair; se reprovar, sai.**

**6.3** (R05) Abriu uma vaga numa turma com lista de espera. Como o primeiro da fila entra?
Opções: entra automaticamente · tem um prazo para confirmar
Resposta: **tem um prazo para confirmar.**

**6.4** Existe espera mínima para fazer o teste avulso pela primeira vez num nível?
Opções: pode fazer na hora · só depois de 30 dias no nível
Resposta *(resposta livre)*: o teste para subir de nível é feito uma vez só, depois do fim das aulas.

### Rodada 7: esclarecer o teste avulso

**7.1** Para o aluno sem turma, o teste avulso só é liberado "depois do fim das aulas". Que aulas são essas?
Opções: um pacote do nível concluído · todos os pacotes do nível · sem requisito de aulas
Resposta *(resposta livre)*: o teste avulso pode ser feito a qualquer momento, e o aluno entra no meio de turmas de outros níveis sem problema. Só o teste para subir de nível é feito depois do fim das aulas. Existem dois tipos de teste.

**7.2** O aluno fez o teste avulso e reprovou. O que acontece?
Opções: refaz após 30 dias · conclui as aulas de novo · só sobe pela turma
Resposta: **conclui as aulas de novo.**

**7.3** Um aluno em turma ainda pode fazer o teste avulso no meio da etapa?
Opções: não, em turma só a prova final · sim, se cumprir o requisito
Resposta: **não; em turma, só a prova final.**

**7.4** Quantos dias de tolerância para a mensalidade atrasada?
Opções: 3 · 5 · 7
Resposta: **7 dias.**

### Rodada 8: confirmar os dois testes

**8.1** A IA resumiu: além do nivelamento, existe (1) a prova final da etapa, para quem está em turma, e (2) o teste avulso, para quem não está em turma, feito na plataforma a qualquer momento, que sobe o aluno 1 nível. Está certo?
Opções: está certo · o teste avulso é outra coisa
Resposta *(resposta livre)*: o teste avulso é só para quem não tem nível, para saber em que turma colocar o aluno. Esquecer a espera de 30 dias.

**8.2** O aluno sem turma reprovou no teste avulso. Quando ele pode tentar subir de novo?
Opções: refaz quando quiser · refaz após 30 dias · só pela turma · depois de concluir um pacote
Resposta *(resposta livre)*: o teste avulso é só para quem não tem nível. Quem tem nível e reprova na prova recomeça o mesmo nível e assiste às aulas de novo.

**8.3** (R05) Quanto tempo o primeiro da fila tem para confirmar a vaga?
Opções: 24 h · 48 h · 72 h
Resposta: **72 horas.**

**8.4** O aluno com nota pendente ocupa uma das 12 vagas?
Opções: ocupa a vaga · não ocupa
Resposta: **ocupa a vaga.**

Mudanças nas sugestões depois desta rodada: S04 removida (tratava do teste avulso) e S03 ajustada.

### Rodada 9: entrada tardia, repetente, valor e horário

**9.1** (R08) Existe um mínimo de aulas na turma para fazer a prova final? Sem mínimo, quem entra na 23ª aula já faz a prova.
Opções: não, faz a prova normal · exige um mínimo · a entrada é bloqueada no fim da etapa
Resposta *(resposta livre)*: o aluno pode entrar até a metade da etapa; o mínimo é de 12 aulas.

**9.2** O aluno que reprovou pode entrar numa turma do mesmo nível que já está no meio da etapa?
Opções: pode, como qualquer aluno · só numa turma que esteja começando a etapa
Resposta: **pode, como qualquer aluno.**

**9.3** Como é definido o valor da mensalidade?
Opções: por matéria · por nível · por turma · valor único
Resposta: **por matéria.**

**9.4** (R07) Como é o horário de uma turma?
Opções: dias e hora fixos na semana · cada aula com data própria
Resposta *(resposta livre)*: os horários são definidos pela diretoria. As aulas acontecem 1 ou 2 vezes por semana, e todas as aulas seguintes ficam sempre nos mesmos dias da semana e no mesmo horário.

Sugestão adicionada depois desta rodada: S06.

### Rodada 10: criação da turma e aulas perdidas

**10.1** Qual é o último momento em que o aluno ainda pode se matricular?
Opções: antes da 13ª aula · antes da 12ª aula
Resposta: **antes da 13ª aula.**

**10.2** Quem cria a turma e escolhe o horário?
Opções: o ADM cria e define tudo · o professor cria escolhendo de uma grade do ADM · o ADM cria e o professor escolhe o horário
Resposta: **o ADM cria a turma, escolhe o professor e fixa dias e horário.**

**10.3** (R07) O horário pode mudar quando a turma sobe de nível?
Opções: fixo para sempre · pode mudar na subida
Resposta: **fixo para sempre.**

**10.4** Uma aula não aconteceu (feriado, professor doente). O que acontece?
Opções: é reposta no fim, no mesmo horário · conta como dada · reposição em outro horário
Resposta: **é reposta no fim da etapa, no mesmo horário.**

Sugestão adicionada depois desta rodada: S07.

### Rodada 11: ciclo de vida da turma e vencimento

**11.1** Em que nível uma turma nova começa?
Opções: sempre no N1 · o ADM escolhe
Resposta: **o ADM escolhe.**

**11.2** (R09) A turma terminou o nível máximo. O que acontece com ela?
Opções: encerra · volta para o N1
Resposta: **encerra.**

**11.3** O ADM pode encerrar uma turma antes do fim?
Opções: não pode · pode, e os alunos mantêm as faltas · pode, e os alunos recomeçam
Resposta: **não pode.**

**11.4** Como funciona a cobrança da mensalidade no tempo?
Opções: no dia da matrícula · dia fixo do mês, com o primeiro mês proporcional · dia fixo, com o primeiro mês cheio
Resposta: **primeiro pagamento na matrícula, depois todo mês no mesmo dia.**

Sugestão adicionada depois desta rodada: S08.

### Rodada 12: saída da turma e início dos pacotes

**12.1** O aluno sai da turma por vontade própria no meio de um mês pago. E a mensalidade?
Opções: sem reembolso · reembolso proporcional
Resposta: **sem reembolso.**

**12.2** E se uma turma ficar sem nenhum aluno?
Opções: continua aberta · encerra sozinha
Resposta: **continua aberta.**

**12.3** (R13) Como medir quanto do pacote foi assistido (os vídeos são do YouTube)?
Opções: aulas concluídas sobre o total · tempo de vídeo assistido
Resposta *(resposta livre)*: mudar o reembolso; ele vale só até 7 dias depois da compra, sem a condição de menos de 30% assistido.

**12.4** (R15) Quem cria o pacote e o envia para revisão?
Opções: o professor cria e envia · só o ADM
Resposta: **o professor cria e envia; o ADM publica ou devolve.**

Sugestão adicionada depois desta rodada: S09.

### Rodada 13: reembolso, recompra e arquivamento

**13.1** (R13) Como contar os 7 dias do reembolso?
Opções: 7 × 24 h a partir da compra · até o fim do 7º dia
Resposta: **até o fim do 7º dia (23h59).**

**13.2** Depois de um reembolso, o aluno pode comprar o pacote de novo? E pedir reembolso outra vez?
Opções: recompra sem reembolso · recompra com reembolso · não pode recomprar
Resposta: **pode recomprar, mas sem direito a novo reembolso.**

**13.3** (R12) O aluno com acesso ativo compra o mesmo pacote de novo. O que acontece?
Opções: compra bloqueada · soma 12 meses · reinicia os 12 meses
Resposta: **compra bloqueada.**

**13.4** (R15) O pacote foi arquivado. E quem já comprou?
Opções: mantém o acesso · perde o acesso
Resposta: **mantém o acesso até o fim dos 12 meses.**

Sugestão adicionada depois desta rodada: S10.

### Rodada 14: edição de pacotes e certificados

**14.1** (R15) Um pacote publicado precisa de correção. O que o professor pode fazer?
Opções: a edição volta para revisão · não edita o publicado · edita direto
Resposta: **edita direto, sem revisão.**

**14.2** (R15) Um pacote arquivado pode voltar a ser publicado?
Opções: sim, pelo ADM · não, é definitivo
Resposta: **sim, pelo ADM.**

**14.3** (R16) Como funciona o simulado?
Opções: automático com tentativas ilimitadas · automático com tentativas limitadas · liberado só após 100%
Resposta *(resposta livre)*: prova de múltipla escolha na plataforma, com uma tentativa só.

**14.4** Além do certificado de pacote, existe certificado pela turma?
Opções: só de pacote · de pacote e de trilha · de pacote, de trilha e de nível
Resposta: **de pacote, de trilha e de nível.**

Sugestão adicionada depois desta rodada: S11.

### Rodada 15: simulado e preço

**15.1** (R16) Quando o simulado fica liberado?
Opções: só após concluir 100% das aulas · a qualquer momento
Resposta: **só após 100%.**

**15.2** (R16) O aluno tirou menos de 6 na tentativa única. Ainda tem caminho para o certificado?
Opções: nunca · nova compra dá nova chance · o ADM libera nova tentativa
Resposta: **o ADM pode liberar nova tentativa.**

**15.3** O professor adiciona uma aula a um pacote publicado. E quem já tinha 100%?
Opções: certificado emitido continua valendo · todos recalculam · a mudança só vale para novos compradores
Resposta: **certificado emitido continua valendo; para quem ainda não tem, a aula nova entra nos 100%.**

**15.4** Quem define o preço do pacote e quem pode mudá-lo?
Opções: o professor define e muda · o professor sugere e o ADM decide · só o ADM
Resposta: **só o ADM.**

Mudança nas sugestões depois desta rodada: S11 ajustada.

### Rodada 16: cupons

**16.1** (R14) Que tipo de desconto o cupom dá, e o que é o "desconto máximo"?
Opções: percentual com teto em reais · percentual ou valor fixo, com teto em reais · só percentual, com limite de percentual
Resposta: **só percentual, e o sistema recusa cupom acima de um percentual máximo.**

**16.2** (R14) Como se conta o limite de usos?
Opções: total · total e 1 por aluno · por aluno
Resposta: **limite total, e cada aluno usa o mesmo cupom uma vez.**

**16.3** Em que compras o cupom vale?
Opções: só pacotes · pacotes e primeira mensalidade · pacotes e mensalidades
Resposta: **só pacotes.**

**16.4** Uma compra com cupom foi reembolsada. O uso do cupom volta?
Opções: o uso é devolvido · o uso continua contado
Resposta: **o uso continua contado.**

Sugestão adicionada depois desta rodada: S12.

### Rodada 17: criação de cupons, nivelamento interrompido e correções

**17.1** (R14) Quem cria cupons e para quais pacotes eles valem?
Opções: o ADM, para todos os pacotes · o ADM, para pacotes escolhidos · o ADM e o professor (este só nos próprios pacotes)
Resposta: **só o ADM, e o cupom vale para todos os pacotes.**

**17.2** (R14) Qual é o percentual máximo de um cupom?
Opções: 50% · 70% · o ADM configura
Resposta: **50%.**

**17.3** O aluno fechou o navegador no meio do nivelamento. O que acontece?
Opções: retoma de onde parou · é corrigido com o que respondeu · recomeça do zero
Resposta: **retoma de onde parou.**

**17.4** (R10) O professor lançou presença ou nota errada. Quem corrige e até quando?
Opções: o professor até o fim da etapa · o professor a qualquer momento · só o ADM
Resposta: **o professor, a qualquer momento.** (Mudou na rodada 19.)

Sugestão adicionada depois desta rodada: S13.

### Rodada 18: correção tardia e poderes do ADM

**18.1** (R08) Uma correção feita depois que a turma subiu muda o resultado da R08. O que acontece com o nível?
Opções: ajusta nos dois sentidos · só para cima · o nível não muda
Resposta: **só para cima.**

**18.2** O professor nunca lança a nota pendente. E aí?
Opções: há um prazo e depois conta como reprovado · o ADM lança no lugar · sem prazo
Resposta: **o ADM lança no lugar.**

**18.3** (R10) O ADM pode lançar ou corrigir presença e nota em qualquer turma?
Opções: não, só o professor · sim, em qualquer turma
Resposta: **sim, em qualquer turma.**

**18.4** Existe limite de tempo para terminar o nivelamento?
Opções: sem limite · prazo para terminar · tempo de prova
Resposta *(resposta livre)*: tempo de prova, mas o ADM pode abrir exceções.

Sugestão adicionada depois desta rodada: S14.

### Rodada 19: aprovação tardia e detalhes do nivelamento

**19.1** O aluno reprovou, saiu da turma e talvez já esteja em outra do nível antigo. Depois, a nota é corrigida e ele passa a estar aprovado. O que acontece?
Opções: volta à turma original · volta se tiver vaga · sobe e procura outra turma
Resposta *(resposta livre)*: o professor tem até 72 horas para corrigir a nota. Depois disso, o aluno pode sair da turma e entrar em outra.

**19.2** Qual é o tempo de prova do nivelamento?
Opções: 30 min · 60 min · 90 min · o ADM define por matéria
Resposta: **60 minutos.**

**19.3** Que exceções o ADM pode abrir no nivelamento?
Opções: dar mais tempo · liberar que o aluno refaça · as duas
Resposta: **as duas.**

### Rodada 20: prazo de 72 horas

**20.1** As 72 horas para corrigir a nota contam a partir de quê?
Opções: do lançamento da nota · do fim da etapa
Resposta: **do lançamento da nota.**

**20.2** O prazo de 72 horas vale também para presenças?
Opções: sim, nota e presença · presença só até o fim da etapa · presença a qualquer momento
Resposta: **sim, nota e presença.**

**20.3** Passadas as 72 horas, alguém ainda pode corrigir a nota?
Opções: ninguém · o ADM, só para cima · o ADM, nos dois sentidos
Resposta: **o ADM, e só para cima.**

**20.4** Durante as 72 horas, o aluno reprovado continua na turma ocupando a vaga?
Opções: sim, fica e ocupa a vaga · a turma espera as 72 horas para subir
Resposta: **sim, fica e ocupa a vaga.**

Sugestões adicionadas depois desta rodada: S15, S16 e S17.

## Respostas que mudaram durante a entrevista

| Tema | Primeira resposta | Resposta final | Rodadas |
|---|---|---|---|
| Como sobe quem não está em turma | Teste avulso na plataforma, refeito após 30 dias | Não sobe sem turma. O "teste avulso" era o próprio nivelamento, feito uma vez por quem não tem nível. A R03 sai. | 4 → 8 |
| Teste avulso para quem está em turma | Pode fazer e, se passar, sai da turma | Em turma, só a prova final | 5 → 7 |
| Correção de nota e presença | O professor corrige a qualquer momento | O professor corrige até 72 horas depois do lançamento; depois, só o ADM e só para cima | 17 → 20 |

Regras de partida alteradas pela entrevista: R03 (removida), R08 (75% de frequência virou limite de 6 faltas em 24 aulas), R10 (o ADM também lança e corrige), R11 (habilitação só por matéria) e R13 (sem a condição de 30% assistido).

## O que a entrevista mostrou

- **Um nome mal combinado custou quatro rodadas.** O termo "teste avulso" foi criado pela IA na rodada 4 e foi entendido de jeitos diferentes até a rodada 8. É o argumento para fechar o glossário (CONTEXT.md) antes do código.
- **Regras que parecem completas escondem decisões.** "Frequência ≥ 75%" só ficou testável depois de definir como a turma funciona: etapa de 24 aulas, entrada até antes da 13ª aula e limite de 6 faltas.
- **Mudar uma regra mexe em outras.** Tirar o limite de 30% assistido do reembolso abriu a brecha de assistir ao pacote inteiro, tirar o certificado e pedir o dinheiro de volta, que a sugestão S09 fecha.
