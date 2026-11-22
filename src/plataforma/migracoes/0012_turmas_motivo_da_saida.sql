-- 0012: o motivo da saída da matrícula, do módulo turmas (H07).
--
-- Quando a matrícula termina, fica guardado o motivo: vontade própria (R29), reprovação (R21),
-- conclusão da trilha na turma que encerrou (R09) ou atraso da mensalidade (R28). O aviso de
-- quem perdeu a vaga por atraso depende dele (R55). As matrículas que já tinham terminado ficam
-- sem motivo, porque não dá para saber qual foi.
ALTER TABLE matricula ADD COLUMN saiu_por TEXT
    CHECK (saiu_por IN ('vontade', 'reprovacao', 'conclusao', 'atraso'));
