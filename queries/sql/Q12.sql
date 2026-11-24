-- Q12: Bloco 1 - Agregação, Agrupamento e Ordenação Top-N (GROUP BY + ORDER BY + LIMIT)
SELECT "DIAG_PRINC", SUM("VAL_TOT") as gasto_doenca
FROM sih_rd
GROUP BY "DIAG_PRINC"
ORDER BY gasto_doenca DESC LIMIT 100;
