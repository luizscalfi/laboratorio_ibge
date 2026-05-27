import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Monitoramento: Dengue e Saneamento", layout="wide")

# O Streamlit guarda o resultado da query em cache por 1 hora (ttl=3600) para não sobrecarregar o Supabase
@st.cache_data(ttl=3600)
def carregar_dados():
    # Inicia a conexão com o banco
    conn = st.connection("postgresql", type="sql")
    
    # A query exata que você testou no banco
    query = """
    SELECT 
        t.data_inicio_semana AS "Data de Início",
        t.semana_epidemiologica AS "Semana Epidemiológica",
        l.municipio AS "Município",
        f.casos_notificados AS "Casos de Dengue (Notificados)",
        f.temperatura_media AS "Temperatura Média (°C)",
        f.umidade_media AS "Umidade Média (%)",
        s.rede_adequada_total AS "Domicílios com Rede Adequada",
        (s.fossa_rudimentar + s.esgoto_vala + s.esgoto_rio_lago + s.sem_banheiro) AS "Domicílios em Risco (Sem Rede)"
    FROM Fato_notificacao f
    JOIN Dim_tempo t ON f.id_tempo = t.id_tempo
    JOIN Dim_localidade l ON l.id_localidade = f.id_localidade
    JOIN Dim_Saneamento s ON f.id_saneamento = f.id_saneamento
    ORDER BY t.data_inicio_semana;
    """
    
    # Executa a query e já transforma em um DataFrame do Pandas
    df = conn.query(query)
    df['Data de Início'] = pd.to_datetime(df['Data de Início'])
    return df

df = carregar_dados()

# 3. Cabeçalho e Textos Explicativos (A Documentação exigida pelo professor)
st.title("🦟 Painel Público: Dengue e Saneamento em Bauru")
st.markdown("""
**Bem-vindo ao Explorador de Dados Públicos.**
Esta ferramenta cruza informações do Ministério da Saúpython -m streamlit run "gerar dashboards.py"de e do Censo do IBGE para mostrar como a falta de infraestrutura urbana (como rede de esgoto adequada) impacta diretamente na proliferação do mosquito transmissor da Dengue na nossa cidade.
""")

st.divider()

# 4. Indicadores Principais (KPIs)
total_casos = df['Casos de Dengue (Notificados)'].sum()
media_temp = df['Temperatura Média (°C)'].mean()
domicilios_risco = df['Domicílios em Risco (Sem Rede)'].max() # Pega o valor absoluto do município

col1, col2, col3 = st.columns(3)
col1.metric("Total de Casos Notificados", f"{total_casos:,.0f}".replace(',', '.'))
col2.metric("Temperatura Média Anual", f"{media_temp:.1f} °C")
col3.metric("Domicílios Sem Rede de Esgoto", f"{domicilios_risco:,.0f}".replace(',', '.'))

st.divider()

# 5. Gráficos Interativos (Plotly)
col_grafico1, col_grafico2 = st.columns(2)

with col_grafico1:
    st.subheader("Evolução dos Casos de Dengue")
    # Gráfico de Linha mostrando os picos ao longo do tempo
    fig_linha = px.line(df, x='Data de Início', y='Casos de Dengue (Notificados)', 
                       markers=True, title="Histórico de Notificações")
    st.plotly_chart(fig_linha, use_container_width=True)

with col_grafico2:
    st.subheader("Infraestrutura: O Foco do Problema")
    
    # Capturando os valores absolutos de Bauru (usamos max() porque o número repete nas linhas)
    rede_adequada = df['Domicílios com Rede Adequada'].max()
    risco = df['Domicílios em Risco (Sem Rede)'].max()
    
    # Criando um mini dataframe apenas para o gráfico de pizza
    df_saneamento = pd.DataFrame({
        'Situação': ['Rede Adequada', 'Em Risco (Fossas/Valas)'],
        'Domicílios': [rede_adequada, risco]
    })
    
    # Montando o Gráfico de Pizza com cores de alerta
    fig_pizza = px.pie(
        df_saneamento, 
        values='Domicílios', 
        names='Situação',
        title="Perfil de Saneamento Básico (Bauru)",
        hole=0.4, # Deixa com formato de 'Rosca' que é mais moderno
        color='Situação',
        color_discrete_map={'Rede Adequada':'#636EFA', 'Em Risco (Fossas/Valas)':'#EF553B'}
    )
    
    # Ajustando o texto para aparecer a porcentagem e o valor
    fig_pizza.update_traces(textinfo='percent+label')
    st.plotly_chart(fig_pizza, use_container_width=True)

# 6. Exibição da Base de Dados Aberta (Aba do Excel adaptada para a Web)
st.subheader("Base de Dados Aberta")
st.markdown("Explore os dados brutos filtrando pelas colunas abaixo:")
st.dataframe(df, use_container_width=True)  
