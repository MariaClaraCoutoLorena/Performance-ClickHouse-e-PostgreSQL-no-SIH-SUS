-- Q06: Bloco 1 - Consulta simples (Filtro Composto e Agregação)
SELECT COUNT(*) as casos_obito
FROM sih_rd
WHERE "SEXO" = '3' AND "MORTE" = 1;
