-- 0005: o nivelamento que o aluno faz, as respostas dele e o nível do aluno em cada matéria,
-- do módulo nivelamento (H01, H02, H03, H33).
--
-- aluno_id e materia_id apontam para os módulos identidade e materias, sem chave estrangeira
-- (ADR 0002). As datas são texto ISO 8601, no horário de Brasília. O tempo fica em segundos,
-- com fração: arredondar a cada gravação daria minutos de presente ao aluno no fim do teste.
CREATE TABLE nivelamento (
    id INTEGER PRIMARY KEY,
    aluno_id INTEGER NOT NULL,
    materia_id INTEGER NOT NULL,
    iniciado_em TEXT NOT NULL,
    tempo_usado_em_segundos REAL NOT NULL DEFAULT 0 CHECK (tempo_usado_em_segundos >= 0),
    tempo_extra_em_segundos REAL NOT NULL DEFAULT 0 CHECK (tempo_extra_em_segundos >= 0),
    -- Preenchido enquanto o teste está aberto: o tempo só corre nesse período (R30).
    aberto_desde TEXT,
    concluido_em TEXT,
    nota INTEGER CHECK (nota BETWEEN 0 AND 100),
    nivel INTEGER CHECK (nivel >= 1)
);

-- Um aluno tem no máximo um nivelamento em andamento em cada matéria.
CREATE UNIQUE INDEX um_nivelamento_em_andamento
    ON nivelamento (aluno_id, materia_id) WHERE concluido_em IS NULL;

CREATE TABLE resposta (
    nivelamento_id INTEGER NOT NULL REFERENCES nivelamento (id),
    questao_id INTEGER NOT NULL REFERENCES questao (id),
    posicao INTEGER NOT NULL CHECK (posicao BETWEEN 0 AND 4),
    PRIMARY KEY (nivelamento_id, questao_id)
);

-- O nível do aluno em cada matéria (R01). O nivelamento define o primeiro; a promoção muda
-- depois. refazer_liberado é a liberação do ADM, que vale para uma tentativa (R03).
CREATE TABLE nivel_do_aluno (
    aluno_id INTEGER NOT NULL,
    materia_id INTEGER NOT NULL,
    nivel INTEGER NOT NULL CHECK (nivel >= 1),
    refazer_liberado INTEGER NOT NULL DEFAULT 0 CHECK (refazer_liberado IN (0, 1)),
    PRIMARY KEY (aluno_id, materia_id)
);
