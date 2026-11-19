WITH rd_idosos AS (
    SELECT "N_AIH", "MUNIC_RES" FROM sih_rd WHERE cast("IDADE" as integer) > 60
),
sp_custos AS (
    SELECT "SP_NAIH", SUM(cast("SP_VALATO" as float)) as gasto_proc FROM sih_sp GROUP BY "SP_NAIH"
)
SELECT r."MUNIC_RES", COUNT(r."N_AIH") as qtd_idosos, SUM(s.gasto_proc) as total_gasto
FROM rd_idosos r
JOIN sp_custos s ON r."N_AIH" = s."SP_NAIH"
GROUP BY r."MUNIC_RES"
ORDER BY total_gasto DESC LIMIT 100