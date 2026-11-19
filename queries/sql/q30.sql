WITH base AS (
    SELECT r."MUNIC_RES", r."CNES", SUBSTRING(r."DIAG_PRINC", 1, 3) as categoria_doenca,
           COUNT(s."SEQUENCIA") as qtd_proc, SUM(cast(s."SP_VALATO" as float)) as custo_proc
    FROM sih_rd r
    JOIN sih_sp s ON r."N_AIH" = s."SP_NAIH"
    WHERE r."MORTE" = 1 AND length(r."DIAG_PRINC") >= 3
    GROUP BY r."MUNIC_RES", r."CNES", SUBSTRING(r."DIAG_PRINC", 1, 3)
)
SELECT "MUNIC_RES", "CNES", categoria_doenca, custo_proc,
       RANK() OVER(PARTITION BY "MUNIC_RES" ORDER BY custo_proc DESC) as rk_custo
FROM base
ORDER BY "MUNIC_RES", rk_custo
LIMIT 100