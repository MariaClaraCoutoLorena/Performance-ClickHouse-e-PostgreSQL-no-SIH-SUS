SELECT rd."MUNIC_RES", 
       SUM(CASE WHEN rd."MORTE" = 1 THEN rd."VAL_TOT" ELSE 0 END) as custo_obitos, 
       SUM(CASE WHEN rd."MORTE" = 0 THEN rd."VAL_TOT" ELSE 0 END) as custo_sobreviventes 
FROM sih_rd rd 
GROUP BY rd."MUNIC_RES" 
ORDER BY custo_obitos DESC LIMIT 100