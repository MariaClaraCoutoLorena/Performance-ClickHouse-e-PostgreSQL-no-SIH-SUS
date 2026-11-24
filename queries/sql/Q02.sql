-- Q02: Bloco 1 - Projeção Larga sem Agregação (Wide Row Retrieval)
SELECT "N_AIH", "ANO_CMPT", "MES_CMPT", "SEQUENCIA", "IDADE", "SEXO",
       "DIAG_PRINC", "MUNIC_RES", "CNES", "DT_INTER", "CAR_INT",
       "VAL_TOT", "DIAS_PERM", "MORTE"
FROM sih_rd
WHERE "MUNIC_RES" = '355030' AND "MORTE" = 1
LIMIT 1000;
