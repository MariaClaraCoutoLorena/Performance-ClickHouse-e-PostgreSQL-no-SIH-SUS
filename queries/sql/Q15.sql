-- Q15: Bloco 1 - Agregação com Contagem Distinta de Alta Cardinalidade (COUNT DISTINCT em tabela fato)
SELECT "SP_PROCREA", COUNT(DISTINCT "SP_NAIH") as qtd_aihs_distintas
FROM sih_sp
GROUP BY "SP_PROCREA"
ORDER BY qtd_aihs_distintas DESC LIMIT 100;
