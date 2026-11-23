-- Q31: Bloco 3 - Junção (JOIN) com Chave Composta e Agregação (SUM)
SELECT SUM(sp."SP_VALATO") as valor_total_atos
FROM sih_rd rd
JOIN sih_sp sp
  ON rd."N_AIH" = sp."SP_NAIH"
 AND rd."ANO_CMPT" = sp."SP_AA"
 AND rd."MES_CMPT" = sp."SP_MM"
 AND rd."SEQUENCIA" = sp."SEQUENCIA";
