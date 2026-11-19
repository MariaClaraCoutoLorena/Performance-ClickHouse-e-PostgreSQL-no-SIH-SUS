WITH media_hosp AS (
    SELECT "CNES", AVG(cast("VAL_TOT" as float)) as media_cnes
    FROM sih_rd
    GROUP BY "CNES"
)
SELECT r."N_AIH", r."CNES", cast(r."VAL_TOT" as float) as valor, m.media_cnes
FROM sih_rd r
JOIN media_hosp m ON r."CNES" = m."CNES"
WHERE cast(r."VAL_TOT" as float) > (m.media_cnes * 5)
ORDER BY valor DESC LIMIT 100