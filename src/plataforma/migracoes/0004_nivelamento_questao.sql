-- 0004: questões do nivelamento e as alternativas delas, do módulo nivelamento (H28).
--
-- questao.materia_id aponta para uma matéria do módulo materias, sem chave estrangeira: cada
-- módulo cuida das próprias tabelas (ADR 0002), e o caso de uso confere a matéria pela
-- consulta pública do materias.
CREATE TABLE questao (
    id INTEGER PRIMARY KEY,
    materia_id INTEGER NOT NULL,
    enunciado TEXT NOT NULL
);

CREATE INDEX questao_por_materia ON questao (materia_id);

-- Cada questão tem 5 alternativas, nas posições 0 (A) a 4 (E), e só uma correta (R41).
CREATE TABLE alternativa (
    questao_id INTEGER NOT NULL REFERENCES questao (id),
    posicao INTEGER NOT NULL CHECK (posicao BETWEEN 0 AND 4),
    texto TEXT NOT NULL,
    correta INTEGER NOT NULL CHECK (correta IN (0, 1)),
    PRIMARY KEY (questao_id, posicao)
);

CREATE UNIQUE INDEX uma_correta_por_questao ON alternativa (questao_id) WHERE correta = 1;
