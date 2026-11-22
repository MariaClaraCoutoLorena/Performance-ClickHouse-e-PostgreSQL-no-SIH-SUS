import os
import time
from pysus import list_files
from pysus import sih

def extrair_dados_sih():
    os.makedirs('data', exist_ok=True)

    meses = range(1, 13)
    grupos = ['RD', 'SP']

    for grupo in grupos:
        for mes in meses:
            print(f"Init dowload: {grupo} {mes:02d}")        
            caminho_final = f"data/sih_{grupo}_{mes:02d}.parquet"
            
            if os.path.exists(caminho_final):
                continue
            
            try:
                df = sih(state='SP', year='2024', month=mes, group=grupo)
                df.to_parquet(caminho_final, index=False)
                del df
                    
            except Exception as e:
                print(f"Error: {e}")

            time.sleep(1)

if __name__ == "__main__":
    extrair_dados_sih()