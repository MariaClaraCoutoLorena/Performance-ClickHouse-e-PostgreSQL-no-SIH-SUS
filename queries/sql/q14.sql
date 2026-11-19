SELECT SUM(sp."SP_VALATO") as valor_total_atos 
FROM sih_rd rd 
JOIN sih_sp sp ON rd."N_AIH" = sp."SP_NAIH"