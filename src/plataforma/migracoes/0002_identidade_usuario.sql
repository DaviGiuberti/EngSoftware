-- 0002: usuários do módulo identidade (H38).
--
-- O e-mail chega sem espaços nas pontas e em minúsculas, então o UNIQUE já recusa o mesmo
-- e-mail com outras maiúsculas (R39). A senha nunca é guardada, só o hash com sal (RNF06).
CREATE TABLE usuario (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    hash_da_senha TEXT NOT NULL,
    perfil TEXT NOT NULL CHECK (perfil IN ('aluno', 'professor', 'adm'))
);
