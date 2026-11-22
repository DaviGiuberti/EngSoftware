-- 0016: reembolso da compra de pacote, do módulo vendas (H17).
--
-- reembolsada_em fica vazio até o reembolso ser aceito; daí em diante, a compra não dá acesso
-- (R63). A compra feita depois de um reembolso do mesmo pacote não tem direito a reembolso (R13).
-- As compras que já existem não tinham reembolso nenhum antes delas, então têm direito.
-- reembolsada_em é texto ISO 8601, no horário de Brasília.
ALTER TABLE compra ADD COLUMN reembolsada_em TEXT;
ALTER TABLE compra ADD COLUMN com_direito_a_reembolso INTEGER NOT NULL DEFAULT 1
    CHECK (com_direito_a_reembolso IN (0, 1));
