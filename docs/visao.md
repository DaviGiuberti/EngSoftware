# Visão do produto

Plataforma de ensino por níveis. Projeto final de Engenharia de Software (UNIFESP).

Equipe: 1 pessoa · Entrega: 02/12/2026 · Atualizado em 21/11/2026

## 1. Problema

> Alunos que querem aprender um assunto não sabem em que nível estão e estudam sem uma trilha clara, então escolhem conteúdo fácil ou difícil demais, não percebem o próprio progresso e acabam desistindo.

O problema é do **aluno**. Professor e ADM são os perfis que fazem a solução funcionar, mas as métricas de sucesso medem o que muda para o aluno.

## 2. Como a plataforma resolve

1. Em cada matéria, o aluno faz um **teste de nivelamento** uma única vez e recebe um **nível** inicial.
2. Ele estuda por dois caminhos:
   - **turmas** com aulas ao vivo do seu nível, com professor. A turma avança de nível junto, numa **etapa** de 24 aulas por nível;
   - **pacotes de aulas gravadas**, que podem ser comprados em qualquer nível, com destaque para os do nível do aluno. Quem só quer pacotes não precisa fazer o nivelamento.
3. Ele **sobe um nível por vez**, no fim da etapa, se tiver no máximo 6 faltas e nota ≥ 7 na prova final. As regras completas estão em [regras.md](regras.md).

**Hipótese:** se o aluno começar no nível certo e avançar um nível por vez, ele progride e continua estudando. As métricas da seção 4 servem para testar essa hipótese.

## 3. Perfis

| Perfil | O que faz no MVP |
|---|---|
| Aluno | Faz o nivelamento de cada matéria em que quer turma, se matricula numa turma do seu nível, paga a mensalidade, compra pacotes gravados de qualquer nível, pede reembolso e acompanha o próprio nível. |
| Professor | Dá aula nas turmas que o ADM atribui a ele, lança presenças e a nota da prova final, cria pacotes gravados e os envia para revisão. |
| ADM | Cadastra matérias, níveis, faixas e questões do nivelamento. Cadastra e habilita professores. Cria turmas. Revisa, define o preço e publica pacotes. Vê as métricas. |

## 4. Métricas de outcome

Output é o que a equipe fez: pacotes cadastrados, turmas criadas, testes aplicados, vendas. Outcome é o que mudou para o aluno. Os números de output mostram que a plataforma é usada, não que o problema foi resolvido. As três métricas abaixo são de outcome, e cada uma corresponde a uma parte da frase do problema.

| # | Métrica | Parte do problema | Meta inicial (hipótese a calibrar) |
|---|---|---|---|
| M1 | Taxa de progressão | "não percebem o próprio progresso" | 30% ou mais em 6 meses |
| M2 | Continuidade na trilha | "acabam desistindo" | 50% ou mais na 4ª semana |
| M3 | Tempo até estudar no nível certo | "não sabem em que nível estão" | mediana de até 3 dias |

### M1. Taxa de progressão (métrica principal)

- **O que mostra:** a trilha leva o aluno a progredir de verdade.
- **Como o sistema calcula:** pega os alunos que concluíram o nivelamento num período e calcula quantos por cento deles subiram pelo menos um nível em até 6 meses depois do nivelamento.
- **Por que 6 meses:** uma etapa tem 24 aulas, dadas 1 ou 2 vezes por semana, então leva de 12 a 24 semanas.
- **Cuidado:** deve ser lida junto com a M2. Um aluno que sobe de nível e some logo depois não é sucesso.

### M2. Continuidade na trilha

- **O que mostra:** o aluno não desistiu.
- **Como o sistema calcula:** pega os alunos que fizeram o nivelamento há pelo menos 4 semanas e calcula quantos por cento tiveram alguma atividade de estudo na 4ª semana depois do nivelamento. Conta como atividade de estudo uma presença em aula da turma ou uma aula gravada concluída.

### M3. Tempo até estudar no nível certo

- **O que mostra:** o aluno deixou de estar perdido e foi direto do nivelamento para conteúdo do seu nível.
- **Como o sistema calcula:** para cada aluno, conta os dias entre a conclusão do nivelamento e a primeira atividade de estudo no nível que recebeu, seja uma presença numa turma desse nível ou uma aula gravada concluída de um pacote desse nível. A métrica é a mediana desses tempos.

### De onde vêm os dados

As três métricas usam só registros que o sistema já precisa guardar para funcionar: data e resultado do nivelamento, presenças, aulas gravadas concluídas e subidas de nível com data. Não há coleta extra nem ferramenta de analytics.

### Como medir até a entrega

- **M1 e M2** precisam de meses e semanas de uso. Até 02/12 elas serão demonstradas com dados de exemplo que cobrem casos conhecidos, e os testes automatizados conferem se o cálculo está certo.
- **M3** cabe num piloto curto: 3 a 5 colegas fazem o nivelamento e uma atividade de estudo na semana da apresentação.

### O que fazer com o resultado

Medir só vale se o resultado mudar o próximo passo (construir → medir → aprender). Cada resultado abaixo da meta aponta para uma nova hipótese, que entra no backlog.

| Resultado | Leitura provável | Próximo passo |
|---|---|---|
| M3 alta: o aluno demora para começar | Falta turma do nível com vaga, ou o aluno não acha o conteúdo | Mostrar turmas e pacotes do nível logo depois do nivelamento, ou abrir mais turmas no nível |
| M2 baixa: o aluno some | Ele não volta à plataforma | Investigar em que ponto ele para. Lembretes, hoje fora do MVP, só entram com essa evidência |
| M1 baixa com M2 alta: o aluno estuda mas não sobe | Regra de subida difícil demais ou faixas do nivelamento que colocam o aluno acima do nível real | Revisar a R08 ou as faixas do nivelamento |
| M1 alta com M2 baixa: o aluno sobe e some | Subida fácil demais, sem aprendizado real | Revisar a R08 |

## 5. Escopo do MVP

**Premissas:** 4 dias de trabalho, 1 pessoa, uso de IA liberado. A disciplina avalia também o processo (testes, CI, pull requests, histórico no GitHub, documentação), então parte desses dias fica reservada para isso. As duas frentes entram no MVP, turmas e pacotes gravados. A entrevista de regras de 16/11 aumentou o escopo, e esta seção já está de acordo com o [regras.md](regras.md).

### Entra no MVP

| Funcionalidade | Versão do MVP |
|---|---|
| Cadastro e login | E-mail e senha. O aluno se cadastra sozinho. O primeiro ADM é criado na primeira vez que o app abre, sem senha padrão, e cadastra os professores. |
| Matérias e níveis | O ADM cadastra matérias, quantos níveis cada uma tem e as faixas de nota do nivelamento (R01, R02). |
| Teste de nivelamento | Um teste de múltipla escolha por matéria, feito uma vez, com 60 minutos e retomada de onde parou. A correção é automática e define o nível inicial (R03, R30). |
| Turmas | O ADM cria a turma com matéria, nível inicial, professor, dias e horário fixos e 12 vagas. O aluno se matricula só no seu nível, sem conflito de horário e até antes da 13ª aula da etapa (R04, R06, R07, R19, R24). |
| Lista de espera | Turma cheia gera fila. Quando abre vaga, o primeiro tem 72 horas para confirmar (R05). |
| Presença e prova final | O professor lança as presenças e a nota da prova final, que é aplicada fora da plataforma, e pode corrigir até 72 horas depois. O ADM lança e corrige em qualquer turma (R10, R20, R22, R23). |
| Subida de nível | No fim da etapa de 24 aulas, sobe um nível quem tem no máximo 6 faltas e nota ≥ 7. Quem não cumpre sai da turma e recomeça o nível (R08, R17, R21). |
| Certificados de nível e de trilha | Emitidos automaticamente quando o aluno sobe de nível e quando conclui o nível máximo (R33). |
| Mensalidade | Pagamento simulado. A primeira é paga na matrícula, e as seguintes vencem todo mês no mesmo dia, com 7 dias de tolerância antes de o aluno perder a vaga (R27, R28). |
| Pacotes de aulas gravadas | O professor cria e envia para revisão; o ADM define o preço e publica. Vídeos incorporados (YouTube não listado). Qualquer aluno compra pacote de qualquer nível (R15, R31). |
| Compra e reembolso | Compra simulada, que libera 12 meses de acesso. Reembolso até as 23h59 do 7º dia depois da compra (R12, R13). |
| Aula gravada concluída | O aluno marca a aula como concluída. Esse registro alimenta as métricas. |
| Métricas | Uma tela simples do ADM com M1, M2 e M3 do período. |

### Fica fora do MVP

Pelo YAGNI, estes itens só entram quando houver evidência de que são necessários.

| Fica fora | O que o MVP usa no lugar |
|---|---|
| Pagamento real | Pagamento simulado, para pacotes e mensalidades. |
| Cupons (R14) | Nada. A regra fica documentada para depois. |
| Certificado de pacote e simulado (R16) | Nada. A regra fica documentada; os certificados de nível e de trilha entram. |
| Upload e hospedagem de vídeos | Vídeo incorporado por link. |
| Videochamada dentro da plataforma | Link externo do Google Meet. |
| Teste adaptativo e sorteio de questões | Um teste fixo por matéria. |
| Vários fusos horários | Tudo no horário de Brasília. |
| Notificações por e-mail ou WhatsApp | Avisos dentro da plataforma, como o de vaga liberada na lista de espera. |
| Chat, fórum, comentários, avaliação de cursos | Nada. |
| Repasse financeiro e relatórios de vendas para professores | Nada. |
| Recuperação de senha e login social | Nada. |
| App mobile e site | Aplicativo para computador (Windows) ([ADR 0001](adr/0001-stack.md)). |
| Vários computadores com os mesmos dados | Um computador só: aluno, professor e ADM fazem login no mesmo app. |
| Dashboard com gráficos | Os três números na tela do ADM. |

### Ordem de entrega

Cada fatia funciona da tela ao banco antes de a próxima começar. A ordem segue valor e aprendizado: o nivelamento vem primeiro porque é o centro da hipótese, e a tela de métricas fecha o ciclo para medir.

| Dia | Fatia |
|---|---|
| 1 | Base do projeto (repositório, CI, estrutura), cadastro de matérias, níveis e faixas, e o nivelamento: o aluno faz o teste e vê o seu nível. |
| 2 | Turmas: o ADM cria a turma, o aluno se matricula (nível, horário, limite da 13ª aula) ou entra na lista de espera, e o professor lança presença. |
| 3 | Prova final, subida de nível com o prazo de correção de 72 horas, certificados de nível e de trilha, e mensalidade simulada. |
| 4 | Pacotes (revisão, publicação, compra, reembolso e aula concluída), tela de métricas, README, release do executável e ensaio da apresentação. |

Com as regras da entrevista, o plano ficou mais apertado. Se o prazo apertar, simplifica a tela, não a regra: as regras ficam no núcleo, com testes, e partes como lista de espera e mensalidade ganham uma interface mínima. Nenhuma das duas frentes sai do MVP.

## 6. Pendências

- **Matérias da demonstração:** o sistema aceita várias matérias cadastradas pelo ADM; falta escolher quais aparecem na apresentação.
- **Piloto da M3:** confirmar se haverá colegas para participar.
