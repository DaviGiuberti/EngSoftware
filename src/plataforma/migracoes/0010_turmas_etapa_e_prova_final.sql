-- 0010: etapas, encerramento da turma, notas da prova final e correções, do módulo turmas (H23,
-- H09, H10, H11, H24, H32).
--
-- No fim da 24ª aula, a turma passa para a etapa do nível seguinte (R04, R17), e cada etapa
-- ganha uma linha em etapa, com o início da 1ª aula (R43). A etapa atual é a de maior nível. Por
-- isso, turma.nivel e turma.inicio_da_etapa ficam como a turma foi criada: o nível inicial e o
-- início da 1ª etapa. As turmas que já existem começam com a etapa que têm hoje. Datas e horas
-- são texto ISO 8601, no horário de Brasília.
CREATE TABLE etapa (
    turma_id INTEGER NOT NULL REFERENCES turma (id),
    nivel INTEGER NOT NULL CHECK (nivel >= 1),
    inicio TEXT NOT NULL,
    PRIMARY KEY (turma_id, nivel)
);

INSERT INTO etapa (turma_id, nivel, inicio) SELECT id, nivel, inicio_da_etapa FROM turma;

-- O fim da etapa do nível máximo, quando a turma encerra (R09). Ninguém a encerra antes (R25).
ALTER TABLE turma ADD COLUMN encerrada_em TEXT;

-- A nota de cada aluno na prova final da etapa, em décimos: 6,5 é 65 (R51). As 72 horas de
-- correção contam de lancada_em, que a correção não muda (R22). resultado_aplicado é o resultado
-- que já passou a valer, com a promoção ou a saída da turma feitas (R49); antes, fica NULL.
-- aluno_id e lancada_por apontam para o módulo identidade, sem chave estrangeira (ADR 0002).
CREATE TABLE prova_final (
    turma_id INTEGER NOT NULL,
    nivel INTEGER NOT NULL,
    aluno_id INTEGER NOT NULL,
    nota_em_decimos INTEGER NOT NULL CHECK (nota_em_decimos BETWEEN 0 AND 100),
    lancada_em TEXT NOT NULL,
    lancada_por INTEGER NOT NULL,
    corrigida_em TEXT,
    corrigida_por INTEGER,
    resultado_aplicado TEXT CHECK (resultado_aplicado IN ('aprovado', 'reprovado')),
    PRIMARY KEY (turma_id, nivel, aluno_id),
    FOREIGN KEY (turma_id, nivel) REFERENCES etapa (turma_id, nivel)
);

-- A última correção da presença de cada aula (R22). As 72 horas contam de lancada_em.
ALTER TABLE lancamento_de_presenca ADD COLUMN corrigida_em TEXT;
ALTER TABLE lancamento_de_presenca ADD COLUMN corrigida_por INTEGER;
