-- Q42: Bloco 4 - CTE (WITH) e Função de Janela (Window Function - LAG)
WITH mensal AS (
    SELECT "MES_CMPT" as mes, SUM("VAL_TOT") as gasto
    FROM sih_rd
    WHERE "ANO_CMPT" = '2024'
    GROUP BY "MES_CMPT"
)
SELECT mes, gasto, LAG(gasto) OVER (ORDER BY mes) as gasto_mes_anterior
FROM mensal
ORDER BY mes;
