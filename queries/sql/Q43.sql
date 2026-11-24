-- Q43: Bloco 4 - CTE (WITH) e Função de Janela (Window Function - RANK)
WITH rank_hospitais AS (
    SELECT "MUNIC_RES", "CNES", SUM("VAL_TOT") as total,
           RANK() OVER(PARTITION BY "MUNIC_RES" ORDER BY SUM("VAL_TOT") DESC) as rk
    FROM sih_rd
    GROUP BY "MUNIC_RES", "CNES"
)
SELECT "MUNIC_RES", "CNES", total
FROM rank_hospitais
WHERE rk = 1
ORDER BY total DESC LIMIT 100;
