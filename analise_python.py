import basedosdados as bd
import pandas as pd

project_id = "datario-454017"

# tabelas da consultas 
query_chamado = """
SELECT * FROM `datario.adm_central_atendimento_1746.chamado`
"""
query_bairro = """
SELECT * FROM `datario.dados_mestres.bairro`
"""
query_eventos = """
SELECT * FROM `datario.turismo_fluxo_visitantes.rede_hoteleira_ocupacao_eventos`
"""

df_chamado = bd.read_sql(query_chamado, billing_project_id="datario-454017").to_dataframe()
df_bairro = bd.read_sql(query_bairro,billing_project_id="datario-454017" ).to_dataframe()
df_eventos = bd.read_sql(query_eventos,billing_project_id="datario-454017").to_dataframe()

#1.Quantos chamados foram abertos no dia 01/04/2023?
df_chamado['data_inicio'] = pd.to_datetime(df_chamado['data_inicio'])
df_filtered = df_chamado[(df_chamado['data_inicio'] >= '2023-04-01 00:00:00') & (df_chamado['data_inicio'] <= '2023-04-01 23:59:59')]
total_chamados = df_filtered.shape[0]
print(total_chamados)

#2. Qual o tipo de chamado com mais chamados abertos no dia 01/04/2023?
df_filtered = df_chamado[df_chamado['data_inicio'].dt.date == pd.to_datetime('2023-04-01').date()]
tipo_chamado = df_filtered.groupby('tipo').size().idxmax()
print(tipo_chamado)

#3. Quais os nomes dos 3 bairros que mais tiveram chamados abertos neste dia?
df_filtered = df_chamado[df_chamado['data_inicio'].dt.date == pd.to_datetime('2023-04-01').date()]
df_bairro_merged = pd.merge(df_filtered, df_bairro, how='left', on='id_bairro')
bairro_counts = df_bairro_merged['bairro_nome'].value_counts().head(3)
print(bairro_counts.index.tolist())

#4. Qual o nome da subprefeitura com mais chamados abertos nesse dia?
df_filtered = df_chamado[df_chamado['data_inicio'].dt.date == pd.to_datetime('2023-04-01').date()]
df_bairro_merged = pd.merge(df_filtered, df_bairro, how='left', on='id_bairro')
subprefeitura_counts = df_bairro_merged['subprefeitura'].value_counts().idxmax()
print(subprefeitura_counts)

#5.Existe algum chamado aberto nesse dia que não foi associado a um bairro ou subprefeitura na tabela de bairros?
df_filtered = df_chamado[df_chamado['data_inicio'].dt.date == pd.to_datetime('2023-04-01').date()]
df_bairro_merged = pd.merge(df_filtered, df_bairro, how='left', on='id_bairro')
df_nulls = df_bairro_merged[(df_bairro_merged['bairro_nome'].isnull()) | (df_bairro_merged['subprefeitura'].isnull())]
print(df_nulls)

#6. Quantos chamados de Pertubação do sossego foram abertos nesse período?
df_filtered = df_chamado[(df_chamado['data_inicio'] >= '2022-01-01') & (df_chamado['data_inicio'] <= '2024-12-31')]
perturbacao_chamados = df_filtered[df_filtered['id_subtipo'] == '5071'].shape[0]
print(perturbacao_chamados)

#7. Selecione os chamados com esse subtipo que foram abertos durante os eventos (Reveillonm Carnaval e Rock In Rio)
eventos = ['Réveillon', 'Carnaval', 'Rock in Rio']
df_eventos_filtered = df_eventos[df_eventos['evento'].isin(eventos)]
df_filtered_eventos = df_filtered[df_filtered['id_subtipo'] == '5071']
df_filtered_eventos['evento'] = df_filtered_eventos['data_inicio'].apply(lambda x: 'Réveillon' if x.month == 12 else 'Carnaval' if x.month == 2 else 'Rock in Rio' if x.month == 9 else None)
df_filtered_eventos = df_filtered_eventos[df_filtered_eventos['evento'].isin(eventos)]
print(df_filtered_eventos)

#8. Quantos chamados desse subtipo foram abertos em cada evento?
evento_counts = df_filtered_eventos.groupby('evento').size()
print(evento_counts)

#9. Qual evento teve maior média diária de chamados abertos desse subtipo?
evento_counts = df_filtered_eventos.groupby('evento').apply(lambda x: x.shape[0] / (x['data_inicio'].max() - x['data_inicio'].min()).days).idxmax()
print(evento_counts)

#10. Compare as médias diárias de chamados abertos durante os eventos e a média do período de 01/01/2022 até 31/12/2024
# Média dos eventos
media_eventos = df_filtered_eventos.groupby('evento').apply(lambda x: x.shape[0] / (x['data_inicio'].max() - x['data_inicio'].min()).days)

# Média do período completo
df_periodo = df_chamado[(df_chamado['data_inicio'] >= '2022-01-01') & (df_chamado['data_inicio'] <= '2024-12-31')]
media_periodo = df_periodo[df_periodo['id_subtipo'] == '5071'].shape[0] / (df_periodo['data_inicio'].max() - df_periodo['data_inicio'].min()).days

# Comparando as médias
media_comparacao = media_eventos.append(pd.Series({'Media periodo determinado': media_periodo}))
print(media_comparacao.sort_values(ascending=False))

