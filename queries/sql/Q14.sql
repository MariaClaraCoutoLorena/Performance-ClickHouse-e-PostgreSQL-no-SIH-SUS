-- Q14: Bloco 1 - Agregação com Contagem Distinta (COUNT DISTINCT + GROUP BY)
SELECT "MUNIC_RES", COUNT(DISTINCT "DIAG_PRINC") as diversidade_doencas
FROM sih_rd
GROUP BY "MUNIC_RES"
ORDER BY diversidade_doencas DESC LIMIT 100;
