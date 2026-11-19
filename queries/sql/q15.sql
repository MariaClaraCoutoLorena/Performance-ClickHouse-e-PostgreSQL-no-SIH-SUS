SELECT sp."SP_PROCREA", COUNT(*) as qtd_realizada 
FROM sih_rd rd 
JOIN sih_sp sp ON rd."N_AIH" = sp."SP_NAIH" 
WHERE rd."IDADE" > 60 
GROUP BY sp."SP_PROCREA" 
ORDER BY qtd_realizada DESC LIMIT 50