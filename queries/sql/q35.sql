SELECT LENGTH("SP_PROCREA") as tamanho_codigo, COUNT(*) as qtd 
FROM sih_sp 
GROUP BY LENGTH("SP_PROCREA")