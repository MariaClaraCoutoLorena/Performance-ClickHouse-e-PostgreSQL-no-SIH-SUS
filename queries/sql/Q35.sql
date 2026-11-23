-- Q35: Bloco 3 - Junção (JOIN) com Chave Composta e Agregação com HAVING
SELECT rd."CNES", sp."SP_PROCREA", SUM(sp."SP_VALATO") as custo
FROM sih_rd rd
JOIN sih_sp sp
  ON rd."N_AIH" = sp."SP_NAIH"
 AND rd."ANO_CMPT" = sp."SP_AA"
 AND rd."MES_CMPT" = sp."SP_MM"
 AND rd."SEQUENCIA" = sp."SEQUENCIA"
GROUP BY rd."CNES", sp."SP_PROCREA"
HAVING SUM(sp."SP_VALATO") > 50000
ORDER BY custo DESC LIMIT 100;
