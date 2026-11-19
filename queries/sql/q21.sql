WITH obitos AS (
    SELECT "MUNIC_RES", "VAL_TOT"
    FROM sih_rd
    WHERE "MORTE" = 1
)
SELECT "MUNIC_RES", COUNT(*) as qtd_obitos, SUM(cast("VAL_TOT" as float)) as gasto_obitos
FROM obitos
GROUP BY "MUNIC_RES"
ORDER BY qtd_obitos DESC LIMIT 100