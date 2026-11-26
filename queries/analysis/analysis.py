import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import re
from mpl_toolkits.mplot3d import Axes3D
import warnings
warnings.filterwarnings('ignore')

def gerar_relatorio_txt(df_clean, log_outliers, total_original):
    print("Gerando relatório textual completo (relatorio_consultas_e_outliers.txt)...")
    
    with open("relatorio_consultas_e_outliers.txt", "w", encoding="utf-8") as f:
        f.write("="*95 + "\n")
        f.write(" RELATÓRIO ESTATÍSTICO E LIMPEZA DE OUTLIERS - CONSULTAS (SIH-SUS)\n")
        f.write("="*95 + "\n\n")

        # --- SEÇÃO 1: OUTLIERS REMOVIDOS ---
        f.write("1. RELATÓRIO DE REMOÇÃO DE OUTLIERS (MÉTODO IQR POR BANCO E QUERY)\n")
        f.write("-" * 95 + "\n")
        total_removidos = total_original - len(df_clean)
        f.write(f"Total de execuções válidas originais: {total_original} | Mantidas: {len(df_clean)} | Removidas: {total_removidos}\n")

        for banco in df_clean['banco'].unique():
            f.write(f"\n>>> BANCO: {banco}\n")
            itens_banco = [item for item in log_outliers if item['banco'] == banco and item['removidos'] > 0]
            
            if not itens_banco:
                f.write("  Nenhum outlier detectado para este banco.\n")
                continue

            for item in itens_banco:
                f.write(f"  Query {item['query']} ({item['grupo']}): {item['mantidas']}/{item['originais']} rodadas mantidas | Limites IQR: [{item['limite_inf']:.4f}s a {item['limite_sup']:.4f}s]\n")
                for out in item['detalhes_removidos']:
                    f.write(f"    * Rodada {int(out['rodada'])} removida -> Latência: {out['latencia_segundos']:.4f}s | CPU Média: {out['media_cpu_percent']:.2f}%\n")

        # --- SEÇÃO 2: MÉDIAS GERAIS POR BANCO ---
        f.write("\n\n" + "="*95 + "\n")
        f.write("2. RESUMO GERAL POR ARQUITETURA / BANCO (Base Limpa)\n")
        f.write("="*95 + "\n")
        agg_banco = df_clean.groupby('banco')[['latencia_segundos', 'media_cpu_percent', 'pico_ram_percent']].agg(['mean', 'std'])
        
        for banco, row in agg_banco.iterrows():
            f.write(f"\n[{banco}]\n")
            f.write(f" -> Latência Média Global: {row[('latencia_segundos', 'mean')]:.4f}s (± {row[('latencia_segundos', 'std')]:.4f}s)\n")
            f.write(f" -> Consumo Médio CPU:     {row[('media_cpu_percent', 'mean')]:.2f}% (± {row[('media_cpu_percent', 'std')]:.2f}%)\n")
            f.write(f" -> Pico Médio RAM:        {row[('pico_ram_percent', 'mean')]:.2f}% (± {row[('pico_ram_percent', 'std')]:.2f}%)\n")

        # --- SEÇÃO 3: MÉDIAS POR BLOCO DE CONSULTAS ---
        f.write("\n\n" + "="*95 + "\n")
        f.write("3. MÉDIAS POR BLOCO ANALÍTICO E BANCO (Base Limpa)\n")
        f.write("="*95 + "\n")
        agg_grupo = df_clean.groupby(['grupo_query', 'banco'])[['latencia_segundos', 'media_cpu_percent']].agg(['mean', 'std']).reset_index()

        for grupo in sorted(df_clean['grupo_query'].unique()):
            f.write(f"\n--- {grupo} ---\n")
            sub_g = agg_grupo[agg_grupo['grupo_query'] == grupo]
            for _, row in sub_g.iterrows():
                banco_nome = row['banco'].iloc[0] if isinstance(row['banco'], pd.Series) else row['banco']
                lat_m = row[('latencia_segundos', 'mean')]
                lat_s = row[('latencia_segundos', 'std')]
                cpu_m = row[('media_cpu_percent', 'mean')]
                f.write(f" {banco_nome:<28}: Latência = {lat_m:>8.4f}s (± {lat_s:>7.4f}s) | CPU = {cpu_m:>5.2f}%\n")

        # --- SEÇÃO 4: ESTATÍSTICAS DETALHADAS POR QUERY E BANCO ---
        f.write("\n\n" + "="*95 + "\n")
        f.write("4. ESTATÍSTICAS DETALHADAS POR QUERY E BANCO (Média, Mediana, Moda, Desvio Padrão, Min/Max)\n")
        f.write("="*95 + "\n")

        # Ordena as queries numericamente (Q01, Q02, ..., Q44)
        queries_ordenadas = sorted(
            df_clean['query'].unique(),
            key=lambda x: int(re.search(r'\d+', str(x)).group()) if re.search(r'\d+', str(x)) else 999
        )

        bancos_ordem = sorted(df_clean['banco'].unique())

        for grupo in sorted(df_clean['grupo_query'].unique()):
            f.write(f"\n{'#'*95}\n")
            f.write(f" {grupo.upper()}\n")
            f.write(f"{'#'*95}\n")

            queries_do_grupo = [q for q in queries_ordenadas if df_clean[df_clean['query'] == q]['grupo_query'].iloc[0] == grupo]

            for query in queries_do_grupo:
                f.write(f"\n[{query}]\n")
                f.write(f"{'Banco':<27} | {'N':>2} | {'Média(s)':>9} | {'Mediana(s)':>10} | {'Moda(s)':>9} | {'DP(s)':>8} | {'Min(s)':>8} | {'Max(s)':>8} | {'CPU(%)':>6} | {'RAM(%)':>6}\n")
                f.write("-" * 114 + "\n")

                for banco in bancos_ordem:
                    sub = df_clean[(df_clean['query'] == query) & (df_clean['banco'] == banco)]
                    if sub.empty:
                        continue

                    lat = sub['latencia_segundos']
                    n = len(lat)
                    media = lat.mean()
                    mediana = lat.median()
                    dp = lat.std() if n > 1 else 0.0
                    minimo = lat.min()
                    maximo = lat.max()
                    cpu_media = sub['media_cpu_percent'].mean()
                    ram_media = sub['pico_ram_percent'].mean()

                    # Cálculo da Moda (arredondado para 4 casas decimais; se não houver repetição, indica 'Amodal')
                    modas = lat.round(4).mode()
                    if len(modas) == n and n > 1:
                        moda_str = "Amodal"
                    else:
                        moda_str = f"{modas.iloc[0]:.4f}"

                    f.write(
                        f"{banco:<27} | {n:>2} | {media:>9.4f} | {mediana:>10.4f} | {moda_str:>9} | "
                        f"{dp:>8.4f} | {minimo:>8.4f} | {maximo:>8.4f} | {cpu_media:>6.2f} | {ram_media:>6.2f}\n"
                    )

    print("Relatório salvo com sucesso em 'relatorio_consultas_e_outliers.txt'!")


def executar_pipeline_completo():
    # 1. LEITURA DO CSV ÚNICO
    arquivo_csv = "metricas_consultas_90_rodadas.csv"  # <-- Ajuste o nome do arquivo se necessário
    if not os.path.exists(arquivo_csv):
        print(f"Erro: Arquivo '{arquivo_csv}' não encontrado!")
        return

    df_full = pd.read_csv(arquivo_csv, sep=";", decimal=",")
    
    cols_num = ['latencia_segundos', 'pico_cpu_percent', 'pico_ram_percent', 'media_cpu_percent', 'media_ram_percent']
    for col in cols_num:
        if col in df_full.columns and df_full[col].dtype == object:
            df_full[col] = df_full[col].astype(str).str.replace(',', '.').astype(float)

    # Padroniza os nomes dos bancos
    mapa_nomes = {
        'PostgreSQL (Sem Índice)': 'PostgreSQL (Sem Índices)',
        'PostgreSQL (Com Índice)': 'PostgreSQL (Com Índices)'
    }
    df_full['banco'] = df_full['banco'].replace(mapa_nomes)

    # Filtra apenas execuções bem-sucedidas
    df_full = df_full[(df_full['status'] == 'Sucesso') & (df_full['latencia_segundos'] >= 0)].copy()

    # 2. CLASSIFICAÇÃO DOS BLOCOS (Q01 - Q44)
    grupos_dict = {
        (1, 18):  "Bloco 1 - Recuperacao Direta, Consultas Simples e Agregacoes em Tabela Unica",
        (19, 29): "Bloco 2 - Manipulacao de Strings e Auditoria em Tabela Unica",
        (30, 37): "Bloco 3 - Juncoes entre sih_rd e sih_sp (Chave Composta)",
        (38, 44): "Bloco 4 - Subconsultas, CTEs (WITH) e Funcoes de Janela"
    }

    def identificar_grupo(query_name):
        match = re.search(r'\d+', str(query_name))
        if match:
            num = int(match.group())
            for (inicio, fim), nome_grupo in grupos_dict.items():
                if inicio <= num <= fim:
                    return nome_grupo
        return "Bloco 5 - Outros"

    df_full['grupo_query'] = df_full['query'].apply(identificar_grupo)

    # 3. REMOÇÃO DE OUTLIERS (MÉTODO IQR) E COLETA DE LOGS
    total_original = len(df_full)
    df_clean_list = []
    log_outliers = []

    for banco in df_full['banco'].unique():
        for query in df_full['query'].unique():
            subset = df_full[(df_full['banco'] == banco) & (df_full['query'] == query)].copy()
            if subset.empty:
                continue

            grupo_nome = subset['grupo_query'].iloc[0]

            if len(subset) > 3:
                Q1 = subset['latencia_segundos'].quantile(0.25)
                Q3 = subset['latencia_segundos'].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                cond_valido = (subset['latencia_segundos'] >= lower_bound) & (subset['latencia_segundos'] <= upper_bound)
                clean_subset = subset[cond_valido]
                outliers_subset = subset[~cond_valido]
            else:
                clean_subset = subset
                outliers_subset = pd.DataFrame()
                lower_bound, upper_bound = None, None

            df_clean_list.append(clean_subset)
            log_outliers.append({
                'banco': banco,
                'query': query,
                'grupo': grupo_nome,
                'originais': len(subset),
                'mantidas': len(clean_subset),
                'removidos': len(outliers_subset),
                'limite_inf': lower_bound,
                'limite_sup': upper_bound,
                'detalhes_removidos': outliers_subset[['rodada', 'latencia_segundos', 'media_cpu_percent']].to_dict('records')
            })

    df_clean = pd.concat(df_clean_list, ignore_index=True)
    df_clean.to_csv("metricas_consultas_LIMPO.csv", index=False, sep=";", decimal=",")

    # Gera o relatório TXT completo (incluindo a Seção 4 por Query)
    gerar_relatorio_txt(df_clean, log_outliers, total_original)

    # Ordenação por complexidade (baseada no Postgres Sem Índices)
    tempos_pg_cru = df_clean[df_clean['banco'] == 'PostgreSQL (Sem Índices)'].groupby('query')['latencia_segundos'].mean()
    order_complexity = tempos_pg_cru.sort_values().index.tolist()
    for q in df_clean['query'].unique():
        if q not in order_complexity:
            order_complexity.append(q)

    # =========================================================================
    # 4. PREPARAÇÃO DE PASTAS E VISUAL
    # =========================================================================
    sns.set_theme(style="whitegrid")
    pastas = [
        "plotagens_completas/1_latencia_por_grupos",
        "plotagens_completas/2_cpu_por_grupos",
        "plotagens_completas/3_boxplots_outliers_por_grupos",
        "plotagens_completas/4_individuais_por_banco",
        "plotagens_completas/5_visao_global",
        "plotagens_completas/6_heatmap_por_grupos",
        "plotagens_completas/7_3d_por_grupos",
        "plotagens_completas/8_piores_por_grupo"
    ]
    for p in pastas:
        os.makedirs(p, exist_ok=True)
    
    bancos = df_clean['banco'].unique()
    grupos = sorted(df_clean['grupo_query'].unique())

    cores_dict = {
        'ClickHouse': '#1f77b4', 
        'PostgreSQL (Sem Índices)': '#d62728', 
        'PostgreSQL (Com Índices)': '#2ca02c'  
    }

    # =========================================================================
    # 5. GERANDO GRÁFICOS POR BLOCO (Loops)
    # =========================================================================
    print("Gerando gráficos particionados por bloco...")
    
    for grupo in grupos:
        nome_arq = re.sub(r'[^\w\s-]', '', grupo).replace(' ', '_')
        titulo_limpo = grupo
        
        df_c_grupo = df_clean[df_clean['grupo_query'] == grupo]
        df_f_grupo = df_full[df_full['grupo_query'] == grupo]
        if df_c_grupo.empty:
            continue

        order_grupo = [q for q in order_complexity if q in df_c_grupo['query'].unique()]
        largura_fig = max(12, len(order_grupo) * 0.85)

        # 5.1 Latência (Base Limpa)
        plt.figure(figsize=(largura_fig, 6))
        sns.barplot(data=df_c_grupo, x='query', y='latencia_segundos', hue='banco', palette=cores_dict, order=order_grupo, errorbar=None)
        if df_c_grupo['latencia_segundos'].max() > 50:
            plt.yscale('log')
        plt.title(f'Latência (Sem Outliers): {titulo_limpo}', fontsize=14, fontweight='bold')
        plt.ylabel('Latência Média (s)' + (' [LOG]' if df_c_grupo['latencia_segundos'].max() > 50 else ''))
        plt.xticks(rotation=30, ha='right')
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f"plotagens_completas/1_latencia_por_grupos/{nome_arq}.png")
        plt.close()

        # 5.2 CPU (Base Limpa)
        plt.figure(figsize=(largura_fig, 6))
        sns.barplot(data=df_c_grupo, x='query', y='media_cpu_percent', hue='banco', palette=cores_dict, order=order_grupo, errorbar=None)
        plt.title(f'Uso de CPU (Sem Outliers): {titulo_limpo}', fontsize=14, fontweight='bold')
        plt.ylabel('CPU Média (%)')
        plt.xticks(rotation=30, ha='right')
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f"plotagens_completas/2_cpu_por_grupos/{nome_arq}.png")
        plt.close()

        # 5.3 Boxplots (Base Original para visualizar os outliers removidos)
        plt.figure(figsize=(largura_fig + 2, 8))
        sns.boxplot(data=df_f_grupo, x='query', y='latencia_segundos', hue='banco', palette=cores_dict, order=order_grupo, showfliers=True)
        if df_f_grupo['latencia_segundos'].max() > 100:
            plt.yscale('log')
        plt.title(f'Dispersão Original e Outliers: {titulo_limpo}', fontsize=14, fontweight='bold')
        plt.ylabel('Latência (s)')
        plt.xticks(rotation=30, ha='right')
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f"plotagens_completas/3_boxplots_outliers_por_grupos/{nome_arq}.png")
        plt.close()

        # 5.4 Individuais (Base Limpa)
        for banco in bancos:
            pasta_banco = f"plotagens_completas/4_individuais_por_banco/{banco.replace(' ', '_').replace('(', '').replace(')', '')}"
            os.makedirs(pasta_banco, exist_ok=True)
            df_bg = df_c_grupo[df_c_grupo['banco'] == banco]
            if df_bg.empty:
                continue
            
            plt.figure(figsize=(largura_fig, 5))
            ax = sns.barplot(data=df_bg, x='query', y='latencia_segundos', color=cores_dict[banco], order=order_grupo, errorbar=None)
            plt.title(f'[{banco}] {titulo_limpo}', fontsize=13, fontweight='bold')
            plt.ylabel('Latência Média (s)')
            plt.xticks(rotation=30, ha='right')
            
            for p in ax.patches:
                ax.annotate(f"{p.get_height():.2f}s", (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='bottom', fontsize=8, xytext=(0, 4), textcoords='offset points')
            plt.ylim(0, df_bg['latencia_segundos'].max() * 1.2) 
            plt.tight_layout()
            plt.savefig(f"{pasta_banco}/{nome_arq}.png")
            plt.close()

        # 5.5 Heatmap Local (Base Limpa)
        pivot_lat_g = df_c_grupo.pivot_table(index='banco', columns='query', values='latencia_segundos', aggfunc='mean').reindex(columns=order_grupo)
        plt.figure(figsize=(largura_fig, 4.5))
        sns.heatmap(pivot_lat_g, annot=True, fmt=".3f", cmap="YlOrRd", cbar_kws={'label': 'Segundos'}, annot_kws={"size": 8})
        plt.title(f'Heatmap de Latência: {titulo_limpo}', fontsize=13, fontweight='bold')
        plt.xticks(rotation=30, ha='right')
        plt.tight_layout()
        plt.savefig(f"plotagens_completas/6_heatmap_por_grupos/{nome_arq}.png")
        plt.close()

        # 5.6 3D Local (Base Limpa)
        df_m_g = df_c_grupo.groupby(['banco', 'query'])['latencia_segundos'].mean().reset_index()
        b_map = {b: i for i, b in enumerate(bancos)}
        q_map_g = {q: i for i, q in enumerate(order_grupo)}
        
        df_m_g['x_banco'] = df_m_g['banco'].map(b_map)
        df_m_g['y_query'] = df_m_g['query'].map(q_map_g)
        
        fig = plt.figure(figsize=(11, 8))
        ax = fig.add_subplot(111, projection='3d')
        c_3d_g = [cores_dict[b] for b in df_m_g['banco']]

        ax.scatter(df_m_g['x_banco'], df_m_g['y_query'], df_m_g['latencia_segundos'], c=c_3d_g, s=150, alpha=0.8)
        for b_idx in df_m_g['x_banco'].unique():
            sub = df_m_g[df_m_g['x_banco'] == b_idx].sort_values('y_query')
            ax.plot(sub['x_banco'], sub['y_query'], sub['latencia_segundos'], color='gray', alpha=0.5)

        ax.set_xticks(list(b_map.values()))
        ax.set_xticklabels(list(b_map.keys()), rotation=15, ha='right')
        ax.set_yticks(list(q_map_g.values()))
        ax.set_yticklabels(list(q_map_g.keys()), rotation=15, ha='left', fontsize=8)
        ax.set_zlabel('Latência (s)', fontsize=12)
        ax.set_title(f'Visão 3D: {titulo_limpo}', fontsize=13, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f"plotagens_completas/7_3d_por_grupos/{nome_arq}.png")
        plt.close()

    # =========================================================================
    # 6. "AS PIORES DE CADA BLOCO" (Base Limpa)
    # =========================================================================
    print("Gerando gráficos focados nas piores queries de cada bloco...")
    
    idx_piores = df_clean[df_clean['banco'] == 'PostgreSQL (Sem Índices)'].groupby('grupo_query')['latencia_segundos'].idxmax()
    piores_queries = df_clean.loc[idx_piores]['query'].tolist()
    
    df_worst_c = df_clean[df_clean['query'].isin(piores_queries)]
    order_worst = [q for q in order_complexity if q in piores_queries]

    # Barras de Latência
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_worst_c, x='query', y='latencia_segundos', hue='banco', palette=cores_dict, order=order_worst, errorbar=None)
    plt.yscale('log')
    plt.title('Latência: A Query Mais Demorada de Cada Bloco (LOG)', fontsize=15, fontweight='bold')
    plt.ylabel('Latência Média (s) [LOG]')
    plt.xticks(rotation=15, ha='right')
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig("plotagens_completas/8_piores_por_grupo/01_latencia_barras.png")
    plt.close()

    # Barras de CPU
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_worst_c, x='query', y='media_cpu_percent', hue='banco', palette=cores_dict, order=order_worst, errorbar=None)
    plt.title('Uso de CPU: A Query Mais Demorada de Cada Bloco', fontsize=15, fontweight='bold')
    plt.ylabel('CPU Média (%)')
    plt.xticks(rotation=15, ha='right')
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig("plotagens_completas/8_piores_por_grupo/02_cpu_barras.png")
    plt.close()

    # Heatmap
    pivot_w = df_worst_c.pivot_table(index='banco', columns='query', values='latencia_segundos', aggfunc='mean').reindex(columns=order_worst)
    plt.figure(figsize=(12, 4))
    sns.heatmap(pivot_w, annot=True, fmt=".3f", cmap="YlOrRd", cbar_kws={'label': 'Segundos'})
    plt.title('Heatmap: As Piores Queries de Cada Bloco', fontsize=15, fontweight='bold')
    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()
    plt.savefig("plotagens_completas/8_piores_por_grupo/03_heatmap.png")
    plt.close()

    # =========================================================================
    # 7. VISÕES GLOBAIS (Base Limpa)
    # =========================================================================
    print("Gerando visões globais e 3D global...")
    
    pivot_lat = df_clean.pivot_table(index='banco', columns='query', values='latencia_segundos', aggfunc='mean').reindex(columns=order_complexity) 
    plt.figure(figsize=(20, 5))
    sns.heatmap(pivot_lat, annot=False, cmap="YlOrRd", cbar_kws={'label': 'Segundos'})
    plt.title('Heatmap Global: Latência Média por Banco e Query (Q01 - Q44)', fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.tight_layout()
    plt.savefig('plotagens_completas/5_visao_global/01_heatmap_global.png')
    plt.close()

    plt.figure(figsize=(18, 7))
    sns.lineplot(data=df_clean, x='query', y='latencia_segundos', hue='banco', palette=cores_dict, marker='o', sort=False)
    plt.yscale('log')
    plt.title('Curva Global de Complexidade vs Latência (Escala LOG)', fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.tight_layout()
    plt.savefig('plotagens_completas/5_visao_global/02_curva_complexidade_global.png')
    plt.close()

    df_mean = df_clean.groupby(['banco', 'query'])['latencia_segundos'].mean().reset_index()
    banco_map = {b: idx for idx, b in enumerate(bancos)}
    query_map = {q: idx for idx, q in enumerate(order_complexity)}
    
    df_mean['x_banco'] = df_mean['banco'].map(banco_map)
    df_mean['y_query'] = df_mean['query'].map(query_map)
    
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')
    cores_3d = [cores_dict[b] for b in df_mean['banco']]

    ax.scatter(df_mean['x_banco'], df_mean['y_query'], df_mean['latencia_segundos'], c=cores_3d, s=120, alpha=0.8)
    for b_idx in df_mean['x_banco'].unique():
        subset = df_mean[df_mean['x_banco'] == b_idx].sort_values('y_query')
        ax.plot(subset['x_banco'], subset['y_query'], subset['latencia_segundos'], color='gray', alpha=0.4)

    ax.set_xticks(list(banco_map.values()))
    ax.set_xticklabels(list(banco_map.keys()), rotation=15, ha='right')
    ax.set_yticks(list(query_map.values())[::2]) 
    ax.set_yticklabels(list(query_map.keys())[::2], rotation=45, ha='left', fontsize=8)
    ax.set_zlabel('Latência (s)', fontsize=12)
    ax.set_title('Visão 3D Global: Arquitetura vs Complexidade vs Latência', fontsize=18)
    plt.tight_layout()
    plt.savefig('plotagens_completas/5_visao_global/03_grafico_3d_global.png')
    plt.close()

    print("=== SUCESSO! Gráficos gerados em 'plotagens_completas' e relatório salvo em 'relatorio_consultas_e_outliers.txt'. ===")

if __name__ == "__main__":
    executar_pipeline_completo()