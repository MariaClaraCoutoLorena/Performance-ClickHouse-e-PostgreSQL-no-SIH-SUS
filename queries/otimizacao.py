import time
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
import clickhouse_connect

# Configurações de conexão
PG_URI = 'postgresql+psycopg2://admin:admin@localhost:5432/sih_db'
SCHEMA_ORIGEM = 'public'
SCHEMA_OTIMIZADO = 'sih_otimizado'

CH_CONFIG = {
    'host': 'localhost',
    'port': 8123,
    'username': 'admin',
    'password': 'admin',
    'database': 'sih_db'
}

ARQUIVO_RELATORIO = 'relatorio_estrutural_comparativo.txt'


def formatar_bytes(num_bytes):
    """Converte bytes em unidade legível (KB, MB, GB)."""
    if num_bytes is None:
        return "0 B"
    valor = float(num_bytes)
    for unidade in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(valor) < 1024.0:
            return f"{valor:.2f} {unidade}"
        valor /= 1024.0
    return f"{valor:.2f} PB"


def criar_schema_otimizado(pg_engine):
    """
    Cria o schema otimizado copiando as tabelas de public,
    define PK/FK compostas, cria índices B-Tree/Covering/Parciais
    e atualiza estatísticas (ANALYZE).
    """
    tempos_execucao = []

    etapas_ddl = [
        ("Criar schema otimizado",
         f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA_OTIMIZADO}";'),

        ("Limpar tabelas antigas no schema otimizado",
         f'DROP TABLE IF EXISTS "{SCHEMA_OTIMIZADO}".sih_sp, "{SCHEMA_OTIMIZADO}".sih_rd CASCADE;'),

        ("Copiar sih_rd para schema otimizado",
         f'CREATE TABLE "{SCHEMA_OTIMIZADO}".sih_rd AS TABLE "{SCHEMA_ORIGEM}".sih_rd;'),

        ("Copiar sih_sp para schema otimizado",
         f'CREATE TABLE "{SCHEMA_OTIMIZADO}".sih_sp AS TABLE "{SCHEMA_ORIGEM}".sih_sp;'),

        ("Alinhar tipo de SEQUENCIA em sih_rd (bigint)",
         f'ALTER TABLE "{SCHEMA_OTIMIZADO}".sih_rd ALTER COLUMN "SEQUENCIA" TYPE bigint USING "SEQUENCIA"::bigint;'),

        ("Criar PK composta em sih_rd",
         f'ALTER TABLE "{SCHEMA_OTIMIZADO}".sih_rd ADD PRIMARY KEY ("N_AIH", "ANO_CMPT", "MES_CMPT", "SEQUENCIA");'),

        ("Criar FK composta em sih_sp",
         f'''ALTER TABLE "{SCHEMA_OTIMIZADO}".sih_sp
             ADD CONSTRAINT fk_sih_sp_rd
             FOREIGN KEY ("SP_NAIH", "SP_AA", "SP_MM", "SEQUENCIA")
             REFERENCES "{SCHEMA_OTIMIZADO}".sih_rd ("N_AIH", "ANO_CMPT", "MES_CMPT", "SEQUENCIA")
             NOT VALID;'''),

        # --- SIH_RD: Índices B-Tree e de Cobertura (INCLUDE) ---
        ("Índice idx_pg_rd_diag_princ (Covering)",
         f'CREATE INDEX idx_pg_rd_diag_princ ON "{SCHEMA_OTIMIZADO}".sih_rd ("DIAG_PRINC") INCLUDE ("VAL_TOT");'),

        ("Índice idx_pg_rd_munic_res (Covering)",
         f'CREATE INDEX idx_pg_rd_munic_res ON "{SCHEMA_OTIMIZADO}".sih_rd ("MUNIC_RES") INCLUDE ("VAL_TOT", "DIAG_PRINC");'),

        ("Índice idx_pg_rd_cnes (Covering)",
         f'CREATE INDEX idx_pg_rd_cnes ON "{SCHEMA_OTIMIZADO}".sih_rd ("CNES") INCLUDE ("VAL_TOT", "MUNIC_RES");'),

        ("Índice idx_pg_rd_dtinter (Covering / Range Scan)",
         f'CREATE INDEX idx_pg_rd_dtinter ON "{SCHEMA_OTIMIZADO}".sih_rd ("DT_INTER") INCLUDE ("VAL_TOT");'),

        # --- SIH_RD: Índices Parciais ---
        ("Índice idx_pg_rd_morte_1 (Parcial + Covering)",
         f'CREATE INDEX idx_pg_rd_morte_1 ON "{SCHEMA_OTIMIZADO}".sih_rd ("MUNIC_RES", "N_AIH") INCLUDE ("VAL_TOT", "CNES", "DIAG_PRINC") WHERE "MORTE" = 1;'),

        ("Índice idx_pg_rd_idosos (Parcial)",
         f'CREATE INDEX idx_pg_rd_idosos ON "{SCHEMA_OTIMIZADO}".sih_rd ("MUNIC_RES", "N_AIH") WHERE "IDADE" > 60;'),

        # --- SIH_SP: Índices B-Tree e de Cobertura (INCLUDE) ---
        ("Índice idx_pg_sp_fk (FK Composta + Covering)",
         f'CREATE INDEX idx_pg_sp_fk ON "{SCHEMA_OTIMIZADO}".sih_sp ("SP_NAIH", "SP_AA", "SP_MM", "SEQUENCIA") INCLUDE ("SP_VALATO", "SP_PROCREA");'),

        ("Índice idx_pg_sp_procrea (Covering)",
         f'CREATE INDEX idx_pg_sp_procrea ON "{SCHEMA_OTIMIZADO}".sih_sp ("SP_PROCREA") INCLUDE ("SP_VALATO", "SP_NAIH");'),

        # --- Atualização de Estatísticas ---
        ("ANALYZE sih_rd (otimizado)",
         f'ANALYZE "{SCHEMA_OTIMIZADO}".sih_rd;'),

        ("ANALYZE sih_sp (otimizado)",
         f'ANALYZE "{SCHEMA_OTIMIZADO}".sih_sp;'),

        ("ANALYZE tabelas base (public)",
         f'ANALYZE "{SCHEMA_ORIGEM}".sih_rd; ANALYZE "{SCHEMA_ORIGEM}".sih_sp;')
    ]

    print(f"Iniciando criação e otimização do schema '{SCHEMA_OTIMIZADO}'...")
    with pg_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for descricao, sql in etapas_ddl:
            inicio = time.perf_counter()
            try:
                conn.execute(text(sql))
                duracao = time.perf_counter() - inicio
                tempos_execucao.append({"etapa": descricao, "tempo_segundos": round(duracao, 2), "status": "OK"})
                print(f"[OK] {descricao} ({duracao:.2f}s)")
            except Exception as e:
                duracao = time.perf_counter() - inicio
                tempos_execucao.append({"etapa": descricao, "tempo_segundos": round(duracao, 2), "status": f"ERRO: {e}"})
                print(f"[ERRO] {descricao}: {e}")

    return pd.DataFrame(tempos_execucao)


def coletar_metricas_pg(conn, schema):
    """Coleta tamanhos de tabelas, índices e definições de um schema PostgreSQL."""
    query_tamanho = text("""
        SELECT
            c.relname AS tabela,
            c.reltuples::bigint AS tuplas_estimadas,
            pg_size_pretty(pg_table_size(c.oid)) AS tamanho_dados,
            pg_size_pretty(pg_indexes_size(c.oid)) AS tamanho_indices,
            pg_size_pretty(pg_total_relation_size(c.oid)) AS tamanho_total_disco,
            pg_table_size(c.oid) AS dados_bytes,
            pg_indexes_size(c.oid) AS indices_bytes,
            pg_total_relation_size(c.oid) AS total_bytes
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = :schema
          AND c.relname IN ('sih_rd', 'sih_sp')
          AND c.relkind = 'r'
        ORDER BY c.relname;
    """)

    query_indices = text("""
        SELECT
            t.relname AS tabela,
            i.relname AS nome_indice,
            pg_size_pretty(pg_relation_size(i.oid)) AS tamanho_indice,
            pg_get_indexdef(i.oid) AS definicao
        FROM pg_index ix
        JOIN pg_class t ON t.oid = ix.indrelid
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = :schema
          AND t.relname IN ('sih_rd', 'sih_sp')
        ORDER BY t.relname, pg_relation_size(i.oid) DESC;
    """)

    df_tamanho = pd.read_sql(query_tamanho, conn, params={"schema": schema})
    df_indices = pd.read_sql(query_indices, conn, params={"schema": schema})
    return df_tamanho, df_indices


def gerar_relatorio_comparativo(pg_engine, df_tempos=None):
    """Gera o relatório TXT comparando PostgreSQL (public), PostgreSQL (otimizado) e ClickHouse."""
    ch_client = clickhouse_connect.get_client(**CH_CONFIG)
    separador = "=" * 90
    subsep = "-" * 90

    with pg_engine.connect() as conn:
        df_pg_norm_tam, df_pg_norm_idx = coletar_metricas_pg(conn, SCHEMA_ORIGEM)
        df_pg_otim_tam, df_pg_otim_idx = coletar_metricas_pg(conn, SCHEMA_OTIMIZADO)

    # Consultas ClickHouse
    query_ch_tables = f"""
        SELECT
            name AS tabela,
            engine AS motor,
            sorting_key AS chave_ordenacao,
            primary_key AS chave_primaria,
            total_rows AS total_tuplas
        FROM system.tables
        WHERE database = '{CH_CONFIG["database"]}'
          AND name IN ('sih_rd', 'sih_sp')
        ORDER BY name;
    """
    query_ch_comp = f"""
        SELECT
            table AS tabela,
            count() AS qtd_partes,
            sum(rows) AS total_linhas,
            formatReadableSize(sum(data_uncompressed_bytes)) AS tamanho_bruto,
            formatReadableSize(sum(data_compressed_bytes)) AS tamanho_real_disco,
            sum(data_uncompressed_bytes) AS bruto_bytes,
            sum(data_compressed_bytes) AS disco_bytes,
            if(sum(data_compressed_bytes) > 0,
               round(sum(data_uncompressed_bytes) / sum(data_compressed_bytes), 2),
               0) AS taxa_compressao
        FROM system.parts
        WHERE database = '{CH_CONFIG["database"]}'
          AND table IN ('sih_rd', 'sih_sp')
          AND active
        GROUP BY table
        ORDER BY table;
    """
    df_ch_tables = ch_client.query_df(query_ch_tables)
    df_ch_comp = ch_client.query_df(query_ch_comp)

    # Totais em bytes para o quadro comparativo final
    bytes_pg_norm = int(df_pg_norm_tam['total_bytes'].sum()) if not df_pg_norm_tam.empty else 0
    bytes_pg_otim = int(df_pg_otim_tam['total_bytes'].sum()) if not df_pg_otim_tam.empty else 0
    bytes_pg_otim_idx = int(df_pg_otim_tam['indices_bytes'].sum()) if not df_pg_otim_tam.empty else 0
    bytes_ch_bruto = int(df_ch_comp['bruto_bytes'].sum()) if not df_ch_comp.empty else 0
    bytes_ch_disco = int(df_ch_comp['disco_bytes'].sum()) if not df_ch_comp.empty else 0

    overhead_idx_pct = ((bytes_pg_otim - bytes_pg_norm) / bytes_pg_norm * 100) if bytes_pg_norm > 0 else 0
    reducao_ch_vs_pg_norm = (bytes_pg_norm / bytes_ch_disco) if bytes_ch_disco > 0 else 0
    reducao_ch_vs_pg_otim = (bytes_pg_otim / bytes_ch_disco) if bytes_ch_disco > 0 else 0

    with open(ARQUIVO_RELATORIO, 'w', encoding='utf-8') as f:
        f.write(f"{separador}\n")
        f.write("RELATÓRIO ESTRUTURAL COMPARATIVO — SIH-SUS\n")
        f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"{separador}\n\n")

        # 1. POSTGRESQL NORMAL (PUBLIC)
        f.write(f"1. POSTGRESQL NORMAL (Schema: {SCHEMA_ORIGEM})\n")
        f.write(f"{subsep}\n")
        f.write("1.1 Espaço em Disco e Volumetria:\n")
        cols_pg = ['tabela', 'tuplas_estimadas', 'tamanho_dados', 'tamanho_indices', 'tamanho_total_disco']
        f.write(df_pg_norm_tam[cols_pg].to_string(index=False) + "\n")
        f.write(f"Total em disco ({SCHEMA_ORIGEM}): {formatar_bytes(bytes_pg_norm)}\n\n")

        f.write("1.2 Índices Ativos:\n")
        if df_pg_norm_idx.empty:
            f.write("Nenhum índice encontrado (apenas varredura sequencial).\n\n")
        else:
            f.write(df_pg_norm_idx[['tabela', 'nome_indice', 'tamanho_indice']].to_string(index=False) + "\n\n")

        # 2. POSTGRESQL OTIMIZADO
        f.write(f"\n2. POSTGRESQL OTIMIZADO (Schema: {SCHEMA_OTIMIZADO})\n")
        f.write(f"{subsep}\n")
        f.write("2.1 Espaço em Disco e Volumetria:\n")
        f.write(df_pg_otim_tam[cols_pg].to_string(index=False) + "\n")
        f.write(f"Total em disco ({SCHEMA_OTIMIZADO}): {formatar_bytes(bytes_pg_otim)} "
                f"(sendo {formatar_bytes(bytes_pg_otim_idx)} apenas de índices | "
                f"overhead de +{overhead_idx_pct:.2f}% sobre o schema '{SCHEMA_ORIGEM}')\n\n")

        f.write("2.2 Índices Criados e Tamanhos:\n")
        if df_pg_otim_idx.empty:
            f.write("Nenhum índice encontrado.\n\n")
        else:
            f.write(df_pg_otim_idx[['tabela', 'nome_indice', 'tamanho_indice']].to_string(index=False) + "\n\n")
            f.write("2.3 Definições SQL dos Índices:\n")
            for _, row in df_pg_otim_idx.iterrows():
                f.write(f"  - [{row['tabela']}] {row['nome_indice']} ({row['tamanho_indice']}):\n")
                f.write(f"    {row['definicao']};\n")
            f.write("\n")

        if df_tempos is not None and not df_tempos.empty:
            f.write("2.4 Tempo de Construção do Schema Otimizado e Índices:\n")
            f.write(df_tempos.to_string(index=False) + "\n")
            f.write(f"Tempo total de preparação: {df_tempos['tempo_segundos'].sum():.2f} segundos\n\n")

        # 3. CLICKHOUSE
        f.write(f"\n3. CLICKHOUSE (Database: {CH_CONFIG['database']})\n")
        f.write(f"{subsep}\n")
        f.write("3.1 Motor e Chaves (Índice Esparso MergeTree):\n")
        f.write(df_ch_tables.to_string(index=False) + "\n\n")

        f.write("3.2 Armazenamento e Compressão Colunar:\n")
        cols_ch = ['tabela', 'qtd_partes', 'total_linhas', 'tamanho_bruto', 'tamanho_real_disco', 'taxa_compressao']
        f.write(df_ch_comp[cols_ch].to_string(index=False) + "\n")
        f.write(f"Total bruto (descomprimido): {formatar_bytes(bytes_ch_bruto)} | "
                f"Total real em disco: {formatar_bytes(bytes_ch_disco)}\n\n")

        # 4. RESUMO COMPARATIVO FINAL
        f.write(f"\n{separador}\n")
        f.write("4. QUADRO COMPARATIVO FINAL DE ARMAZENAMENTO\n")
        f.write(f"{separador}\n")
        df_resumo = pd.DataFrame([
            {
                "Ambiente": f"PostgreSQL Normal ({SCHEMA_ORIGEM})",
                "Espaco_Total_Disco": formatar_bytes(bytes_pg_norm),
                "Observacao": "Baseline orientado a linhas sem índices"
            },
            {
                "Ambiente": f"PostgreSQL Otimizado ({SCHEMA_OTIMIZADO})",
                "Espaco_Total_Disco": formatar_bytes(bytes_pg_otim),
                "Observacao": f"Overhead de +{overhead_idx_pct:.2f}% ({formatar_bytes(bytes_pg_otim_idx)} em índices)"
            },
            {
                "Ambiente": "ClickHouse (MergeTree)",
                "Espaco_Total_Disco": formatar_bytes(bytes_ch_disco),
                "Observacao": f"{reducao_ch_vs_pg_norm:.1f}x menor que PG Normal | {reducao_ch_vs_pg_otim:.1f}x menor que PG Otimizado"
            }
        ])
        f.write(df_resumo.to_string(index=False) + "\n")
        f.write(f"{separador}\n")

    print(f"\nRelatório comparativo salvo com sucesso em '{ARQUIVO_RELATORIO}'.")


if __name__ == "__main__":
    pg_engine = create_engine(PG_URI)
    df_tempos = criar_schema_otimizado(pg_engine)
    gerar_relatorio_comparativo(pg_engine, df_tempos)