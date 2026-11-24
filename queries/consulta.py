import os
import gc
import glob
import time
import psutil
import threading
import itertools
import subprocess
import pandas as pd
from sqlalchemy import create_engine, text
import clickhouse_connect

monitorando = False
pico_cpu = 0.0
pico_ram = 0.0
media_cpu = 0.0
media_ram = 0.0

PG_URI = 'postgresql+psycopg2://admin:admin@localhost:5432/sih_db'
CH_CONFIG = {
    'host': 'localhost',
    'port': 8123,
    'username': 'admin',
    'password': 'admin',
    'database': 'sih_db'
}

SCHEMA_PG_SEM_INDICE = 'public'
SCHEMA_PG_COM_INDICE = 'sih_otimizado'
TOTAL_RODADAS = 90

# Reinicia o container do banco alvo antes de cada query para zerar shared_buffers/RAM
ISOLAMENTO_ESTRITO_POR_QUERY = True


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


def aguardar_postgres(max_tentativas=10, intervalo=5):
    """Aguarda até o PostgreSQL responder SELECT 1 e retorna uma nova engine."""
    for _ in range(max_tentativas):
        try:
            engine = create_engine(PG_URI, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except Exception:
            time.sleep(intervalo)
    raise RuntimeError("PostgreSQL não respondeu dentro do tempo limite.")


def aguardar_clickhouse(max_tentativas=10, intervalo=5):
    """Aguarda até o ClickHouse responder SELECT 1 e retorna um novo client."""
    for _ in range(max_tentativas):
        try:
            client = clickhouse_connect.get_client(**CH_CONFIG)
            client.command("SELECT 1")
            return client
        except Exception:
            time.sleep(intervalo)
    raise RuntimeError("ClickHouse não respondeu dentro do tempo limite.")


def conectar_bancos():
    pg_engine = aguardar_postgres()
    ch_client = aguardar_clickhouse()
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


def limpar_page_cache_linux():
    """Tenta limpar o Page Cache do kernel Linux dentro da VM do Docker/WSL2."""
    cmd = (
        'docker run --rm --privileged --pid=host alpine '
        'nsenter -t 1 -m -u -n -i sh -c "sync && echo 3 > /proc/sys/vm/drop_caches"'
    )
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def preparar_ambiente_frio_pg(pg_engine):
    """Zera conexões, shared_buffers (via restart) e caches antes de rodar no PostgreSQL."""
    if pg_engine is not None:
        try:
            pg_engine.dispose()
        except Exception:
            pass

    if ISOLAMENTO_ESTRITO_POR_QUERY:
        subprocess.run(
            "docker-compose restart postgres",
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        limpar_page_cache_linux()

    gc.collect()
    return aguardar_postgres()


def preparar_ambiente_frio_ch(ch_client):
    """Derruba caches internos do ClickHouse, reinicia o container e aguarda estabilização."""
    if ch_client is not None:
        for cmd in [
            'SYSTEM DROP MARK CACHE',
            'SYSTEM DROP UNCOMPRESSED CACHE',
            'SYSTEM DROP COMPILED EXPRESSION CACHE',
            'SYSTEM DROP QUERY CACHE'
        ]:
            try:
                ch_client.command(cmd)
            except Exception:
                pass
        try:
            ch_client.close()
        except Exception:
            pass

    if ISOLAMENTO_ESTRITO_POR_QUERY:
        subprocess.run(
            "docker-compose restart clickhouse",
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        limpar_page_cache_linux()

    gc.collect()
    client = aguardar_clickhouse()

    # Garante limpeza pós-boot
    for cmd in [
        'SYSTEM DROP MARK CACHE',
        'SYSTEM DROP UNCOMPRESSED CACHE',
        'SYSTEM DROP COMPILED EXPRESSION CACHE',
        'SYSTEM DROP QUERY CACHE'
    ]:
        try:
            client.command(cmd)
        except Exception:
            pass

    return client


def limpeza_profunda_docker_por_rodada():
    """Derruba e sobe toda a infraestrutura ao fim de cada rodada."""
    print("\n      [Manutenção] Fim da rodada. Reiniciando Docker para zerar Temp Files e RAM...")

    subprocess.run("docker-compose down", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    subprocess.run("docker-compose up -d", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    limpar_page_cache_linux()

    print("      [Docker Reiniciado] Aguardando bancos ficarem prontos...")
    aguardar_postgres()
    aguardar_clickhouse()


def salvar_resultado(resultado, caminho_csv):
    """Salva a métrica no arquivo instantaneamente (Append)."""
    df = pd.DataFrame([resultado])
    arquivo_existe = os.path.isfile(caminho_csv)
    df.to_csv(caminho_csv, mode='a', header=not arquivo_existe, index=False, sep=';', decimal=',')


def executar_query_pg(pg_engine, query, nome_query, rodada, ordem, schema, nome_banco):
    global monitorando, pico_cpu, pico_ram, media_cpu, media_ram

    pg_engine = preparar_ambiente_frio_pg(pg_engine)
    print(f"  [{ordem}º] {nome_banco} (schema: {schema}) executando {nome_query}...")

    try:
        with pg_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("DISCARD ALL;"))
            conn.execute(text(f'SET search_path TO "{schema}";'))

            monitorando = True
            thread_mon = threading.Thread(target=monitorar_recursos)
            thread_mon.start()

            t0 = time.perf_counter()
            try:
                df_result = pd.read_sql(text(query), conn)
                tempo = time.perf_counter() - t0
                linhas = len(df_result)
                status = 'Sucesso'
            finally:
                monitorando = False
                thread_mon.join()

    except Exception as e:
        print(f"      [!] {nome_banco} CRASH/ERRO: {e}")
        print("      [!] Reiniciando o PostgreSQL isoladamente para liberar recursos...")
        if monitorando:
            monitorando = False
        tempo = 0
        linhas = 0
        status = 'Crash/Falha (Estouro de Recursos)'

        subprocess.run(
            "docker-compose restart postgres",
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        pg_engine = aguardar_postgres()

    resultado = {
        'rodada': rodada,
        'ordem_execucao': ordem,
        'banco': nome_banco,
        'query': nome_query,
        'latencia_segundos': round(tempo, 4) if status == 'Sucesso' else -1,
        'linhas_retornadas': linhas,
        'status': status,
        'pico_cpu_percent': pico_cpu,
        'pico_ram_percent': pico_ram,
        'media_cpu_percent': media_cpu,
        'media_ram_percent': media_ram
    }
    return resultado, pg_engine

def executar_query_ch(ch_client, query, nome_query, rodada, ordem):
    global monitorando, pico_cpu, pico_ram, media_cpu, media_ram

    ch_client = preparar_ambiente_frio_ch(ch_client)
    print(f"  [{ordem}º] ClickHouse executando {nome_query}...")

    monitorando = True
    thread_mon = threading.Thread(target=monitorar_recursos)
    thread_mon.start()

    t0 = time.perf_counter()
    try:
        df_result = ch_client.query_df(query)
        tempo = time.perf_counter() - t0
        linhas = len(df_result)
        status = 'Sucesso'
    except Exception as e:
        print(f"      [!] CLICKHOUSE CRASH/ERRO: {e}")
        tempo = 0
        linhas = 0
        status = 'Crash/Falha'
        subprocess.run(
            "docker-compose restart clickhouse",
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        ch_client = aguardar_clickhouse()
    finally:
        monitorando = False
        thread_mon.join()

    resultado = {
        'rodada': rodada,
        'ordem_execucao': ordem,
        'banco': 'ClickHouse',
        'query': nome_query,
        'latencia_segundos': round(tempo, 4) if status == 'Sucesso' else -1,
        'linhas_retornadas': linhas,
        'status': status,
        'pico_cpu_percent': pico_cpu,
        'pico_ram_percent': pico_ram,
        'media_cpu_percent': media_cpu,
        'media_ram_percent': media_ram
    }
    return resultado, ch_client


def iniciar_testes_leitura():
    queries = ler_queries_da_pasta()
    if not queries:
        print("Nenhuma query encontrada na pasta 'sql'.")
        return

    caminho_csv = os.path.join(os.path.dirname(__file__), 'metricas_consultas_90_rodadas.csv')

    cenarios = ['pg_sem_indice', 'pg_com_indice', 'clickhouse']
    permutacoes = list(itertools.permutations(cenarios))

    print(f"Carregadas {len(queries)} queries da pasta 'sql'. Iniciando {TOTAL_RODADAS} rodadas...\n")

    for rodada in range(1, TOTAL_RODADAS + 1):
        ordem_rodada = permutacoes[(rodada - 1) % len(permutacoes)]
        print(f"\n{'='*55}\n INICIANDO RODADA {rodada}/{TOTAL_RODADAS} | Ordem: {' -> '.join(ordem_rodada)}\n{'='*55}")

        pg_engine, ch_client = conectar_bancos()

        for nome_query, query in queries.items():
            print(f"\n-> Testando: {nome_query}")

            for ordem, cenario in enumerate(ordem_rodada, start=1):
                if cenario == 'pg_sem_indice':
                    res, pg_engine = executar_query_pg(
                        pg_engine, query, nome_query, rodada, ordem,
                        schema=SCHEMA_PG_SEM_INDICE, nome_banco='PostgreSQL (Sem Índice)'
                    )
                elif cenario == 'pg_com_indice':
                    res, pg_engine = executar_query_pg(
                        pg_engine, query, nome_query, rodada, ordem,
                        schema=SCHEMA_PG_COM_INDICE, nome_banco='PostgreSQL (Com Índice)'
                    )
                else:
                    res, ch_client = executar_query_ch(
                        ch_client, query, nome_query, rodada, ordem
                    )

                salvar_resultado(res, caminho_csv)

        if pg_engine is not None:
            pg_engine.dispose()
        if ch_client is not None:
            ch_client.close()

        limpeza_profunda_docker_por_rodada()


if __name__ == "__main__":
    iniciar_testes_leitura()