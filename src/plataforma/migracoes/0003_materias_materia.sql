-- 0003: matérias e faixas do nivelamento, do módulo materias (H27).
--
-- Cada nível tem uma faixa (R40), então o nível máximo da matéria é o número de faixas dela.
-- A mensalidade fica em centavos, como número inteiro, para não ter erro de arredondamento.
-- O nome repetido com outras maiúsculas é recusado pelo caso de uso; o UNIQUE com NOCASE é
-- uma segunda barreira, que só compara as letras sem acento.
CREATE TABLE materia (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE COLLATE NOCASE,
    mensalidade_em_centavos INTEGER NOT NULL CHECK (mensalidade_em_centavos > 0)
);

CREATE TABLE faixa (
    materia_id INTEGER NOT NULL REFERENCES materia (id),
    nivel INTEGER NOT NULL CHECK (nivel >= 1),
    nota_minima INTEGER NOT NULL CHECK (nota_minima BETWEEN 0 AND 100),
    nota_maxima INTEGER NOT NULL CHECK (nota_maxima BETWEEN nota_minima AND 100),
    PRIMARY KEY (materia_id, nivel)
);
