SELECT rd."CNES", sp."SP_PROCREA", SUM(sp."SP_VALATO") as custo 
FROM sih_rd rd 
JOIN sih_sp sp ON rd."N_AIH" = sp."SP_NAIH" 
GROUP BY rd."CNES", sp."SP_PROCREA" 
HAVING SUM(sp."SP_VALATO") > 50000 
ORDER BY custo DESC LIMIT 100