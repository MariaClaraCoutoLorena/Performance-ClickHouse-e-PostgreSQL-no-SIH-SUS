-- Q44: Bloco 4 - CTE (WITH), Junção com Chave Composta, Manipulação de Strings e Função de Janela (RANK)
WITH base AS (
    SELECT r."MUNIC_RES", r."CNES", SUBSTRING(r."DIAG_PRINC", 1, 3) as categoria_doenca,
           COUNT(s."SEQUENCIA") as qtd_proc, SUM(s."SP_VALATO") as custo_proc
    FROM sih_rd r
    JOIN sih_sp s
      ON r."N_AIH" = s."SP_NAIH"
     AND r."ANO_CMPT" = s."SP_AA"
     AND r."MES_CMPT" = s."SP_MM"
     AND r."SEQUENCIA" = s."SEQUENCIA"
    WHERE r."MORTE" = 1 AND length(r."DIAG_PRINC") >= 3
    GROUP BY r."MUNIC_RES", r."CNES", SUBSTRING(r."DIAG_PRINC", 1, 3)
)
SELECT "MUNIC_RES", "CNES", categoria_doenca, custo_proc,
       RANK() OVER(PARTITION BY "MUNIC_RES" ORDER BY custo_proc DESC) as rk_custo
FROM base
ORDER BY "MUNIC_RES", rk_custo
LIMIT 100;
