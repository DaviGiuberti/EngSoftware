# Regras de negócio

Regras decididas pelo autor: a lista original, as respostas da entrevista de 16/11/2026, registrada em [ia/grill-me-regras.md](ia/grill-me-regras.md), e as regras a partir da R34, que surgiram ao escrever os critérios das [histórias](historias.md) e ao começar a implementá-las. Entre parênteses, a pergunta da entrevista ou a história que originou ou mudou a regra.

Os números não mudam: uma regra alterada mantém o número, e as regras novas começam na R17. Regras marcadas com **[Fora do MVP]** ficam documentadas, mas não entram na entrega de 02/12/2026.

## Usuários e perfis

R39
Cada e-mail tem uma única conta na plataforma, com um único perfil. O cadastro recusa um e-mail que já está em uso, sem diferenciar maiúsculas de minúsculas. (H38)

## Matérias, níveis e nivelamento

R01
O nível do aluno é separado por matéria. Cada matéria define quantos níveis tem. (4.4)

R02
A nota do nivelamento define o nível inicial por faixas que o ADM cadastra para cada matéria (por exemplo, 0–39% → N1, 40–69% → N2, 70–100% → N3). (5.2)

R40
Cada nível da matéria tem uma faixa do nivelamento, e as faixas cobrem de 0% a 100% sem buraco nem sobreposição. A faixa do N1 começa em 0%. Para cada nível seguinte, o ADM define a nota mínima, de 1% a 100% e maior que a do nível anterior. Cada faixa vai até 1 ponto abaixo da nota mínima do nível seguinte, e a do nível máximo vai até 100%. (H27)

R41
Cada questão do nivelamento tem exatamente 5 alternativas, de A a E, e só uma delas é a correta. (H28)

R03 *(alterada)*
O nivelamento é feito uma única vez por matéria, só por quem ainda não tem nível nela. Não existe mais a espera de 30 dias para refazer; só o ADM pode liberar que o aluno refaça (R30). (3.3, 8.1)

R30
O nivelamento tem 60 minutos de prova, e o tempo só corre com o teste aberto. Se o aluno fechar o navegador ou a conexão cair, ele retoma de onde parou. O ADM pode dar mais tempo a um aluno ou liberar que ele refaça. (17.3, 18.4, 19.2, 19.3)

R42
Quando o ADM libera e o aluno refaz o nivelamento, o nível só muda se o resultado novo for maior. Se for igual ou menor, o aluno continua no nível que tinha. (H33)

R34
A nota do nivelamento é a porcentagem de acertos sobre o total de questões, arredondada para baixo (39,9% vira 39%). Questão sem resposta conta como erro. Quando os 60 minutos acabam, o teste é encerrado e corrigido com o que foi respondido. (H01)

R31
Quem só quer pacotes gravados não precisa fazer o nivelamento. Qualquer aluno compra pacote de qualquer nível. (4.2)

## Turmas

R04 *(alterada)*
Cada turma tem matéria, nível atual, professor, dias e horário fixos (1 ou 2 aulas por semana) e no máximo 12 vagas. A turma é contínua: avança de nível junto, uma etapa por nível. (1.1, 9.4)

R24
O ADM cria a turma e escolhe matéria, nível inicial (qualquer nível da matéria), professor, dias e horário. O horário não muda durante toda a vida da turma. (10.2, 10.3, 11.1)

R25
Uma turma aberta não pode ser encerrada antes de concluir o nível máximo, nem se ficar sem alunos. (11.3, 12.2)

R26 *(alterada)*
O professor acompanha a turma quando ela passa de nível. O ADM pode trocar o professor da turma quando quiser, sem precisar de motivo; o novo professor precisa estar habilitado na matéria (R11) e não ter outra turma num horário que se sobreponha (R07). (1.1, H31)

R11 *(alterada)*
O ADM habilita o professor por matéria. Habilitado numa matéria, ele pode dar aula em todos os níveis dela. (2.4, 3.4)

R05 *(alterada)*
Turma cheia: o aluno entra numa lista de espera. Quando abre uma vaga, o primeiro da fila tem 72 horas para confirmar; se não confirmar, a vaga passa para o próximo. (6.3, 8.3)

R35
Quem não confirma a vaga dentro das 72 horas sai da lista de espera. (H06)

R47
Confirmar a vaga da lista de espera é se matricular: o aluno paga a primeira mensalidade (R27), e valem as mesmas regras da matrícula (R06, R07, R19, R44). (H06)

R45
A partir da 13ª aula da etapa, a lista de espera da turma não recebe ninguém novo, e a vaga que abre não é oferecida, porque ninguém poderia mais se matricular (R19). (H05, H06)

R50
No fim da etapa, a lista de espera da turma é esvaziada. Quem está nela é do nível da etapa que terminou (R06) e procura outra turma desse nível. Se a turma passa para o nível seguinte, a etapa nova começa com a lista vazia. (H10)

R06
O aluno só se matricula em turma do seu nível naquela matéria.

R44
O aluno tem no máximo uma turma em cada matéria. Ele pode estar na lista de espera de várias turmas de uma matéria em que ainda não tem turma; ao se matricular numa turma, sai das listas de espera das outras turmas da mesma matéria. (H04, H05)

R07 *(alterada)*
Nem o aluno nem o professor podem ter duas turmas com horários que se sobrepõem no mesmo dia da semana. (9.4)

R19
O aluno só pode se matricular até antes da 13ª aula da etapa, para fazer no mínimo 12 aulas. (9.1, 10.1)

## Etapa, prova final e subida de nível

R17
Toda etapa tem 24 aulas, em todos os níveis e matérias. A etapa termina depois da 24ª aula, com a prova final. (2.1, 3.1, 4.3)

R18
Aula que não acontece (feriado, professor doente) não conta nas 24: ela é reposta no fim da etapa, no mesmo horário. (10.4)

R43
A 1ª aula da turma é no primeiro dia dela depois da criação, no horário da turma. As aulas seguintes caem nos dias e no horário da turma, uma depois da outra, pulando as não realizadas (R18). A aula conta como dada quando começa, se não foi marcada como não realizada, e só a aula que já começou recebe presença. (H30, H22)

R48
O professor pode marcar como não realizada qualquer aula da etapa que ainda não tem presença lançada, passada ou futura. A aula com presença aconteceu e não pode ser marcada. A marcação é definitiva. (H22)

R08 *(alterada)*
Ao fim da etapa, o aluno sobe 1 nível se tiver no máximo 6 faltas (25% das 24 aulas) e nota ≥ 7 na prova final. As faltas contam só a partir da entrada do aluno na turma; as aulas anteriores contam como presença. (2.3, 3.2, 4.3)

R32
Só se sobe de nível pela turma (R08). Não existe outro teste para subir de nível. (7.3, 8.1, 8.2)

R09
Nunca se pula nível. Ao concluir o nível máximo, a trilha da matéria está concluída e a turma encerra. (11.2)

R20
A prova final é aplicada pelo professor fora da plataforma, e ele lança a nota. Se o aluno faltar à prova, o professor decide o que fazer; o sistema não impõe regra. (4.1, 5.4)

R51
A nota da prova final vai de 0 a 10, com uma casa decimal, como 6,5. (H23)

R21
Quando a turma sobe, quem não cumpriu a R08 sai dela e procura sozinho outra turma do mesmo nível, onde recomeça o nível. Ele pode entrar no meio de uma etapa, como qualquer aluno (R19). (2.2, 8.2, 9.2)

R10 *(alterada)*
O professor lança presença e nota só nas próprias turmas. O ADM pode lançar e corrigir presença e nota em qualquer turma. (18.3)

R22
O professor pode corrigir uma presença ou nota até 72 horas depois de lançá-la. Depois disso, só o ADM corrige, e só para cima: se a correção aprova o aluno, ele sobe; se reprova quem já subiu, o nível não muda. (17.4, 18.1, 20.1, 20.2, 20.3)

R52
Quando a correção do ADM, depois das 72 horas, aprova um aluno que já saiu da turma por reprovação, ele sobe de nível, mas não volta para a turma: procura uma turma do nível novo. Se já tiver entrado noutra turma do nível anterior, continua nela. (H32)

R23
O aluno reprovado continua na turma, ocupando a vaga, durante as 72 horas de correção da nota; se a nota não mudar, ele sai. O aluno cuja nota ainda não foi lançada também continua na turma ocupando a vaga, até a nota sair. Se o professor não lançar, o ADM lança no lugar dele. (6.2, 8.4, 18.2, 20.4)

R49
O resultado da etapa de cada aluno (R08) passa a valer quando terminam as 72 horas de correção da nota da prova final, contadas do lançamento (R22). Nesse momento, o aprovado é promovido e o reprovado sai da turma (R21, R23). Como a promoção só acontece depois do prazo, a correção feita dentro dele não desfaz nada. (H09, H24)

R33
Certificado de nível: emitido quando o aluno sobe de nível pela R08. Certificado de trilha: emitido quando ele conclui o nível máximo da matéria. (14.4)

R36
Ao ser aprovado no nível máximo, o aluno recebe o certificado de nível desse nível e o certificado de trilha. (H12)

## Mensalidade

R27
A turma é paga por mensalidade, com valor definido por matéria. A primeira mensalidade é paga na matrícula, e as seguintes vencem todo mês no dia da matrícula. (5.1, 9.3, 11.4)

R46
Quando o mês não tem o dia da matrícula, a mensalidade daquele mês vence no último dia dele: quem se matricula em 31/01 tem os vencimentos seguintes em 28/02 e 31/03. (H04, H07)

R28
Com a mensalidade atrasada, o aluno tem 7 dias de tolerância; depois disso, perde a vaga. (6.1, 7.4)

R37
A tolerância da mensalidade vai até as 23h59 do 7º dia depois do vencimento. Na virada para o 8º dia, o aluno perde a vaga. (H07)

R53
A mensalidade seguinte fica em aberto quando a anterior vence, e só ela pode ser paga: quem se matriculou em 10/03 paga a de 10/04 de 10/03 até as 23h59 de 17/04, e a de 10/05 só a partir de 10/04. (H07)

R54
Depois que a turma encerra (R09), nenhuma mensalidade vence. A que venceu antes do encerramento continua valendo, com a tolerância (R28). (H07)

R55
Quem perde a vaga por atraso da mensalidade vê um aviso na aba Turmas até entrar em outra turma da matéria. (H07)

R29
Quem sai da turma por vontade própria não recebe reembolso da mensalidade. (12.1)

## Pacotes gravados

R15 *(alterada)*
O pacote passa por rascunho → em revisão → publicado → arquivado. O professor cria o pacote e envia para revisão; o ADM publica ou devolve. Só o ADM define e altera o preço. O professor edita o pacote publicado direto, sem nova revisão. O ADM pode publicar de novo um pacote arquivado. (12.4, 14.1, 14.2, 15.4)

R38
Quando o ADM devolve um pacote em revisão, ele volta para rascunho, e o professor pode editá-lo e enviá-lo de novo. (H34)

R56
O professor só cria pacote de uma matéria em que está habilitado (R11), num dos níveis dela. A matéria e o nível do pacote não mudam depois de criado, e só o professor que criou o pacote o edita. (H25)

R57
O pacote só vai para revisão com pelo menos 1 aula. O professor edita o pacote em rascunho e o publicado (R15); em revisão, ele espera o ADM publicar ou devolver, e o arquivado não é editado. (H25, H26, H35)

R58
Cada aula gravada tem um título e o link de um vídeo do YouTube (youtube.com/watch?v=… ou youtu.be/…); outro link é recusado. No rascunho, o professor adiciona, corrige e remove aulas. No pacote publicado, ele adiciona e corrige aulas e muda o título, mas não remove nenhuma aula, porque quem comprou a perderia. (H26)

R59
O ADM define o preço do pacote, maior que zero, ao publicá-lo, e pode mudá-lo depois, no publicado ou no arquivado. A mudança vale para as compras seguintes. Publicado de novo, o pacote arquivado volta com o preço que tinha. (H34, H35)

R12 *(alterada)*
A compra de um pacote libera o acesso por 12 meses. Com acesso ativo, o aluno não pode comprar o mesmo pacote de novo. Se o pacote for arquivado, quem comprou mantém o acesso até o fim dos 12 meses. (13.3, 13.4)

R60
O acesso do pacote vale até as 23h59 do dia da compra, 12 meses depois; na virada para o dia seguinte, ele vence. Quando o mês não tem o dia da compra, vale até o último dia dele: quem compra em 29/02/2028 tem acesso até 28/02/2029. (H15)

R61
O aluno assiste à aula gravada no navegador, pelo link do YouTube, e só com o acesso ativo ao pacote (R12). (H16)

R62 *(alterada)*
Com o acesso ativo, o aluno marca a aula gravada como concluída. A marcação fica guardada com a data, o aluno não a desfaz, e marcar de novo a mesma aula é recusado. Só o reembolso do pacote apaga as aulas concluídas dele (R63). (H16, H17)

R63
O reembolso aceito encerra o acesso ao pacote na hora, apaga as aulas que o aluno concluiu nele e tira o pacote de "Meus pacotes". O aluno pode comprá-lo de novo na vitrine, e essa compra não dá direito a reembolso (R13). (H17)

R13 *(alterada)*
O reembolso de pacote só pode ser pedido até as 23h59 do 7º dia depois da compra, sem nenhuma condição sobre quanto foi assistido. Quem foi reembolsado pode comprar o mesmo pacote de novo, mas essa nova compra não dá direito a reembolso. (12.3, 13.1, 13.2)

R14 *(alterada)* **[Fora do MVP]**
O cupom dá desconto só percentual, de no máximo 50%. Tem validade, limite total de usos e 1 uso por aluno, e não acumula com outro cupom. Vale só para pacotes, em qualquer pacote. Só o ADM cria cupons. Se a compra for reembolsada, o uso do cupom continua contado. (16.1–16.4, 17.1, 17.2)

R16 *(alterada)* **[Fora do MVP]**
O certificado de pacote exige 100% das aulas concluídas e nota ≥ 6 no simulado. O simulado é de múltipla escolha, feito na plataforma, liberado só depois de 100% das aulas, com uma única tentativa; o ADM pode liberar nova tentativa. Se o professor adicionar uma aula ao pacote, o certificado já emitido continua valendo, e para quem ainda não tem certificado a aula nova passa a contar nos 100%. (14.3, 15.1–15.3)
