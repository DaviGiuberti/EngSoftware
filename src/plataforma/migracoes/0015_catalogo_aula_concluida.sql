-- 0015: aulas gravadas concluídas, do módulo catalogo (H16).
--
-- A aula é a do pacote com aquele número, que não muda depois de publicado (R58). A marcação não é
-- desfeita (R62), então cada aula é concluída uma vez por aluno, e concluida_em é a atividade de
-- estudo que as métricas contam. aluno_id aponta para o módulo identidade, sem chave estrangeira
-- (ADR 0002). concluida_em é texto ISO 8601, no horário de Brasília.
CREATE TABLE aula_concluida (
    aluno_id INTEGER NOT NULL,
    pacote_id INTEGER NOT NULL,
    numero INTEGER NOT NULL,
    concluida_em TEXT NOT NULL,
    PRIMARY KEY (aluno_id, pacote_id, numero),
    FOREIGN KEY (pacote_id, numero) REFERENCES aula_gravada (pacote_id, numero)
);
