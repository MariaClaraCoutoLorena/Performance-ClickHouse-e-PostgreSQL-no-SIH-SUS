-- Q25: Bloco 2 - Manipulação de Strings (Múltiplos NOT LIKE) e Agregação
SELECT "MUNIC_RES", COUNT(*) as qtd
FROM sih_rd
WHERE "DIAG_PRINC" NOT LIKE 'I%'
  AND "DIAG_PRINC" NOT LIKE 'J%'
  AND "DIAG_PRINC" NOT LIKE 'O%'
GROUP BY "MUNIC_RES"
ORDER BY qtd DESC LIMIT 100;
