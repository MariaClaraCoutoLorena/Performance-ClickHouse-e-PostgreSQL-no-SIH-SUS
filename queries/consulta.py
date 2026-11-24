import os
import glob
import time
import psutil
import threading
import itertools
import pandas as pd
from sqlalchemy import create_engine, text
import clickhouse_connect
import gc
import subprocess

monitorando = False
pico_cpu = 0.0
pico_ram = 0.0
media_cpu = 0.0
media_ram = 0.0

SCHEMA_PG_SEM_INDICE = 'public'
SCHEMA_PG_COM_INDICE = 'sih_otimizado'
TOTAL_RODADAS = 90


def monitorar_recursos():
    global monitorando, pico_cpu, pico_ram, media_cpu, media_ram
    pico_cpu = 0.0
    pico_ram = 0.0
    soma_cpu = 0.0
    soma_ram = 0.0
    contagem = 0

    psutil.cpu_percent(interval=None)

    while monitorando:
        time.sleep(0.05)
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent

        if cpu > pico_cpu:
            pico_cpu = cpu
        if ram > pico_ram:
            pico_ram = ram

        soma_cpu += cpu
        soma_ram += ram
        contagem += 1

    if contagem > 0:
        media_cpu = round(soma_cpu / contagem, 2)
        media_ram = round(soma_ram / contagem, 2)


def conectar_bancos():
    pg_engine = create_engine('postgresql+psycopg2://admin:admin@localhost:5432/sih_db')
    ch_client = clickhouse_connect.get_client(
        host='localhost', port=8123, username='admin', password='admin', database='sih_db'
    )
    return pg_engine, ch_client


def ler_queries_da_pasta():
    caminho_pasta = os.path.join(os.path.dirname(__file__), 'sql')
    arquivos_sql = sorted(glob.glob(os.path.join(caminho_pasta, '*.sql')))

    queries = {}
    for arquivo in arquivos_sql:
        nome_query = os.path.basename(arquivo).replace('.sql', '')
        with open(arquivo, 'r', encoding='utf-8') as f:
            queries[nome_query] = f.read().strip()
    return queries


def limpar_caches_por_query(pg_engine, ch_client):
    """Limpa a RAM antes de cada query para garantir testes isolados (Cold Run)"""
    try:
        ch_client.command('SYSTEM DROP MARK CACHE')
        ch_client.command('SYSTEM DROP UNCOMPRESSED CACHE')
        ch_client.command('SYSTEM DROP COMPILED EXPRESSION CACHE')
    except Exception:
        pass

    try:
        pg_engine.dispose()
    except Exception:
        pass

    gc.collect()
    time.sleep(1)


def limpeza_profunda_docker_por_rodada():
    """Derruba toda a infraestrutura para limpar o SSD e a RAM do host"""
    print("\n      [Manutenção] Fim da rodada. Reiniciando Docker para zerar Temp Files e RAM...")

    subprocess.run("docker-compose down", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run("docker system prune -f", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    subprocess.run("docker-compose up -d", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("      [Docker Reiniciado] Aguardando 10s para estabilização dos bancos...")
    time.sleep(10)


def salvar_resultado(resultado, caminho_csv):
    """Salva a métrica no arquivo instantaneamente (Append)"""
    df = pd.DataFrame([resultado])
    arquivo_existe = os.path.isfile(caminho_csv)
    df.to_csv(caminho_csv, mode='a', header=not arquivo_existe, index=False, sep=';', decimal=',')


def executar_query_pg(engine, query, nome_query, rodada, ordem, schema, nome_banco):
    global monitorando, pico_cpu, pico_ram, media_cpu, media_ram
    print(f"  [{ordem}º] {nome_banco} (schema: {schema}) executando {nome_query}...")

    try:
        with engine.connect() as conn:
            # Define o schema antes de iniciar o cronômetro e o monitoramento
            conn.execute(text(f'SET search_path TO "{schema}";'))

            monitorando = True
            thread_mon = threading.Thread(target=monitorar_recursos)
            thread_mon.start()

            t0 = time.time()
            try:
                df_result = pd.read_sql(text(query), conn)
                tempo = time.time() - t0
                linhas = len(df_result)
                status = 'Sucesso'
            finally:
                monitorando = False
                thread_mon.join()

    except Exception as e:
        print(f"      [!] {nome_banco} CRASH/ERRO: {e}")
        print("      [!] Reiniciando o PostgreSQL isoladamente para liberar o SSD...")
        if monitorando:
            monitorando = False
        tempo = 0
        linhas = 0
        status = 'Crash/Falha (Estouro de Recursos)'

        subprocess.run("docker-compose restart postgres", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(10)

    return {
        'rodada': rodada, 'ordem_execucao': ordem, 'banco': nome_banco,
        'query': nome_query, 'latencia_segundos': round(tempo, 4) if status == 'Sucesso' else -1,
        'linhas_retornadas': linhas, 'status': status,
        'pico_cpu_percent': pico_cpu, 'pico_ram_percent': pico_ram,
        'media_cpu_percent': media_cpu, 'media_ram_percent': media_ram
    }


def executar_query_ch(client, query, nome_query, rodada, ordem):
    global monitorando, pico_cpu, pico_ram, media_cpu, media_ram
    print(f"  [{ordem}º] ClickHouse executando {nome_query}...")

    monitorando = True
    thread_mon = threading.Thread(target=monitorar_recursos)
    thread_mon.start()

    t0 = time.time()
    try:
        df_result = client.query_df(query)
        tempo = time.time() - t0
        linhas = len(df_result)
        status = 'Sucesso'
    except Exception as e:
        print(f"      [!] CLICKHOUSE CRASH/ERRO: {e}")
        tempo = 0
        linhas = 0
        status = 'Crash/Falha'
        subprocess.run("docker-compose restart clickhouse", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(8)
    finally:
        monitorando = False
        thread_mon.join()

    return {
        'rodada': rodada, 'ordem_execucao': ordem, 'banco': 'ClickHouse',
        'query': nome_query, 'latencia_segundos': round(tempo, 4) if status == 'Sucesso' else -1,
        'linhas_retornadas': linhas, 'status': status,
        'pico_cpu_percent': pico_cpu, 'pico_ram_percent': pico_ram,
        'media_cpu_percent': media_cpu, 'media_ram_percent': media_ram
    }


def iniciar_testes_leitura():
    queries = ler_queries_da_pasta()
    if not queries:
        print("Nenhuma query encontrada na pasta 'sql'.")
        return

    caminho_csv = os.path.join(os.path.dirname(__file__), 'metricas_consultas_90_rodadas.csv')

    if os.path.exists(caminho_csv):
        os.remove(caminho_csv)

    # Todas as 6 permutações possíveis dos 3 cenários para balancear a ordem de execução
    cenarios = ['pg_sem_indice', 'pg_com_indice', 'clickhouse']
    permutacoes = list(itertools.permutations(cenarios))

    print(f"Carregadas {len(queries)} queries da pasta. Iniciando {TOTAL_RODADAS} rodadas...\n")

    for rodada in range(1, TOTAL_RODADAS + 1):
        ordem_rodada = permutacoes[(rodada - 1) % len(permutacoes)]
        print(f"\n{'='*50}\n INICIANDO RODADA {rodada}/{TOTAL_RODADAS} | Ordem: {' -> '.join(ordem_rodada)}\n{'='*50}")

        pg_engine, ch_client = conectar_bancos()

        for nome_query, query in queries.items():
            print(f"\n-> Testando: {nome_query}")

            for ordem, cenario in enumerate(ordem_rodada, start=1):
                limpar_caches_por_query(pg_engine, ch_client)

                if cenario == 'pg_sem_indice':
                    res = executar_query_pg(
                        pg_engine, query, nome_query, rodada, ordem,
                        schema=SCHEMA_PG_SEM_INDICE, nome_banco='PostgreSQL (Sem Índice)'
                    )
                elif cenario == 'pg_com_indice':
                    res = executar_query_pg(
                        pg_engine, query, nome_query, rodada, ordem,
                        schema=SCHEMA_PG_COM_INDICE, nome_banco='PostgreSQL (Com Índice)'
                    )
                else:
                    res = executar_query_ch(ch_client, query, nome_query, rodada, ordem)

                salvar_resultado(res, caminho_csv)

        limpeza_profunda_docker_por_rodada()


if __name__ == "__main__":
    iniciar_testes_leitura()