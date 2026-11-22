-- 0007: turmas, do módulo turmas (H30, H31, H20).
--
-- materia_id e professor_id apontam para os módulos materias e identidade, sem chave
-- estrangeira (ADR 0002). Os dias da semana vão de 0 (segunda) a 6 (domingo), como no
-- date.weekday() do Python. A turma tem 1 ou 2 aulas por semana (R04): na de 1 aula, o
-- segundo_dia fica NULL. As horas são texto 'HH:MM', e inicio_da_etapa é o início da 1ª aula
-- da etapa (R43), em texto ISO 8601 no horário de Brasília. O horário não muda (R24): só o
-- professor (R26) e, nas próximas fatias, o nível e a etapa mudam.
CREATE TABLE turma (
    id INTEGER PRIMARY KEY,
    materia_id INTEGER NOT NULL,
    nivel INTEGER NOT NULL CHECK (nivel >= 1),
    professor_id INTEGER NOT NULL,
    primeiro_dia INTEGER NOT NULL CHECK (primeiro_dia BETWEEN 0 AND 6),
    segundo_dia INTEGER CHECK (segundo_dia BETWEEN 0 AND 6 AND segundo_dia > primeiro_dia),
    inicio TEXT NOT NULL,
    fim TEXT NOT NULL CHECK (fim > inicio),
    inicio_da_etapa TEXT NOT NULL
);

CREATE INDEX turma_por_professor ON turma (professor_id);
