SELECT 'Urgência' as tipo_atendimento, COUNT(*) as qtd, SUM(cast("VAL_TOT" as float)) as custo
FROM sih_rd WHERE "CAR_INT" = '02'
UNION ALL
SELECT 'Eletiva' as tipo_atendimento, COUNT(*) as qtd, SUM(cast("VAL_TOT" as float)) as custo
FROM sih_rd WHERE "CAR_INT" = '01'