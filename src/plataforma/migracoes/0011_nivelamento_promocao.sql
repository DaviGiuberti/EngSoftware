-- 0011: promoções e trilhas concluídas, do módulo nivelamento (H09, H32, H03).
--
-- Aprovado na etapa, o aluno sobe exatamente um nível (R08, R09), e a promoção fica guardada com a
-- data, que a M1 e os certificados de nível (R33) usam. A aprovação no nível máximo conclui a
-- trilha da matéria (R09). aluno_id e materia_id apontam para os módulos identidade e materias,
-- sem chave estrangeira (ADR 0002). Datas e horas são texto ISO 8601, no horário de Brasília.
CREATE TABLE promocao (
    aluno_id INTEGER NOT NULL,
    materia_id INTEGER NOT NULL,
    nivel_anterior INTEGER NOT NULL CHECK (nivel_anterior >= 1),
    nivel_novo INTEGER NOT NULL CHECK (nivel_novo = nivel_anterior + 1),
    promovido_em TEXT NOT NULL,
    PRIMARY KEY (aluno_id, materia_id, nivel_novo)
);

CREATE TABLE trilha_concluida (
    aluno_id INTEGER NOT NULL,
    materia_id INTEGER NOT NULL,
    concluida_em TEXT NOT NULL,
    PRIMARY KEY (aluno_id, materia_id)
);
