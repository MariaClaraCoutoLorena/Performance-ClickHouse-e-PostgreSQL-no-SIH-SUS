--------POSTGRESQL-----------------
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

--------CLICKHOUSE-----------------
SELECT name as tabela, 
       engine as motor, 
       primary_key as chave_primaria, 
       sorting_key as chave_ordenacao
FROM system.tables 
WHERE name IN ('sih_rd', 'sih_sp');

SELECT table as tabela, 
       formatReadableSize(sum(data_uncompressed_bytes)) as tamanho_bruto_memoria,
       formatReadableSize(sum(data_compressed_bytes)) as tamanho_real_comprimido,
       round(sum(data_uncompressed_bytes) / sum(data_compressed_bytes), 2) as taxa_compressao
FROM system.parts 
WHERE table IN ('sih_rd', 'sih_sp') AND active 
GROUP BY table;

SELECT name as coluna, 
       type as tipo_dado, 
       compression_codec as codec_de_compressao
FROM system.columns 
WHERE table = 'sih_rd'
LIMIT 15;