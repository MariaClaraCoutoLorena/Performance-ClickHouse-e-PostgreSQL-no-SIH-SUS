from sqlalchemy import create_engine, text

def limpar_indices_antigos(conn):
    query_busca_indices = """
    SELECT indexname, tablename 
    FROM pg_indexes 
    WHERE tablename IN ('sih_rd', 'sih_sp', 'sih_rd_old', 'sih_sp_old') 
      AND indexname NOT LIKE '%_pkey';
    """
    
    indices = conn.execute(text(query_busca_indices)).fetchall()
    for indexname, tablename in indices:
        try:
            conn.execute(text(f'DROP INDEX IF EXISTS "{indexname}" CASCADE;'))
        except Exception:
            pass

def aplicar_particionamento_por_mes(conn, tabela_origem, coluna_mes):

    check_partition = f"""
    SELECT p.partstrat 
    FROM pg_class c 
    JOIN pg_partitioned_table p ON c.oid = p.partrelid 
    WHERE c.relname = '{tabela_origem}';
    """
    is_partitioned = conn.execute(text(check_partition)).fetchone()
    
    if is_partitioned:
        return
    
    tabela_old = f"{tabela_origem}_old"
    
    try:
        conn.execute(text(f'ALTER TABLE "{tabela_origem}" RENAME TO "{tabela_old}";'))
        conn.execute(text(f"""
            CREATE TABLE "{tabela_origem}" (
                LIKE "{tabela_old}" INCLUDING DEFAULTS INCLUDING CONSTRAINTS
            ) PARTITION BY LIST ("{coluna_mes}");
        """))
        
        meses = conn.execute(text(f'SELECT DISTINCT "{coluna_mes}" FROM "{tabela_old}" WHERE "{coluna_mes}" IS NOT NULL;')).fetchall()
        
        for mes in meses:
            mes_val = mes[0]
            nome_particao = f"{tabela_origem}_m{mes_val}"
            conn.execute(text(f"""
                CREATE TABLE "{nome_particao}" 
                PARTITION OF "{tabela_origem}" 
                FOR VALUES IN ('{mes_val}');
            """))
            
        conn.execute(text(f'CREATE TABLE "{tabela_origem}_default" PARTITION OF "{tabela_origem}" DEFAULT;'))
        conn.execute(text(f'INSERT INTO "{tabela_origem}" SELECT * FROM "{tabela_old}";'))
        conn.execute(text(f'DROP TABLE "{tabela_old}";'))
        
    except Exception as e:
        print(f"{str(e)}")
        try: conn.execute(text(f'ALTER TABLE "{tabela_old}" RENAME TO "{tabela_origem}";'))
        except: pass


def otimizar_postgresql():
    engine = create_engine('postgresql+psycopg2://admin:admin@localhost:5432/sih_db')
    
    comandos_indexacao = [
        #SIH_RD
        'CREATE INDEX IF NOT EXISTS idx_pg_rd_naih ON sih_rd ("N_AIH");',
        'CREATE INDEX IF NOT EXISTS idx_pg_rd_cnes ON sih_rd ("CNES");',
        'CREATE INDEX IF NOT EXISTS idx_pg_rd_diag_princ ON sih_rd ("DIAG_PRINC");',

        #Recortes Temporais (BRIN)
        'CREATE INDEX IF NOT EXISTS idx_pg_rd_dtinter ON sih_rd USING BRIN ("DT_INTER");',
        'CREATE INDEX IF NOT EXISTS idx_pg_rd_dtsaida ON sih_rd USING BRIN ("DT_SAIDA");',

        #SIH_SP
        'CREATE INDEX IF NOT EXISTS idx_pg_sp_naih ON sih_sp ("SP_NAIH");',
        'CREATE INDEX IF NOT EXISTS idx_pg_sp_cnes ON sih_sp ("SP_CNES");',
        'CREATE INDEX IF NOT EXISTS idx_pg_sp_procrea ON sih_sp ("SP_PROCREA");',

        #Recortes Temporais (BRIN)
        'CREATE INDEX IF NOT EXISTS idx_pg_sp_dtinter ON sih_sp USING BRIN ("SP_DTINTER");',
        'CREATE INDEX IF NOT EXISTS idx_pg_sp_dtsaida ON sih_sp USING BRIN ("SP_DTSAIDA");'
    ]
    
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        
        limpar_indices_antigos(conn)
        aplicar_particionamento_por_mes(conn, 'sih_rd', 'MES_CMPT')
        aplicar_particionamento_por_mes(conn, 'sih_sp', 'SP_MM')
                
        for sql in comandos_indexacao:
            try:
                conn.execute(text(sql))
                nome_indice = sql.split()[5] 
                print(f"Criado: {nome_indice}")
            except Exception as e:
                print(f"{str(e)}")
        
        try:
             conn.execute(text("ANALYZE sih_rd;"))
             conn.execute(text("ANALYZE sih_sp;"))
             print("ANALYZE concluído")
        except Exception as e:
             print(f"{str(e)}")
             
if __name__ == "__main__":
    otimizar_postgresql()