SELECT sp."SP_PF_CBO", SUM(sp."SP_VALATO") as valor_gerado 
FROM sih_rd rd 
JOIN sih_sp sp ON rd."N_AIH" = sp."SP_NAIH" 
GROUP BY sp."SP_PF_CBO" 
ORDER BY valor_gerado DESC LIMIT 50