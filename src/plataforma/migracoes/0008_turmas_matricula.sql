-- 0008: matrículas, mensalidades pagas e listas de espera, do módulo turmas (H04, H05, H06, H13).
--
-- aluno_id aponta para o módulo identidade, sem chave estrangeira (ADR 0002). Datas e horas são
-- texto ISO 8601, no horário de Brasília; o vencimento é só a data.
CREATE TABLE matricula (
    id INTEGER PRIMARY KEY,
    turma_id INTEGER NOT NULL REFERENCES turma (id),
    aluno_id INTEGER NOT NULL,
    matriculada_em TEXT NOT NULL,
    -- Preenchido quando o aluno sai da turma. A matrícula continua guardada, sem reembolso (R29).
    saiu_em TEXT
);

-- No máximo uma matrícula ativa do aluno em cada turma. A regra de uma turma por matéria (R44)
-- fica no caso de uso, porque a matéria está na turma.
CREATE UNIQUE INDEX uma_matricula_ativa_por_turma
    ON matricula (turma_id, aluno_id) WHERE saiu_em IS NULL;

CREATE INDEX matricula_por_aluno ON matricula (aluno_id);

-- As mensalidades pagas da matrícula (R27). O pagamento é simulado (ADR 0003).
CREATE TABLE mensalidade (
    matricula_id INTEGER NOT NULL REFERENCES matricula (id),
    vencimento TEXT NOT NULL,
    valor_em_centavos INTEGER NOT NULL CHECK (valor_em_centavos > 0),
    paga_em TEXT NOT NULL,
    PRIMARY KEY (matricula_id, vencimento)
);

-- A lista de espera de cada turma, na ordem de entrada (R05). prazo é até quando o aluno pode
-- confirmar a vaga que recebeu; sem oferta de vaga, fica NULL.
CREATE TABLE lista_de_espera (
    turma_id INTEGER NOT NULL REFERENCES turma (id),
    aluno_id INTEGER NOT NULL,
    entrou_em TEXT NOT NULL,
    prazo TEXT,
    PRIMARY KEY (turma_id, aluno_id)
);

CREATE INDEX lista_de_espera_por_aluno ON lista_de_espera (aluno_id);
