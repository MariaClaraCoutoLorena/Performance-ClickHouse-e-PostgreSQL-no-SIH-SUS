SELECT CONCAT("MUNIC_RES", '-', "CNES") as chave_local, COUNT(*) as qtd 
FROM sih_rd 
GROUP BY CONCAT("MUNIC_RES", '-', "CNES") 
ORDER BY qtd DESC LIMIT 100