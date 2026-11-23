-- Q39: Bloco 4 - Subconsulta (Subquery com IN Composto) e Agregação
SELECT "SP_PROCREA", COUNT(*) as qtd
FROM sih_sp
WHERE ("SP_NAIH", "SP_AA", "SP_MM", "SEQUENCIA") IN (
    SELECT "N_AIH", "ANO_CMPT", "MES_CMPT", "SEQUENCIA"
    FROM sih_rd
    WHERE "MORTE" = 1
)
GROUP BY "SP_PROCREA"
ORDER BY qtd DESC LIMIT 100;
