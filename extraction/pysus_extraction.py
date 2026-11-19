import os
import time
from pysus import list_files
from pysus import sih

def extrair_dados_sih():
    os.makedirs('dados', exist_ok=True)
    print("Iniciando conexão com DataSUS")

    meses = range(1, 13)
    grupos = ['RD', 'SP']

    for grupo in grupos:
        for mes in meses:
            print(f"Iniciando dowload do mes {mes} do grupo {grupo}")        
            caminho_final = f"dados/sih_{grupo}_{mes:02d}.parquet"
            
            if os.path.exists(caminho_final):
                continue
            
            try:
                df = sih(state='SP', year='2024', month=mes, group=grupo)
                df.to_parquet(caminho_final, index=False)
                del df
                    
            except Exception as e:
                print(f"Erro ao baixar: {e}")

            time.sleep(1)

    print("Extração concluída com Sucesso!")

if __name__ == "__main__":
    extrair_dados_sih()