-- Q09: Bloco 1 - Agregação e Agrupamento com Filtro (WHERE + GROUP BY)
SELECT "MUNIC_RES", COUNT(*) as qtd_idosos
FROM sih_rd
WHERE "IDADE" > 60
GROUP BY "MUNIC_RES";
