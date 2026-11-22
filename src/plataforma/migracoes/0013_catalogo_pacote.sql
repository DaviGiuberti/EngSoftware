-- 0013: pacotes e aulas gravadas, do módulo catalogo (H25, H26, H34, H35).
--
-- materia_id e professor_id apontam para os módulos materias e identidade, sem chave estrangeira
-- (ADR 0002). A matéria e o nível não mudam depois de criado o pacote (R56). O preço fica em
-- centavos e vazio até o ADM publicar o pacote; publicado ou arquivado, ele sempre tem preço (R59).
CREATE TABLE pacote (
    id INTEGER PRIMARY KEY,
    titulo TEXT NOT NULL CHECK (titulo <> ''),
    materia_id INTEGER NOT NULL,
    nivel INTEGER NOT NULL CHECK (nivel >= 1),
    professor_id INTEGER NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN ('rascunho', 'em_revisao', 'publicado', 'arquivado')),
    preco_em_centavos INTEGER CHECK (preco_em_centavos > 0),
    CHECK (estado IN ('rascunho', 'em_revisao') OR preco_em_centavos IS NOT NULL)
);

CREATE INDEX pacote_por_professor ON pacote (professor_id);

-- As aulas do pacote, numeradas de 1 em diante. Depois de publicado, o pacote não perde aulas
-- (R58), então o número de uma aula não muda mais, e o pacote e o número dizem qual é a aula.
-- O link é sempre o de um vídeo do YouTube, no formato youtube.com/watch?v=.
CREATE TABLE aula_gravada (
    pacote_id INTEGER NOT NULL REFERENCES pacote (id),
    numero INTEGER NOT NULL CHECK (numero >= 1),
    titulo TEXT NOT NULL CHECK (titulo <> ''),
    link TEXT NOT NULL,
    PRIMARY KEY (pacote_id, numero)
);
