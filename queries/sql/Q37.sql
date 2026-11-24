-- Q37: Bloco 3 - Junção (JOIN) com Chave Composta, Manipulação de Strings e Agregação Top-N
SELECT CONCAT(r."ANO_CMPT", '-', r."MES_CMPT") as periodo,
       UPPER(TRIM(r."DIAG_PRINC")) as diag_limpo,
       COUNT(s."SEQUENCIA") as qtd_procedimentos
FROM sih_rd r
JOIN sih_sp s
  ON r."N_AIH" = s."SP_NAIH"
 AND r."ANO_CMPT" = s."SP_AA"
 AND r."MES_CMPT" = s."SP_MM"
 AND r."SEQUENCIA" = s."SEQUENCIA"
WHERE LENGTH(s."SP_PROCREA") >= 8
GROUP BY CONCAT(r."ANO_CMPT", '-', r."MES_CMPT"), UPPER(TRIM(r."DIAG_PRINC"))
ORDER BY qtd_procedimentos DESC LIMIT 50;
