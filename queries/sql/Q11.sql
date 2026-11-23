-- Q11: Bloco 1 - Agregação, Agrupamento Composto e Ordenação (GROUP BY + ORDER BY)
SELECT "ANO_CMPT", "MES_CMPT", SUM("VAL_TOT") as custo_mensal
FROM sih_rd
GROUP BY "ANO_CMPT", "MES_CMPT"
ORDER BY "ANO_CMPT", "MES_CMPT";
