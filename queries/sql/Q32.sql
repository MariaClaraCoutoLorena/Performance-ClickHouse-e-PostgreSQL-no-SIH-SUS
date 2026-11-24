-- Q32: Bloco 3 - Junção (JOIN) com Chave Composta e Agregação Top-N
SELECT sp."SP_PF_CBO", SUM(sp."SP_VALATO") as valor_gerado
FROM sih_rd rd
JOIN sih_sp sp
  ON rd."N_AIH" = sp."SP_NAIH"
 AND rd."ANO_CMPT" = sp."SP_AA"
 AND rd."MES_CMPT" = sp."SP_MM"
 AND rd."SEQUENCIA" = sp."SEQUENCIA"
GROUP BY sp."SP_PF_CBO"
ORDER BY valor_gerado DESC LIMIT 50;
