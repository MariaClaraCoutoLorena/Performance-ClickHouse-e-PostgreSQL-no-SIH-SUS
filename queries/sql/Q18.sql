-- Q18: Bloco 1 - União de Consultas (UNION ALL) e Agregação
SELECT 'Urgência' as tipo_atendimento, COUNT(*) as qtd, SUM("VAL_TOT") as custo
FROM sih_rd WHERE "CAR_INT" = '02'
UNION ALL
SELECT 'Eletiva' as tipo_atendimento, COUNT(*) as qtd, SUM("VAL_TOT") as custo
FROM sih_rd WHERE "CAR_INT" = '01';
