-- Q28: Bloco 2 - Manipulação de Strings (SUBSTRING, LENGTH) e Auditoria Temporal
SELECT "ANO_CMPT", SUBSTRING("DT_INTER", 1, 4) as ano_inter, COUNT(*) as qtd_atrasos
FROM sih_rd
WHERE "ANO_CMPT" != SUBSTRING("DT_INTER", 1, 4)
  AND LENGTH("DT_INTER") = 8
GROUP BY "ANO_CMPT", SUBSTRING("DT_INTER", 1, 4)
LIMIT 100;
