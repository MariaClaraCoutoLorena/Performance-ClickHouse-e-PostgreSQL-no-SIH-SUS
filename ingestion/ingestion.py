import os
import time
import psutil
import threading
import pandas as pd
from sqlalchemy import create_engine, text
import clickhouse_connect
import gc

monitorando = False
pico_cpu = 0.0
pico_ram = 0.0
media_cpu = 0.0
media_ram = 0.0

def monitorar_recursos():
    global monitorando, pico_cpu, pico_ram, media_cpu, media_ram
    pico_cpu = 0.0
    pico_ram = 0.0
    soma_cpu = 0.0
    soma_ram = 0.0
    contagem = 0
    
    psutil.cpu_percent(interval=None)
    
    while monitorando:
        time.sleep(0.1)
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        
        if cpu > pico_cpu: pico_cpu = cpu
        if ram > pico_ram: pico_ram = ram
        
        soma_cpu += cpu
        soma_ram += ram
        contagem += 1

    if contagem > 0:
        media_cpu = round(soma_cpu / contagem, 2)
        media_ram = round(soma_ram / contagem, 2)
    else:
        media_cpu = 0.0
        media_ram = 0.0

def conectar_bancos():
    pg_engine = create_engine('postgresql+psycopg2://admin:admin@localhost:5432/sih_db')
    ch_client = clickhouse_connect.get_client(host='localhost', port=8123, username='admin', password='admin', database='sih_db')
    return pg_engine, ch_client

def limpar_tabelas_da_rodada(pg_engine, ch_client):
    print("  -> Limpando tabelas antigas para iniciar a rodada com os bancos zerados...")
    for grupo in ['sih_rd', 'sih_sp']:
        # Limpa PostgreSQL
        with pg_engine.connect() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {grupo};"))
            conn.commit()
        # Limpa ClickHouse
        ch_client.command(f"DROP TABLE IF EXISTS {grupo}")

def executar_postgres(df, grupo, pg_engine, arquivo, linhas, rodada, ordem):
    global monitorando, pico_cpu, pico_ram, media_cpu, media_ram
    
    print(f"  [{ordem}º] PostgreSQL inserindo {linhas:,} registros...".replace(',', '.'))

    monitorando = True
    thread_mon = threading.Thread(target=monitorar_recursos)
    thread_mon.start()        
    
    t0_pg = time.time()
    df.to_sql(grupo, pg_engine, if_exists='append', index=False, chunksize=50000)
    tempo_pg = time.time() - t0_pg
    
    monitorando = False
    thread_mon.join()
    vazao_pg = linhas / tempo_pg
    
    return {
        'rodada': rodada,
        'ordem_execucao': ordem,
        'arquivo': arquivo,
        'banco': 'PostgreSQL',
        'linhas': linhas,
        'latencia_segundos': round(tempo_pg, 2),
        'vazao_linhas_seg': round(vazao_pg, 0),
        'pico_cpu_percent': pico_cpu,
        'pico_ram_percent': pico_ram,
        'media_cpu_percent': media_cpu,
        'media_ram_percent': media_ram
    }

def executar_clickhouse(df, grupo, ch_client, arquivo, linhas, rodada, ordem):
    global monitorando, pico_cpu, pico_ram, media_cpu, media_ram
    
    print(f"  [{ordem}º] ClickHouse inserindo {linhas:,} registros...".replace(',', '.'))
    
    colunas_ch = []
    for coluna, tipo in df.dtypes.items():
        tipo_str = str(tipo).lower()
        if 'int' in tipo_str: tipo_ch = 'Nullable(Int64)'
        elif 'float' in tipo_str: tipo_ch = 'Nullable(Float64)'
        else: tipo_ch = 'Nullable(String)'
        colunas_ch.append(f"`{coluna}` {tipo_ch}")
    definicao_colunas = ",\n".join(colunas_ch)
    
    ch_client.command(f"CREATE TABLE IF NOT EXISTS {grupo} ({definicao_colunas}) ENGINE = MergeTree ORDER BY tuple()")
    
    monitorando = True
    thread_mon = threading.Thread(target=monitorar_recursos)
    thread_mon.start()
    
    t0_ch = time.time()
    ch_client.insert_df(grupo, df)
    tempo_ch = time.time() - t0_ch
    
    monitorando = False
    thread_mon.join()
    vazao_ch = linhas / tempo_ch
    
    return {
        'rodada': rodada,
        'ordem_execucao': ordem,
        'arquivo': arquivo,
        'banco': 'ClickHouse',
        'linhas': linhas,
        'latencia_segundos': round(tempo_ch, 2),
        'vazao_linhas_seg': round(vazao_ch, 0),
        'pico_cpu_percent': pico_cpu,
        'pico_ram_percent': pico_ram,
        'media_cpu_percent': media_cpu,
        'media_ram_percent': media_ram
    }

def iniciar_insercao():
    pg_engine, ch_client = conectar_bancos()
    
    if not os.path.exists('data'):
        print("Pasta 'data' não encontrada.")
        return
        
    arquivos = [f for f in os.listdir('data') if f.endswith('.parquet')]
    arquivos.sort()
    resultados = []
    TOTAL_RODADAS = 30

    print(f"Iniciando {TOTAL_RODADAS} rodadas de testes com {len(arquivos)} arquivos.\n")

    for rodada in range(1, TOTAL_RODADAS + 1):
        print(f"\n{'='*40}")
        print(f" INICIANDO RODADA {rodada}/{TOTAL_RODADAS}")
        print(f"{'='*40}")
        
        # GARANTE QUE A RODADA COMECE COM OS BANCOS ZERADOS
        limpar_tabelas_da_rodada(pg_engine, ch_client)
        
        # Define quem roda primeiro com base em par/ímpar
        pg_primeiro = (rodada % 2 != 0)

        for arquivo in arquivos:
            caminho = os.path.join('data', arquivo)
            grupo = 'sih_rd' if 'RD' in arquivo else 'sih_sp'
            
            print(f"\nLendo arquivo: {arquivo}")
            df = pd.read_parquet(caminho)
            linhas = len(df)
            
            if pg_primeiro:
                # PostgreSQL primeiro, ClickHouse em segundo
                res_pg = executar_postgres(df, grupo, pg_engine, arquivo, linhas, rodada, ordem=1)
                resultados.append(res_pg)
                
                time.sleep(3) # Pausa para resfriamento de CPU/RAM
                
                res_ch = executar_clickhouse(df, grupo, ch_client, arquivo, linhas, rodada, ordem=2)
                resultados.append(res_ch)
            else:
                # ClickHouse primeiro, PostgreSQL em segundo
                res_ch = executar_clickhouse(df, grupo, ch_client, arquivo, linhas, rodada, ordem=1)
                resultados.append(res_ch)
                
                time.sleep(3) # Pausa para resfriamento de CPU/RAM
                
                res_pg = executar_postgres(df, grupo, pg_engine, arquivo, linhas, rodada, ordem=2)
                resultados.append(res_pg)
            
            del df
            gc.collect() # Força a limpeza da memória do Pandas antes do próximo arquivo
            time.sleep(2)

        df_resultados = pd.DataFrame(resultados)
        df_resultados.to_csv('metricas_ingestao_oficial.csv', index=False, sep=';', decimal=',')
        print(f"\n[Rodada {rodada} concluída e salva no CSV]")

    print("\nTodos os testes finalizados com sucesso!")

if __name__ == '__main__':
    iniciar_insercao()