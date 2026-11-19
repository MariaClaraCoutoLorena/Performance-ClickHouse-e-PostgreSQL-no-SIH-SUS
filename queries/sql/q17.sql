SELECT rd."DIAG_PRINC", COUNT(sp."SEQUENCIA") as qtd_procedimentos 
FROM sih_rd rd 
JOIN sih_sp sp ON rd."N_AIH" = sp."SP_NAIH" 
GROUP BY rd."DIAG_PRINC" 
ORDER BY qtd_procedimentos DESC LIMIT 50