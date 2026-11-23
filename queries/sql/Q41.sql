-- Q41: Bloco 4 - Múltiplas CTEs (WITH) e Junção (JOIN) com Chave Composta
WITH rd_idosos AS (
    SELECT "N_AIH", "ANO_CMPT", "MES_CMPT", "SEQUENCIA", "MUNIC_RES"
    FROM sih_rd
    WHERE "IDADE" > 60
),
sp_custos AS (
    SELECT "SP_NAIH", "SP_AA", "SP_MM", "SEQUENCIA", SUM("SP_VALATO") as gasto_proc
    FROM sih_sp
    GROUP BY "SP_NAIH", "SP_AA", "SP_MM", "SEQUENCIA"
)
SELECT r."MUNIC_RES", COUNT(r."N_AIH") as qtd_idosos, SUM(s.gasto_proc) as total_gasto
FROM rd_idosos r
JOIN sp_custos s
  ON r."N_AIH" = s."SP_NAIH"
 AND r."ANO_CMPT" = s."SP_AA"
 AND r."MES_CMPT" = s."SP_MM"
 AND r."SEQUENCIA" = s."SEQUENCIA"
GROUP BY r."MUNIC_RES"
ORDER BY total_gasto DESC LIMIT 100;
