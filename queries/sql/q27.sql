WITH rank_hospitais AS (
    SELECT "MUNIC_RES", "CNES", SUM(cast("VAL_TOT" as float)) as total,
           RANK() OVER(PARTITION BY "MUNIC_RES" ORDER BY SUM(cast("VAL_TOT" as float)) DESC) as rk
    FROM sih_rd
    GROUP BY "MUNIC_RES", "CNES"
)
SELECT "MUNIC_RES", "CNES", total
FROM rank_hospitais
WHERE rk = 1
ORDER BY total DESC LIMIT 100