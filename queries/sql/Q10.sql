-- Q10: Bloco 1 - Agregação e Agrupamento com Lista de Valores (IN + GROUP BY)
SELECT "CNES", COUNT(*) as casos
FROM sih_rd
WHERE "DIAG_PRINC" IN ('I219', 'J189', 'E119')
GROUP BY "CNES";
