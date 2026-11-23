-- Q16: Bloco 1 - Agregação com Filtro Pós-Agrupamento (GROUP BY + HAVING)
SELECT "CNES", SUM("VAL_TOT") as valor_total
FROM sih_rd
GROUP BY "CNES"
HAVING SUM("VAL_TOT") > 1000000
ORDER BY valor_total DESC LIMIT 50;
