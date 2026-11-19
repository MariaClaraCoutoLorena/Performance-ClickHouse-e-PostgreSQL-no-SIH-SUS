SELECT rd."DIAG_PRINC", 
       COUNT(DISTINCT rd."N_AIH") as qtd_internacoes, 
       COUNT(sp."SEQUENCIA") as qtd_procedimentos, 
       SUM(sp."SP_VALATO") as custo_procedimentos, 
       AVG(rd."DIAS_PERM") as media_dias_internacao 
FROM sih_rd rd 
JOIN sih_sp sp ON rd."N_AIH" = sp."SP_NAIH" 
GROUP BY rd."DIAG_PRINC" 
ORDER BY custo_procedimentos DESC LIMIT 50