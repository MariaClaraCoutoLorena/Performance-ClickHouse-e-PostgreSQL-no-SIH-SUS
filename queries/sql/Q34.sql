-- Q34: Bloco 3 - Junção (JOIN) com Chave Composta, Filtro (WHERE) e Agregação Top-N
SELECT sp."SP_PROCREA", COUNT(*) as qtd_realizada
FROM sih_rd rd
JOIN sih_sp sp
  ON rd."N_AIH" = sp."SP_NAIH"
 AND rd."ANO_CMPT" = sp."SP_AA"
 AND rd."MES_CMPT" = sp."SP_MM"
 AND rd."SEQUENCIA" = sp."SEQUENCIA"
WHERE rd."IDADE" > 60
GROUP BY sp."SP_PROCREA"
ORDER BY qtd_realizada DESC LIMIT 50;
