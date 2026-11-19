import pandas as pd
from sqlalchemy import create_engine, text
import clickhouse_connect

def gerar_relatorio_estrutural():
    pg_engine = create_engine('postgresql+psycopg2://admin:admin@localhost:5432/sih_db')
    ch_client = clickhouse_connect.get_client(host='localhost', port=8123, username='admin', password='admin', database='sih_db')

    
    with open('relatorio_estrutural.txt', 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO ESTRUTURAL (ANTES DA OTIMIZAÇÃO)\n")

        f.write("POSTGRESQL\n\n")
        
        f.write("1. índices atuais(Mapeamento de Árvore-B)\n")
        query_pg_idx = """
            SELECT tablename as tabela, indexname as nome_indice 
            FROM pg_indexes 
            WHERE tablename IN ('sih_rd', 'sih_sp');
        """
        with pg_engine.connect() as conn:
            df_idx = pd.read_sql(text(query_pg_idx), conn)
            f.write(df_idx.to_string(index=False) + "\n\n")

        f.write("2. tamanho\n")
        query_pg_size = """
            SELECT relname as tabela, 
                   pg_size_pretty(pg_total_relation_size(relid)) as tamanho_no_disco
            FROM pg_catalog.pg_statio_user_tables
            WHERE relname IN ('sih_rd', 'sih_sp');
        """
        with pg_engine.connect() as conn:
            df_size = pd.read_sql(text(query_pg_size), conn)
            f.write(df_size.to_string(index=False) + "\n\n")


        f.write("CLICKHOUSE\n\n")

        f.write("1. Míndices atuais (Índice Esparso)\n")
        query_ch_keys = """
            SELECT name as tabela, engine as motor, sorting_key as chave_ordenacao
            FROM system.tables 
            WHERE name IN ('sih_rd', 'sih_sp');
        """
        df_ch_keys = ch_client.query_df(query_ch_keys)
        f.write(df_ch_keys.to_string(index=False) + "\n\n")

        f.write("2. taxa de compressão (Vetorização)\n")
        query_ch_comp = """
            SELECT table as tabela, 
                   formatReadableSize(sum(data_uncompressed_bytes)) as tamanho_bruto,
                   formatReadableSize(sum(data_compressed_bytes)) as tamanho_real_disco,
                   round(sum(data_uncompressed_bytes) / sum(data_compressed_bytes), 2) as taxa_reducao
            FROM system.parts 
            WHERE table IN ('sih_rd', 'sih_sp') AND active 
            GROUP BY table;
        """
        df_ch_comp = ch_client.query_df(query_ch_comp)
        f.write(df_ch_comp.to_string(index=False) + "\n\n")

    print("\nRelatório gerado com sucesso! Abra o arquivo 'relatorio_estrutural.txt'.")

if __name__ == "__main__":
    gerar_relatorio_estrutural()