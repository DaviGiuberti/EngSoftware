-- 0009: aulas não realizadas e presenças, do módulo turmas (H21, H22, H08).
--
-- A etapa é a da turma no nível dela, então turma_id e nivel juntos dizem a etapa (R04). As
-- aulas são guardadas pela data, e não pelo número: marcar uma aula como não realizada muda o
-- número das aulas seguintes (R18), mas não a data delas. Datas e horas são texto ISO 8601, no
-- horário de Brasília.
CREATE TABLE aula_nao_realizada (
    turma_id INTEGER NOT NULL REFERENCES turma (id),
    nivel INTEGER NOT NULL,
    data TEXT NOT NULL,
    marcada_em TEXT NOT NULL,
    PRIMARY KEY (turma_id, nivel, data)
);

-- Uma linha por aula com a presença lançada, mesmo que a turma não tivesse alunos nela.
-- lancada_em e lancada_por servem à correção em até 72 horas (R22).
CREATE TABLE lancamento_de_presenca (
    turma_id INTEGER NOT NULL REFERENCES turma (id),
    nivel INTEGER NOT NULL,
    data_da_aula TEXT NOT NULL,
    lancada_em TEXT NOT NULL,
    lancada_por INTEGER NOT NULL,
    PRIMARY KEY (turma_id, nivel, data_da_aula)
);

-- aluno_id aponta para o módulo identidade, sem chave estrangeira (ADR 0002).
CREATE TABLE presenca (
    turma_id INTEGER NOT NULL,
    nivel INTEGER NOT NULL,
    data_da_aula TEXT NOT NULL,
    aluno_id INTEGER NOT NULL,
    presente INTEGER NOT NULL CHECK (presente IN (0, 1)),
    PRIMARY KEY (turma_id, nivel, data_da_aula, aluno_id),
    FOREIGN KEY (turma_id, nivel, data_da_aula)
        REFERENCES lancamento_de_presenca (turma_id, nivel, data_da_aula)
);
