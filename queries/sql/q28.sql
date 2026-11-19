WITH mensal AS (
    SELECT "MES_CMPT" as mes, SUM(cast("VAL_TOT" as float)) as gasto
    FROM sih_rd
    WHERE "ANO_CMPT" = '2024'
    GROUP BY "MES_CMPT"
)
SELECT mes, gasto, LAG(gasto) OVER (ORDER BY mes) as gasto_mes_anterior
FROM mensal
ORDER BY mes