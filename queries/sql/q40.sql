SELECT CONCAT(r."ANO_CMPT", '-', r."MES_CMPT") as periodo, 
       UPPER(TRIM(r."DIAG_PRINC")) as diag_limpo, 
       COUNT(s."SEQUENCIA") as qtd_procedimentos 
FROM sih_rd r 
JOIN sih_sp s ON r."N_AIH" = s."SP_NAIH" 
WHERE LENGTH(s."SP_PROCREA") >= 8
GROUP BY CONCAT(r."ANO_CMPT", '-', r."MES_CMPT"), UPPER(TRIM(r."DIAG_PRINC")) 
ORDER BY qtd_procedimentos DESC LIMIT 50