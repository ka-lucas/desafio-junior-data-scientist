import basedosdados as bd
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Configuração do projeto
PROJETO_ID = "datario-454017"

# Função auxiliar para consultas SQL
def executar_consulta(query, projeto_id):
    try:
        return bd.read_sql(query, billing_project_id=projeto_id).to_dataframe()
    except Exception as e:
        print(f"Erro ao executar consulta: {e}")
        return pd.DataFrame()

# Queries SQL para extrair dados
sql_chamados = """
SELECT * FROM `datario.adm_central_atendimento_1746.chamado`
"""

sql_bairros = """
SELECT * FROM `datario.dados_mestres.bairro`
"""

sql_eventos_turisticos = """
SELECT * FROM `datario.turismo_fluxo_visitantes.rede_hoteleira_ocupacao_eventos`
"""

# Carregamento dos dados
print("Iniciando carregamento de dados...")
df_chamados = executar_consulta(sql_chamados, PROJETO_ID)
df_bairros = executar_consulta(sql_bairros, PROJETO_ID)
df_eventos = executar_consulta(sql_eventos_turisticos, PROJETO_ID)
print("Dados carregados com sucesso!")

# Preparação dos dados
df_chamados["data_inicio"] = pd.to_datetime(df_chamados["data_inicio"])

# Constantes úteis
DATA_ANALISE = "2023-04-01"
PERIODO_INICIO = "2022-01-01"
PERIODO_FIM = "2024-12-31"
ID_PERTURBACAO_SOSSEGO = "5071"
EVENTOS_ALVO = ["Réveillon", "Carnaval", "Rock in Rio"]

# ============ ANÁLISES DOS CHAMADOS ============

# 1. Volume de chamados em 01/04/2023
def analisar_volume_diario(data_alvo):
    inicio_dia = pd.to_datetime(data_alvo)
    fim_dia = inicio_dia + timedelta(days=1) - timedelta(seconds=1)
    chamados_dia = df_chamados[(df_chamados["data_inicio"] >= inicio_dia) & 
                               (df_chamados["data_inicio"] <= fim_dia)]
    return len(chamados_dia)

total_chamados_dia = analisar_volume_diario(DATA_ANALISE)
print(f"\n1. Total de chamados em {DATA_ANALISE}: {total_chamados_dia}")

# 2. Tipo de chamado mais frequente
def obter_tipo_mais_frequente(data_alvo):
    chamados_dia = df_chamados[df_chamados["data_inicio"].dt.date == pd.to_datetime(data_alvo).date()]
    
    # Usando value_counts em vez de groupby para variar um pouco o código
    contagem_tipos = chamados_dia["tipo"].value_counts()
    return contagem_tipos.index[0], contagem_tipos.iloc[0]

tipo_mais_comum, qtd_tipo = obter_tipo_mais_frequente(DATA_ANALISE)
print(f"\n2. Tipo de chamado mais comum: {tipo_mais_comum} ({qtd_tipo} ocorrências)")

# 3. Bairros com mais chamados
def top_bairros_por_chamados(data_alvo, n=3):
    # Filtragem por data
    chamados_dia = df_chamados[df_chamados["data_inicio"].dt.date == pd.to_datetime(data_alvo).date()]
    
    # Join com dados de bairros
    dados_combinados = pd.merge(chamados_dia, df_bairros, how="left", on="id_bairro")
    
    # Contagem e ordenação
    contagem_bairros = dados_combinados["bairro_nome"].value_counts().reset_index()
    contagem_bairros.columns = ["bairro", "total_chamados"]
    
    return contagem_bairros.head(n)

top_bairros = top_bairros_por_chamados(DATA_ANALISE)
print(f"\n3. Top 3 bairros com mais chamados:")
for i, row in top_bairros.iterrows():
    print(f"   {i+1}. {row['bairro']} - {row['total_chamados']} chamados")

# 4. Subprefeitura com mais chamados
def subprefeitura_mais_ativa(data_alvo):
    chamados_dia = df_chamados[df_chamados["data_inicio"].dt.date == pd.to_datetime(data_alvo).date()]
    dados_combinados = pd.merge(chamados_dia, df_bairros, how="left", on="id_bairro")
    
    # Somando chamados por subprefeitura
    stats_subprefeitura = dados_combinados.groupby("subprefeitura").agg(
        total_chamados=("id_chamado", "count"),
        tipos_distintos=("tipo", "nunique")
    ).sort_values("total_chamados", ascending=False)
    
    return stats_subprefeitura.index[0], stats_subprefeitura["total_chamados"].iloc[0]

subprefeitura_lider, total_subprefeitura = subprefeitura_mais_ativa(DATA_ANALISE)
print(f"\n4. Subprefeitura com mais chamados: {subprefeitura_lider} ({total_subprefeitura} chamados)")

# 5. Verificação de chamados sem bairro/subprefeitura
def verificar_chamados_sem_localizacao(data_alvo):
    chamados_dia = df_chamados[df_chamados["data_inicio"].dt.date == pd.to_datetime(data_alvo).date()]
    
    # Mescla com dados de bairro
    dados_combinados = pd.merge(chamados_dia, df_bairros, how="left", on="id_bairro")
    
    # Filtra registros sem bairro ou subprefeitura
    chamados_sem_loc = dados_combinados[
        (dados_combinados["bairro_nome"].isna()) | 
        (dados_combinados["subprefeitura"].isna())
    ]
    
    return len(chamados_sem_loc), chamados_sem_loc
    
qtd_sem_loc, dados_sem_loc = verificar_chamados_sem_localizacao(DATA_ANALISE)

if qtd_sem_loc > 0:
    print(f"\n5. Encontrados {qtd_sem_loc} chamados sem bairro/subprefeitura associados")
    # Mostrar primeiras linhas apenas para não sobrecarregar a saída
    print(dados_sem_loc[["id_chamado", "id_bairro", "bairro_nome", "subprefeitura"]].head())
else:
    print("\n5. Todos os chamados possuem bairro e subprefeitura associados")

# 6. Análise de perturbação do sossego no período completo
def analisar_perturbacao_sossego(data_inicio, data_fim, id_subtipo):
    # Filtragem por período e subtipo
    periodo = df_chamados[(df_chamados["data_inicio"] >= data_inicio) & 
                          (df_chamados["data_inicio"] <= data_fim)]
    chamados_subtipo = periodo[periodo["id_subtipo"] == id_subtipo]
    
    # Estatísticas básicas
    stats = {
        "total": len(chamados_subtipo),
        "media_mensal": len(chamados_subtipo) / ((pd.to_datetime(data_fim) - pd.to_datetime(data_inicio)).days / 30),
        "primeiro_chamado": chamados_subtipo["data_inicio"].min(),
        "ultimo_chamado": chamados_subtipo["data_inicio"].max()
    }
    
    return stats, chamados_subtipo

stats_perturbacao, chamados_perturbacao = analisar_perturbacao_sossego(
    PERIODO_INICIO, 
    PERIODO_FIM, 
    ID_PERTURBACAO_SOSSEGO
)

print(f"\n6. Análise de perturbação do sossego ({PERIODO_INICIO} a {PERIODO_FIM}):")
print(f"   Total de chamados: {stats_perturbacao['total']}")
print(f"   Média mensal: {stats_perturbacao['media_mensal']:.2f}")
print(f"   Período dos chamados: {stats_perturbacao['primeiro_chamado']} a {stats_perturbacao['ultimo_chamado']}")

# 7. Chamados de perturbação durante eventos
def chamados_durante_eventos(chamados_df, eventos_df, eventos_lista, id_subtipo):
    # Filtrar apenas eventos de interesse
    eventos_alvos = eventos_df[eventos_df["evento"].isin(eventos_lista)].copy()
    
    # Converter colunas de data
    eventos_alvos["data_inicial"] = pd.to_datetime(eventos_alvos["data_inicial"])
    eventos_alvos["data_final"] = pd.to_datetime(eventos_alvos["data_final"])
    
    # Filtrar chamados por subtipo
    chamados_filtrados = chamados_df[chamados_df["id_subtipo"] == id_subtipo].copy()
    
    # Lista para armazenar resultados
    resultados = []
    
    # Para cada evento, buscar chamados que ocorreram durante ele
    for _, evento in eventos_alvos.iterrows():
        chamados_evento = chamados_filtrados[
            (chamados_filtrados["data_inicio"] >= evento["data_inicial"]) & 
            (chamados_filtrados["data_inicio"] <= evento["data_final"])
        ]
        
        # Adicionar informação do evento aos chamados correspondentes
        if not chamados_evento.empty:
            chamados_evento = chamados_evento.copy()
            chamados_evento["evento"] = evento["evento"]
            chamados_evento["data_inicial_evento"] = evento["data_inicial"]
            chamados_evento["data_final_evento"] = evento["data_final"]
            resultados.append(chamados_evento)
    
    # Combinar resultados se houver algum
    if resultados:
        return pd.concat(resultados)
    else:
        return pd.DataFrame()

chamados_eventos = chamados_durante_eventos(
    df_chamados, 
    df_eventos, 
    EVENTOS_ALVO, 
    ID_PERTURBACAO_SOSSEGO
)

print(f"\n7. Chamados de perturbação de sossego durante eventos:")
if len(chamados_eventos) > 0:
    print(f"   Total: {len(chamados_eventos)} chamados encontrados")
    print(chamados_eventos[["id_chamado", "data_inicio", "evento"]].head())
else:
    print("   Nenhum chamado encontrado durante os eventos especificados")

# 8 e 9. Análise por evento
def analisar_chamados_por_evento(chamados_eventos_df):
    if chamados_eventos_df.empty:
        return pd.DataFrame(), None
    
    # Agrupamento por evento
    resumo = chamados_eventos_df.groupby("evento").agg(
        total_chamados=("id_chamado", "count"),
        data_inicial=("data_inicial_evento", "min"),
        data_final=("data_final_evento", "max")
    )
    
    # Calcular duração de cada evento em dias
    resumo["duracao_dias"] = (resumo["data_final"] - resumo["data_inicial"]).dt.days + 1
    
    # Calcular média diária
    resumo["media_diaria"] = resumo["total_chamados"] / resumo["duracao_dias"]
    
    # Evento com maior média
    evento_maior_media = resumo["media_diaria"].idxmax()
    
    return resumo, evento_maior_media

resumo_eventos, evento_maior_media = analisar_chamados_por_evento(chamados_eventos)

print("\n8. Chamados por evento:")
if not resumo_eventos.empty:
    print(resumo_eventos[["total_chamados", "duracao_dias", "media_diaria"]])
else:
    print("   Sem dados para análise")

if evento_maior_media:
    print(f"\n9. Evento com maior média diária: {evento_maior_media} " +
          f"({resumo_eventos.loc[evento_maior_media, 'media_diaria']:.2f} chamados/dia)")
else:
    print("\n9. Não foi possível determinar o evento com maior média diária")

# 10. Comparação de médias
def comparar_medias(chamados_eventos_df, todos_chamados_df, id_subtipo, periodo_inicio, periodo_fim):
    # Se não há dados de eventos, retorna apenas média do período
    if chamados_eventos_df.empty:
        # Filtrando chamados do período e subtipo
        chamados_periodo = todos_chamados_df[
            (todos_chamados_df["data_inicio"] >= periodo_inicio) & 
            (todos_chamados_df["data_inicio"] <= periodo_fim) &
            (todos_chamados_df["id_subtipo"] == id_subtipo)
        ]
        
        # Calculando média diária para o período inteiro
        dias_periodo = (pd.to_datetime(periodo_fim) - pd.to_datetime(periodo_inicio)).days + 1
        media_periodo = len(chamados_periodo) / dias_periodo
        
        return pd.DataFrame({"media_diaria": [media_periodo]}, index=["Período completo"])
    
    # Criando DataFrame com médias dos eventos
    medias_eventos = resumo_eventos[["media_diaria"]].copy()
    
    # Calculando média do período inteiro
    chamados_periodo = todos_chamados_df[
        (todos_chamados_df["data_inicio"] >= periodo_inicio) & 
        (todos_chamados_df["data_inicio"] <= periodo_fim) &
        (todos_chamados_df["id_subtipo"] == id_subtipo)
    ]
    
    dias_periodo = (pd.to_datetime(periodo_fim) - pd.to_datetime(periodo_inicio)).days + 1
    media_periodo = len(chamados_periodo) / dias_periodo
    
    # Adicionando média do período às médias dos eventos
    medias_eventos.loc["Período completo"] = media_periodo
    
    return medias_eventos.sort_values("media_diaria", ascending=False)

comparativo_medias = comparar_medias(
    chamados_eventos, 
    df_chamados, 
    ID_PERTURBACAO_SOSSEGO, 
    PERIODO_INICIO, 
    PERIODO_FIM
)

print("\n10. Comparativo de médias diárias:")
print(comparativo_medias)

# Conclusão da análise
print("\n============ RESUMO DA ANÁLISE ============")
print(f"Analisamos {total_chamados_dia} chamados do dia {DATA_ANALISE}.")
print(f"O tipo mais comum foi '{tipo_mais_comum}' com {qtd_tipo} ocorrências.")
print(f"Os três bairros com mais chamados foram: {', '.join(top_bairros['bairro'].tolist())}")
print(f"A subprefeitura com mais chamados foi {subprefeitura_lider}.")

if not resumo_eventos.empty:
    print(f"\nNa análise de perturbação do sossego, encontramos {stats_perturbacao['total']} chamados no período.")
    print(f"Durante eventos como {', '.join(EVENTOS_ALVO)}, o evento com maior média diária foi {evento_maior_media}.")
else:
    print(f"\nNão foram encontrados chamados de perturbação do sossego durante os eventos analisados.")