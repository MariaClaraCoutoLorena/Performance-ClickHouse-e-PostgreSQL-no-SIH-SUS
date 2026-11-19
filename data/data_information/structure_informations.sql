SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE tablename IN ('sih_rd', 'sih_sp');

SELECT conname as nome_restricao, 
       contype as tipo (p=primary, f=foreign), 
       pg_get_constraintdef(oid) as definicao
FROM pg_constraint 
WHERE conrelid IN ('sih_rd'::regclass, 'sih_sp'::regclass);

SELECT relname as tabela, 
       pg_size_pretty(pg_total_relation_size(relid)) as tamanho_total_disco
FROM pg_catalog.pg_statio_user_tables
WHERE relname IN ('sih_rd', 'sih_sp');