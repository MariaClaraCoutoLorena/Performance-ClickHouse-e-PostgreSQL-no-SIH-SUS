-- Q40: Bloco 4 - CTE (WITH) e Auto-Junção Analítica (Detecção de Outliers)
WITH media_hosp AS (
    SELECT "CNES", AVG("VAL_TOT") as media_cnes
    FROM sih_rd
    GROUP BY "CNES"
)
SELECT r."N_AIH", r."CNES", r."VAL_TOT" as valor, m.media_cnes
FROM sih_rd r
JOIN media_hosp m ON r."CNES" = m."CNES"
WHERE r."VAL_TOT" > (m.media_cnes * 5)
ORDER BY valor DESC LIMIT 100;
