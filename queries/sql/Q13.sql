-- Q13: Bloco 1 - Agregação, Agrupamento Composto e Ordenação Top-N (GROUP BY + ORDER BY + LIMIT)
SELECT "CNES", "MUNIC_RES", COUNT(*) as total
FROM sih_rd
GROUP BY "CNES", "MUNIC_RES"
ORDER BY total DESC LIMIT 100;
