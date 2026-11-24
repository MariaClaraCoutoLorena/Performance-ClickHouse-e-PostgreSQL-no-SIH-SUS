-- Q07: Bloco 1 - Filtro de Intervalo Direto (Range Scan - BETWEEN) e Agregação
SELECT COUNT(*) as qtd_internacoes, SUM("VAL_TOT") as gasto_periodo
FROM sih_rd
WHERE "DT_INTER" BETWEEN '20240601' AND '20240630';
