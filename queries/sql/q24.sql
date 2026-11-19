SELECT SUBSTRING("DIAG_PRINC", 1, 1) as capitulo_cid, COUNT(*) as volume_casos
FROM sih_rd
GROUP BY SUBSTRING("DIAG_PRINC", 1, 1)
ORDER BY volume_casos DESC