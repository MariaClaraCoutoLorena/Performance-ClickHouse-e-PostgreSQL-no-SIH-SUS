-- Q38: Bloco 4 - CTE (WITH) e Agregação
WITH obitos AS (
    SELECT "MUNIC_RES", "VAL_TOT"
    FROM sih_rd
    WHERE "MORTE" = 1
)
SELECT "MUNIC_RES", COUNT(*) as qtd_obitos, SUM("VAL_TOT") as gasto_obitos
FROM obitos
GROUP BY "MUNIC_RES"
ORDER BY qtd_obitos DESC LIMIT 100;
