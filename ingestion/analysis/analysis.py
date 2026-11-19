import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def gerar_relatorio_estatistico(df):
    print("Gerando relatório textual (informacoes.txt)...")
    
    df['mes'] = df['arquivo'].apply(lambda x: x.split('_')[-1].replace('.parquet', ''))
    
    with open('informacoes.txt', 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write(" RELATÓRIO ESTATÍSTICO - MÉTRICAS DE INGESTÃO (SIH-SUS)\n")
        f.write("="*60 + "\n\n")

        f.write("1. MÉDIAS GERAIS POR BANCO E GRUPO (Com Desvio Padrão)\n")
        f.write("-" * 60 + "\n")
        agg_geral = df.groupby(['banco', 'tipo_grupo_curto'])[['latencia_segundos', 'vazao_linhas_seg', 'media_cpu_percent', 'pico_ram_percent']].agg(['mean', 'std'])
        
        for index, row in agg_geral.iterrows():
            banco, grupo = index
            lat_mean, lat_std = row[('latencia_segundos', 'mean')], row[('latencia_segundos', 'std')]
            vazao_mean, vazao_std = row[('vazao_linhas_seg', 'mean')], row[('vazao_linhas_seg', 'std')]
            cpu_mean, cpu_std = row[('media_cpu_percent', 'mean')], row[('media_cpu_percent', 'std')]
            ram_mean, ram_std = row[('pico_ram_percent', 'mean')], row[('pico_ram_percent', 'std')]
            
            f.write(f"\n[{banco}] - Grupo {grupo}\n")
            f.write(f" -> Latência (segundos): {lat_mean:^8.2f} (± {lat_std:.2f})\n")
            f.write(f" -> Vazão (linhas/seg):  {vazao_mean:^8,.0f} (± {vazao_std:,.0f})\n".replace(',', '.'))
            f.write(f" -> Consumo CPU (%):     {cpu_mean:^8.2f} (± {cpu_std:.2f})\n")
            f.write(f" -> Pico RAM (%):        {ram_mean:^8.2f} (± {ram_std:.2f})\n")
            
        f.write("\n\n" + "="*60 + "\n")
        f.write("2. MÉDIAS DETALHADAS POR MÊS\n")
        f.write("="*60 + "\n")
        
        agg_mes = df.groupby(['banco', 'tipo_grupo_curto', 'mes'])[['latencia_segundos', 'vazao_linhas_seg']].mean().reset_index()
        
        for banco in df['banco'].unique():
            for grupo in ['RD', 'SP']:
                f.write(f"\n--- {banco} | Grupo {grupo} ---\n")
                df_filtrado = agg_mes[(agg_mes['banco'] == banco) & (agg_mes['tipo_grupo_curto'] == grupo)]
                
                for _, row in df_filtrado.iterrows():
                    vazao_fmt = f"{row['vazao_linhas_seg']:,.0f}".replace(',', '.')
                    f.write(f" Mês {row['mes']}: Latência = {row['latencia_segundos']:>6.2f}s | Vazão = {vazao_fmt:>10} linhas/s\n")
                    
    print("Relatório salvo com sucesso!")

def gerar_todos_os_graficos():
    if not os.path.exists('metricas_ingestao_oficial.csv'):
        print("Arquivo metricas_ingestao_oficial.csv não encontrado!")
        return

    df = pd.read_csv('metricas_ingestao_oficial.csv', sep=';', decimal=',')
    os.makedirs('graficos', exist_ok=True)
    sns.set_theme(style="whitegrid")
    cores = {'PostgreSQL': '#3366cc', 'ClickHouse': '#ff9900'}

    df['tipo_grupo_curto'] = df['arquivo'].apply(lambda x: 'RD' if '_RD_' in x else 'SP')
    df['tipo_grupo_desc'] = df['tipo_grupo_curto'].apply(lambda x: 'Grupo RD\n(Menor Volume)' if x == 'RD' else 'Grupo SP\n(Maior Volume)')

    gerar_relatorio_estatistico(df)

    df_rd = df[df['tipo_grupo_curto'] == 'RD']
    df_sp = df[df['tipo_grupo_curto'] == 'SP']
    df_pg = df[df['banco'] == 'PostgreSQL']
    df_ch = df[df['banco'] == 'ClickHouse']

    print("Gerando gráficos visuais...")

    # LATÊNCIA
    plt.figure(figsize=(8, 6))
    sns.boxplot(data=df_rd, x='banco', y='latencia_segundos', palette=cores, showfliers=True)
    plt.title('Distribuição de Latência - Grupo RD', fontsize=14, fontweight='bold', pad=15)
    plt.ylabel('Tempo (Segundos)', fontsize=12)
    plt.xlabel('')
    plt.tight_layout()
    plt.savefig('graficos/01a_latencia_RD.png', dpi=300)
    plt.close()

    plt.figure(figsize=(8, 6))
    sns.boxplot(data=df_sp, x='banco', y='latencia_segundos', palette=cores, showfliers=True)
    plt.title('Distribuição de Latência - Grupo SP', fontsize=14, fontweight='bold', pad=15)
    plt.ylabel('Tempo (Segundos)', fontsize=12)
    plt.xlabel('')
    plt.tight_layout()
    plt.savefig('graficos/01b_latencia_SP.png', dpi=300)
    plt.close()

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle('Desempenho Isolado: PostgreSQL (Latência)', fontsize=16, fontweight='bold')
    sns.boxplot(ax=axes[0], data=df_pg[df_pg['tipo_grupo_curto'] == 'RD'], y='latencia_segundos', color='#3366cc')
    axes[0].set_title('Grupo RD')
    axes[0].set_ylabel('Tempo (Segundos)')
    sns.boxplot(ax=axes[1], data=df_pg[df_pg['tipo_grupo_curto'] == 'SP'], y='latencia_segundos', color='#3366cc')
    axes[1].set_title('Grupo SP')
    axes[1].set_ylabel('Tempo (Segundos)')
    plt.tight_layout()
    plt.savefig('graficos/02a_latencia_isolada_PostgreSQL.png', dpi=300)
    plt.close()

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle('Desempenho Isolado: ClickHouse (Latência)', fontsize=16, fontweight='bold')
    sns.boxplot(ax=axes[0], data=df_ch[df_ch['tipo_grupo_curto'] == 'RD'], y='latencia_segundos', color='#ff9900')
    axes[0].set_title('Grupo RD')
    axes[0].set_ylabel('Tempo (Segundos)')
    sns.boxplot(ax=axes[1], data=df_ch[df_ch['tipo_grupo_curto'] == 'SP'], y='latencia_segundos', color='#ff9900')
    axes[1].set_title('Grupo SP')
    axes[1].set_ylabel('Tempo (Segundos)')
    plt.tight_layout()
    plt.savefig('graficos/02b_latencia_isolada_ClickHouse.png', dpi=300)
    plt.close()

    # VAZÃO E CONSUMO
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Vazão Média de Inserção por Grupo (Linhas por Segundo)', fontsize=16, fontweight='bold')
    sns.barplot(ax=axes[0], data=df_rd, x='banco', y='vazao_linhas_seg', palette=cores, errorbar='sd', capsize=0.1)
    axes[0].set_title('Grupo RD')
    axes[0].set_ylabel('Vazão (Linhas/seg)')
    axes[0].set_xlabel('')
    sns.barplot(ax=axes[1], data=df_sp, x='banco', y='vazao_linhas_seg', palette=cores, errorbar='sd', capsize=0.1)
    axes[1].set_title('Grupo SP')
    axes[1].set_ylabel('Vazão (Linhas/seg)')
    axes[1].set_xlabel('')
    plt.tight_layout()
    plt.savefig('graficos/03_comparativo_vazao.png', dpi=300)
    plt.close()

    plt.figure(figsize=(8, 6))
    sns.barplot(data=df, x='tipo_grupo_desc', y='media_cpu_percent', hue='banco', palette=cores, errorbar='sd', capsize=0.1)
    plt.title('Consumo Médio de Processamento (CPU)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('')
    plt.ylabel('Uso de CPU (%)', fontsize=12)
    plt.legend(title='Banco de Dados')
    plt.tight_layout()
    plt.savefig('graficos/04_comparativo_cpu.png', dpi=300)
    plt.close()

    plt.figure(figsize=(8, 6))
    sns.barplot(data=df, x='tipo_grupo_desc', y='pico_ram_percent', hue='banco', palette=cores, errorbar='sd', capsize=0.1)
    plt.title('Pico de Consumo de Memória RAM', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('')
    plt.ylabel('Uso de RAM do Sistema (%)', fontsize=12)
    plt.legend(title='Banco de Dados')
    plt.tight_layout()
    plt.savefig('graficos/05_comparativo_ram.png', dpi=300)
    plt.close()

    # HISTOGRAMAS
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Distribuição de Frequência da Vazão de Inserção', fontsize=16, fontweight='bold', y=0.98)

    sns.histplot(ax=axes[0, 0], data=df_pg[df_pg['tipo_grupo_curto'] == 'RD'], x='vazao_linhas_seg', color='#3366cc', kde=True, bins=12)
    axes[0, 0].set_title('PostgreSQL - Grupo RD', fontsize=12)
    axes[0, 0].set_xlabel('Vazão (Linhas por Segundo)')
    axes[0, 0].set_ylabel('Frequência')

    sns.histplot(ax=axes[0, 1], data=df_ch[df_ch['tipo_grupo_curto'] == 'RD'], x='vazao_linhas_seg', color='#ff9900', kde=True, bins=12)
    axes[0, 1].set_title('ClickHouse - Grupo RD', fontsize=12)
    axes[0, 1].set_xlabel('Vazão (Linhas por Segundo)')
    axes[0, 1].set_ylabel('Frequência')

    sns.histplot(ax=axes[1, 0], data=df_pg[df_pg['tipo_grupo_curto'] == 'SP'], x='vazao_linhas_seg', color='#3366cc', kde=True, bins=12)
    axes[1, 0].set_title('PostgreSQL - Grupo SP', fontsize=12)
    axes[1, 0].set_xlabel('Vazão (Linhas por Segundo)')
    axes[1, 0].set_ylabel('Frequência')

    sns.histplot(ax=axes[1, 1], data=df_ch[df_ch['tipo_grupo_curto'] == 'SP'], x='vazao_linhas_seg', color='#ff9900', kde=True, bins=12)
    axes[1, 1].set_title('ClickHouse - Grupo SP', fontsize=12)
    axes[1, 1].set_xlabel('Vazão (Linhas por Segundo)')
    axes[1, 1].set_ylabel('Frequência')

    plt.tight_layout(pad=2.0)
    plt.savefig('graficos/06_distribuicao_normalidade_vazao.png', dpi=300)
    plt.close()

    print("Todas as tarefas concluídas (Imagens e Relatório TXT)!")

if __name__ == "__main__":
    gerar_todos_os_graficos()