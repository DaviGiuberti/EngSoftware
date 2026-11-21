-- 0006: habilitação dos professores por matéria, do módulo identidade (H29).
--
-- Habilitado numa matéria, o professor dá aula em todos os níveis dela (R11), então a
-- habilitação não guarda nível. materia_id aponta para o módulo materias, sem chave
-- estrangeira (ADR 0002): o caso de uso confere a matéria pela consulta pública do materias.
CREATE TABLE habilitacao (
    professor_id INTEGER NOT NULL REFERENCES usuario (id),
    materia_id INTEGER NOT NULL,
    PRIMARY KEY (professor_id, materia_id)
);
