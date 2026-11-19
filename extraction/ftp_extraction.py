import os
import time
import ftplib
import pandas as pd
from pyreaddbc import dbc2dbf
from dbfread import DBF

def extrair_sih():
    os.makedirs('dados', exist_ok=True)
    os.makedirs('temp_dbc', exist_ok=True) 

    grupos = ['RD', 'SP']
    meses = range(1, 13)

    print("Conectando ao FTP do DataSUS")
    ftp = ftplib.FTP("ftp.datasus.gov.br")
    ftp.login()
    ftp.cwd("/dissemin/publicos/SIHSUS/200801_/Dados")

    for grupo in grupos:
        for mes in meses:
            nome_arquivo_ftp = f"{grupo}SP24{mes:02d}.dbc"
            
            caminho_dbc = f"temp_dbc/{nome_arquivo_ftp}"
            caminho_dbf = f"temp_dbc/{nome_arquivo_ftp.replace('.dbc', '.dbf')}"
            caminho_parquet = f"dados/sih_{grupo}_SP_2024_{mes:02d}.parquet"

            if os.path.exists(caminho_parquet):
                
                continue

            print(f"Baixando {nome_arquivo_ftp}")

            try:
                with open(caminho_dbc, 'wb') as f:
                    ftp.retrbinary(f"RETR {nome_arquivo_ftp}", f.write)
                
                dbc2dbf(caminho_dbc, caminho_dbf)

                dbf = DBF(caminho_dbf, encoding='iso-8859-1')
                df = pd.DataFrame(iter(dbf))

                if not df.empty:
                    df.to_parquet(caminho_parquet, index=False)
                else:
                    print("Arquivo vazio")

                if os.path.exists(caminho_dbc): os.remove(caminho_dbc)
                if os.path.exists(caminho_dbf): os.remove(caminho_dbf)
                del df, dbf

            except Exception as e:
                print(f"Erro: {e}")
                
            time.sleep(1)

    ftp.quit()
    
    try:
        import shutil
        shutil.rmtree('temp_dbc')
    except:
        pass

        
if __name__ == "__main__":
    extrair_sih()