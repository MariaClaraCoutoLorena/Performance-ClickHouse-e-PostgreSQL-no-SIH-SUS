-- Q33: Bloco 3 - Junção (JOIN) com Chave Composta e Agregação Top-N
SELECT rd."DIAG_PRINC", COUNT(sp."SEQUENCIA") as qtd_procedimentos
FROM sih_rd rd
JOIN sih_sp sp
  ON rd."N_AIH" = sp."SP_NAIH"
 AND rd."ANO_CMPT" = sp."SP_AA"
 AND rd."MES_CMPT" = sp."SP_MM"
 AND rd."SEQUENCIA" = sp."SEQUENCIA"
GROUP BY rd."DIAG_PRINC"
ORDER BY qtd_procedimentos DESC LIMIT 50;
