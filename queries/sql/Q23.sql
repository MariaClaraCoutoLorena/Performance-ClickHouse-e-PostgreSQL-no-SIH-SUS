-- Q23: Bloco 2 - Manipulação de Strings (Filtro de Padrão LIKE) e Agregação
SELECT "CNES", COUNT(*) as qtd
FROM sih_rd
WHERE "CNES" LIKE '2%5'
GROUP BY "CNES";
