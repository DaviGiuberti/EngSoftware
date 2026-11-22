-- 0014: compras de pacote, do módulo vendas (H15).
--
-- aluno_id e pacote_id apontam para os módulos identidade e catalogo, sem chave estrangeira
-- (ADR 0002). O valor é o preço do pacote no momento da compra, em centavos (R59), e o pagamento
-- é simulado (ADR 0003). O acesso vai até o mesmo dia, 12 meses depois (R12, R60), e é calculado
-- da data da compra, sem coluna própria. comprada_em é texto ISO 8601, no horário de Brasília.
CREATE TABLE compra (
    id INTEGER PRIMARY KEY,
    aluno_id INTEGER NOT NULL,
    pacote_id INTEGER NOT NULL,
    valor_em_centavos INTEGER NOT NULL CHECK (valor_em_centavos > 0),
    comprada_em TEXT NOT NULL
);

CREATE INDEX compra_por_aluno ON compra (aluno_id, pacote_id);
