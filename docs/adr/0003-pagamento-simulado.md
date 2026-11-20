# ADR 0003 — Pagamento simulado
Data: 2026-11-20
Status: Aceito

## Contexto
O aluno paga a turma por mensalidade (R27, R28) e compra pacotes gravados, com direito a reembolso (R12, R13). O MVP tem 4 dias de trabalho e uma pessoa, e pelo YAGNI só entra o que tiver evidência de que é necessário. É preciso decidir como o sistema recebe esses pagamentos.

## Decisão
O pagamento é simulado, tanto na mensalidade quanto na compra de pacote. Não há gateway de pagamento no MVP.

- O pagamento conta como feito no momento em que o aluno paga, como nos critérios da H07 (mensalidade) e da H15 (compra).
- O reembolso (R13) também é simulado: o sistema registra a devolução, mas nenhum dinheiro sai de verdade.

## Consequências
- Não há conta em serviço de pagamento, chave secreta a mais nem dado de cartão para proteger.
- Os testes não dependem de serviço externo e dão sempre o mesmo resultado.
- O sistema não trata falhas reais de pagamento, como cartão recusado, pagamento pendente ou estorno.
