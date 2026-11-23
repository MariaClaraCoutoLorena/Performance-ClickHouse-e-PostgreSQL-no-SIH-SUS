-- Q24: Bloco 2 - Manipulação de Strings (Múltiplos LIKE) e Agregação
SELECT "ANO_CMPT", COUNT(*) as internacoes_festas
FROM sih_rd
WHERE "DT_INTER" LIKE '%1224' OR "DT_INTER" LIKE '%1225' OR "DT_INTER" LIKE '%1231'
GROUP BY "ANO_CMPT";
