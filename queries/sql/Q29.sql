-- Q29: Bloco 2 - Manipulação de Strings, Expressão Condicional (CASE WHEN) e Agregação
SELECT
    SUBSTRING("DT_INTER", 1, 4) as ano,
    CASE WHEN CAST(SUBSTRING("DT_INTER", 5, 2) AS INTEGER) <= 6 THEN '1_Semestre' ELSE '2_Semestre' END as semestre,
    SUM("VAL_TOT") as custo
FROM sih_rd
WHERE LENGTH("DT_INTER") = 8
GROUP BY
    SUBSTRING("DT_INTER", 1, 4),
    CASE WHEN CAST(SUBSTRING("DT_INTER", 5, 2) AS INTEGER) <= 6 THEN '1_Semestre' ELSE '2_Semestre' END;
