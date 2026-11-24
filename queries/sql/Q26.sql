-- Q26: Bloco 2 - Manipulação de Strings (SUBSTRING, LENGTH) e Agregação
SELECT SUBSTRING("DT_INTER", 7, 2) as dia_do_mes, COUNT(*) as total_internacoes
FROM sih_rd
WHERE LENGTH("DT_INTER") = 8
GROUP BY SUBSTRING("DT_INTER", 7, 2)
ORDER BY total_internacoes DESC;
