
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Configuração inicial da página
st.set_page_config(page_title="Análise de Devoluções", layout="wide")

# COLUNAS_DEVOLUCAO = ['DATA ', 'Entrada/Saída', 'CLIENTE/FORNECEDOR ',
#        'NOME CLIENTE/FORNECEDOR ', 'NF', 'PRODUTO', 'QTD UN/KG', 'VALOR UNIT.',
#        'VALOR TOTAL', 'MOTIVO DO PROBLEMA', 'RESPONSAVEL POR RESOLVER',
#        'ANDAMENTO', 'NFD', 'PENDENTE', 'SOLUÇÃO', 'FINANCEIRO']

# --- FUNÇÕES DE RELATÓRIO (PADRÃO: Retorna fig, dataframe) ---

def rel_valor_total_devolvido(df):
    df_grouped = df.groupby('DATA NF')['VALOR TOTAL'].sum().reset_index()
    fig = go.Figure(data=go.Scatter(x=df_grouped['DATA NF'], y=df_grouped['VALOR TOTAL'], mode='lines+markers', name='Valor Total'))
    fig.update_layout(title="Valor Total Devolvido ao Longo do Tempo", xaxis_title="Data NF", yaxis_title="Valor (R$)")
    return fig, df_grouped

def rel_tipo_devolucao(df):
    df_grouped = df.groupby(['DATA NF', 'Imp/Qual'])['VALOR TOTAL'].sum().unstack(fill_value=0).reset_index()
    fig = go.Figure()
    for col in df_grouped.columns[1:]:
        fig.add_trace(go.Bar(x=df_grouped['DATA NF'], y=df_grouped[col], name=col))
    fig.update_layout(barmode='stack', title="Tipo de Devolução (Imp/Qual) por Data", xaxis_title="Data NF")
    return fig, df_grouped

def rel_motivo_devolucao(df):
    df_grouped = df.groupby(['DATA NF', 'MOTIVO DO PROBLEMA'])['VALOR TOTAL'].sum().unstack(fill_value=0).reset_index()
    fig = go.Figure()
    for col in df_grouped.columns[1:]:
        fig.add_trace(go.Bar(x=df_grouped['DATA NF'], y=df_grouped[col], name=col))
    fig.update_layout(barmode='stack', title="Motivo da Devolução por Data", xaxis_title="Data NF")
    return fig, df_grouped

def rel_prod_qtd(df):
    df_grouped = df.groupby('PRODUTO')['QTD [UN/KG]'].sum().sort_values(ascending=False).reset_index()
    fig = go.Figure(go.Bar(x=df_grouped['PRODUTO'], y=df_grouped['QTD [UN/KG]'], marker_color='teal'))
    fig.update_layout(title="Produtos x Qtd Devolvida", xaxis_title="Produto", yaxis_title="Quantidade")
    return fig, df_grouped

def rel_prod_valor(df):
    df_grouped = df.groupby('PRODUTO')['VALOR TOTAL'].sum().sort_values(ascending=False).reset_index()
    fig = go.Figure(go.Bar(x=df_grouped['PRODUTO'], y=df_grouped['VALOR TOTAL'], marker_color='indianred'))
    fig.update_layout(title="Produtos x Valor Total Devolvido", xaxis_title="Produto", yaxis_title="Valor (R$)")
    return fig, df_grouped

def rel_cliente_valor(df):
    df_grouped = df.groupby('NOME CLIENTE/FORNECEDOR')['VALOR TOTAL'].sum().sort_values(ascending=False).reset_index()
    fig = go.Figure(go.Bar(x=df_grouped['NOME CLIENTE/FORNECEDOR'], y=df_grouped['VALOR TOTAL'], marker_color='royalblue'))
    fig.update_layout(title="Clientes que mais devolveram (R$)", xaxis_title="Cliente", yaxis_title="Valor (R$)")
    return fig, df_grouped

def rel_cliente_itens(df):
    # Conta o número de linhas (itens) por cliente
    df_grouped = df.groupby('NOME CLIENTE/FORNECEDOR').size().reset_index(name='Qtd Itens')
    df_grouped = df_grouped.sort_values(by='Qtd Itens', ascending=False)
    fig = go.Figure(go.Bar(x=df_grouped['NOME CLIENTE/FORNECEDOR'], y=df_grouped['Qtd Itens'], marker_color='orange'))
    fig.update_layout(title="Clientes que mais devolveram (Qtd de Itens)", xaxis_title="Cliente", yaxis_title="Frequência (Linhas)")
    return fig, df_grouped

def rel_pendente_status(df):
    df_grouped = df.groupby('PENDENTE')['VALOR TOTAL'].sum().reset_index()
    df_grouped['Status'] = df_grouped['PENDENTE'].apply(lambda x: 'Pendente' if x == 'SIM' else 'Devolvida')
    fig = go.Figure(go.Pie(labels=df_grouped['Status'], values=df_grouped['VALOR TOTAL'], hole=.3))
    fig.update_layout(title="Valor Devolvido x Valor Pendente")
    return fig, df_grouped

# --- CARREGAMENTO DE DADOS (EXEMPLO) ---
def load_data():
    # Substitua pelo carregamento do seu arquivo real: pd.read_excel(...) ou query SQL
    # Criando dados fictícios para teste imediato
    hoje = datetime.now()
    data = {
        'DATA NF': pd.to_datetime([hoje, hoje, hoje - pd.Timedelta(days=40), hoje - pd.Timedelta(days=5)]),
        'NOME CLIENTE/FORNECEDOR': ['Cliente A', 'Cliente B', 'Cliente A', 'Cliente C'],
        'VALOR TOTAL': [1500.0, 800.0, 1200.0, 300.0],
        'QTD [UN/KG]': [10, 5, 8, 2],
        'PRODUTO': ['Produto X', 'Produto Y', 'Produto X', 'Produto Z'],
        'Imp/Qual': ['Imp', 'Qual', 'Imp', 'Qual'],
        'MOTIVO DO PROBLEMA': ['Atraso', 'Defeito', 'Atraso', 'Erro'],
        'PENDENTE': ['SIM', 'NÃO', 'NÃO', 'SIM']
    }
    return pd.DataFrame(data)


def carregar_dados(caminho_arquivo, sheet=None):
    df = pd.read_excel(caminho_arquivo, sheet_name=sheet,engine='openpyxl')

    return df
    

st.title(":material/Area_Chart: Dashboard de Devoluções")

arquivos_carregados = st.file_uploader(
    "Escolha os arquivos Excel", 
    type=["xls", "xlsx"], 
)
if not arquivos_carregados:
    st.info("Aguardando o upload de arquivos para iniciar...")
    st.stop()



resp = carregar_dados(arquivos_carregados)

abas_disponiveis = resp.keys()

aba_selecionada = st.selectbox("Selecione uma das abas",abas_disponiveis)

st.markdown("# Resumo das informações")
df = resp[aba_selecionada]
df.columns = df.columns.str.strip()
st.dataframe(df.head())



# --- SEÇÃO 1: RELATÓRIOS TOTAIS (TODO O PERÍODO) ---
st.markdown("# Análise Geral (Todo o Período)")
c1, c2 = st.columns(2)

with c1:
    fig, d_tab = rel_valor_total_devolvido(df)
    st.plotly_chart(fig, width='stretch')
    st.dataframe(d_tab, width='stretch', hide_index=True)

with c2:
    fig, d_tab = rel_tipo_devolucao(df)
    st.plotly_chart(fig, width='stretch')
    st.dataframe(d_tab, width='stretch', hide_index=True)

fig, d_tab = rel_motivo_devolucao(df)
st.plotly_chart(fig, width='stretch')
st.dataframe(d_tab, width='stretch', hide_index=True)

st.markdown("---")

# --- SEÇÃO 2: ANÁLISE DO ÚLTIMO MÊS ---
st.header("🔍 Detalhamento Mensal")

# Input para seleção de mês (Padrão: último mês disponível na base)
meses_disponiveis = df['DATA NF'].dt.to_period('M').unique().astype(str)
ultimo_mes_default = sorted(meses_disponiveis, reverse=True)[0]

mes_selecionado = st.selectbox("Selecione o período para análise detalhada:", 
                               options=sorted(meses_disponiveis, reverse=True),
                               index=0)

# Filtrando o dataframe para o mês selecionado
df_mensal = df[df['DATA NF'].dt.to_period('M').astype(str) == mes_selecionado]

col_a, col_b = st.columns(2)

with col_a:
    # Produtos x Qtd
    f1, d1 = rel_prod_qtd(df_mensal)
    st.plotly_chart(f1, width='stretch')
    st.dataframe(d1, width='stretch', hide_index=True)

    # Clientes x Valor
    f3, d3 = rel_cliente_valor(df_mensal)
    st.plotly_chart(f3, width='stretch')
    st.dataframe(d3, width='stretch', hide_index=True)

with col_b:
    # Produtos x Valor
    f2, d2 = rel_prod_valor(df_mensal)
    st.plotly_chart(f2, width='stretch')
    st.dataframe(d2, width='stretch', hide_index=True)

    # Clientes x Itens
    f4, d4 = rel_cliente_itens(df_mensal)
    st.plotly_chart(f4, width='stretch')
    st.dataframe(d4, width='stretch', hide_index=True)

# Valor Devolvido x Valor Pendente
st.subheader("Situação Financeira das Devoluções")
f5, d5 = rel_pendente_status(df_mensal)
st.plotly_chart(f5, width='stretch')
st.dataframe(d5, width='stretch', hide_index=True)
