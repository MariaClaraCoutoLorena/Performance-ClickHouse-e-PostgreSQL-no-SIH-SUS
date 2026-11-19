SELECT COUNT(sp."SEQUENCIA") as total_procedimentos 
FROM sih_rd rd 
JOIN sih_sp sp ON rd."N_AIH" = sp."SP_NAIH"