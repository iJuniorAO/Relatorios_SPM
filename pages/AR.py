import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Constants
REQUIRED_ROLES = ['administrador', 'usuario']
COMPANY_CODE = 10
PENDING_STATUS = ["NF Pendente"]
OPERATION_TYPES = ['Compra', 'Venda', 'Entrada', 'Saída']
VALID_STATUSES = ["NFe", "NFCe"]

FINANCIAL_CONDITIONS = [
    lambda df: df['Operação (Tipo)'].str.contains('Compra', case=False, na=False),
    lambda df: df['Operação (Tipo)'].str.contains('Venda', case=False, na=False),
    lambda df: df['Operação (Nome)'].str.contains('LOCAÇÃO|PRATELEIRA', case=False, na=False),
    lambda df: df['Operação (Nome)'].str.contains('PERDA|AVARIA|BAIXA DE ESTOQUE|SAIDA DE INVENTÁRIO', case=False, na=False),
    lambda df: df['Operação (Nome)'].str.contains('SAÍDA PARA DESPESA|USO E CONSUMO', case=False, na=False),
    lambda df: (df['Operação (Tipo)'] == 'Saída') & (df['Operação (Nome)'].str.contains('DEVOLUÇÃO|DEVOLUCAO', case=False, na=False)),
    lambda df: (df['Operação (Tipo)'] == 'Entrada') & (df['Operação (Nome)'].str.contains('DEVOLUÇÃO DE VENDA', case=False, na=False)),
    lambda df: (df['Operação (Tipo)'] == 'Saída') & (df['Operação (Nome)'].str.contains('BONIFICAÇAO PARA CLIENTE', case=False, na=False)),
    lambda df: (df['Operação (Tipo)'] == 'Entrada') & (df['Operação (Nome)'].str.contains('DOACAO|BONIFICACAO|BONIFICAÇÃO|ENTRADA DE INVENTÁRIO', case=False, na=False)),
]

FINANCIAL_CATEGORIES = [
    'Compra',
    'Venda',
    'Outros',
    'Perda e Avaria',
    'Uso e Consumo',
    'Devolução Fornecedor',
    'Devolução Loja',
    'Bonificação Loja',
    'Outras Entradas',
]

COLUMNS_TO_DROP = ['Cód. Empresa', 'Emissão', 'Espécie', 'Eventos', 'Serie-SubSerie', 'Situação', 'Cidade']
# Negative categories for balance
NEGATIVE_CATEGORIES = ['Bonificação Loja', 'Compra', 'Devolução Loja', 'Perda e Avaria', 'Uso e Consumo']
BALANCE_COLUMNS_TO_REMOVE = ['Outros', 'Devolução Fornecedor']
LOSS_COLUMNS_TO_REMOVE = ['Compra', 'Venda', 'Outras Entradas', 'Devolução Fornecedor', 'Outros']

st.set_page_config(page_title="Graficos Diretoria", layout='wide')

def check_authentication():
    if "user" not in st.session_state:
        st.session_state.user = None
        st.session_state.session = None

    if (st.session_state.user is None or
        st.session_state.perfil.get('status') != 'ativo' or
        st.session_state.perfil.get('role') not in REQUIRED_ROLES):
        st.markdown("## :material/Close: Area Restrita")
        if st.button('Realizar login'):
            st.switch_page('login.py')
        st.stop()

check_authentication()

def create_consolidated_dataframe(file_list):
    dataframes = []
    with st.spinner('Processando arquivos...'):
        for file in file_list:
            try:
                df_temp = pd.read_excel(file)
                df_temp['Arquivo Origem'] = file.name
                dataframes.append(df_temp)
            except Exception as e:
                st.error(f"Erro ao ler {file.name}: {e}")
                st.stop()

    consolidated_df = pd.concat(dataframes, ignore_index=True)
    consolidated_df["Referência"] = pd.to_datetime(consolidated_df["Referência"], dayfirst=True, errors="coerce")
    return consolidated_df

def validate_company_code(df):
    """Validate that all records are for the correct company code."""
    df_wrong_company = df[df["Cód. Empresa"] != COMPANY_CODE]
    if not df_wrong_company.empty:
        st.divider()
        st.error(":material/Close: ERRO - Loja diferente da 010")
        st.dataframe(df_wrong_company)
        st.divider()
        st.stop()

def handle_pending_nfs(df):
    """Handle pending NFs by filtering them out and showing a warning."""
    pending_nfs = df[df["Status"].isin(PENDING_STATUS)]
    
    if not pending_nfs.empty:
        st.error(f":material/Close: [{len(pending_nfs)}] NFs Pendentes")
        with st.expander("Verificar NFs"):
            st.dataframe(pending_nfs)
        st.divider()
    return df

def convert_data_types(df):
    """Convert data types for specific columns."""
    df["Número"] = pd.to_numeric(df["Número"], errors="raise")
    df["Total"] = df["Total"].astype(str).str.replace(".", "").str.replace(",", ".")
    df["Total"] = pd.to_numeric(df["Total"], errors="raise")
    return df

def add_date_columns(df):
    """Add month and year columns for analysis."""
    df['MesAno'] = df['Referência'].dt.to_period('M').dt.to_timestamp()
    df['Mes_Ref'] = df["Referência"].dt.month
    df['Ano_Ref'] = df["Referência"].dt.year
    df['Mes_Ano'] = df['Referência'].dt.strftime('%y/%b').str.upper()
    return df

def categorize_financial_operations(df):
    conditions = [cond(df) for cond in FINANCIAL_CONDITIONS]
    df['CategoriaFinanceira'] = np.select(conditions, FINANCIAL_CATEGORIES, default='Outros')
    return df

def filter_dataframes(df):
    """Filter the dataframe into operation-specific dataframes."""
    df_purchase = df[df["Operação (Tipo)"] == "Compra"]
    df_sale = df[df["Operação (Tipo)"] == "Venda"]
    df_sale = df_sale[df_sale["Status"].isin(VALID_STATUSES)]
    df_entry = df[df["Operação (Tipo)"] == "Entrada"]
    df_exit = df[df["Operação (Tipo)"] == "Saída"]
    return df_purchase, df_sale, df_entry, df_exit

def process_dataframe(df):
    """Process the consolidated dataframe: validate, clean, and categorize."""
    validate_company_code(df)
    df = df.drop(columns=COLUMNS_TO_DROP)
    # df = handle_pending_nfs(df)
    df = convert_data_types(df)
    df = add_date_columns(df)
    df = categorize_financial_operations(df)
    return filter_dataframes(df) + (df,)

def create_financial_balance_evolution(df, columns_to_remove):
    """Create a financial balance evolution chart."""
    grouped_df = df.groupby(["MesAno", "CategoriaFinanceira"])["Total"].sum().unstack()
    grouped_df = grouped_df.drop(columns=columns_to_remove)

    # Apply negative sign to expense categories
    for category in NEGATIVE_CATEGORIES:
        if category in grouped_df.columns:
            grouped_df[category] = -grouped_df[category]

    grouped_df["Balanço"] = grouped_df.sum(axis=1)

    plot_df = grouped_df.reset_index()


    fig = go.Figure()

    colors = ['#1f77b4' if x >= 0 else '#d62728' for x in plot_df['Balanço']]

    fig.add_trace(
        go.Bar(
            x=plot_df['MesAno'],
            y=plot_df['Balanço'],
            text=plot_df['Balanço'],
            texttemplate='%{y:.2s}',
            textposition='outside',
            marker_color=colors,
            hovertemplate="<b>Mes/Ano:</b> %{x}<br><b>Balanço:</b> R$ %{y:,.2f}<extra></extra>",
        )
    )

    fig.add_hline(
            y=plot_df['Balanço'].mean(),
            line_dash='dot',
            line_color='red',
            line_width=2,
            annotation_text="Média",
            annotation_position='bottom left',
            annotation_font_color='red',
        )

    fig.update_layout(
        xaxis_title="Mês/Ano",
        yaxis_title="Valor (R$)",
        template="plotly_white",
        showlegend=False
    )
    fig.update_xaxes(
        # rangeslider_visible=True,
        rangeselector=dict(
            buttons=[
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1ano", step="year", stepmode="backward"),
                dict(step="all")
            ]
        )
    )

    return fig, grouped_df

def create_revenue_chart(df):
    """Create a revenue evolution chart."""
    # revenue_df = df.set_index('Referência').resample('ME')['Total'].sum().reset_index()
    # revenue_df['Mês/Ano'] = revenue_df['Referência'].dt.strftime('%m/%Y')

    df['Referência'] = df['Referência'].dt.to_period('M').dt.to_timestamp()
    revenue_df = df[df['CategoriaFinanceira'] != 'Devolução Fornecedor'].groupby(['Referência', 'CategoriaFinanceira'])['Total'].sum().reset_index()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=revenue_df['Referência'],
            y=revenue_df['Total'],
            text=revenue_df['Total'],
            mode='lines+markers+text',
            texttemplate='%{text:.2s}',
            textposition='top center',
            fill='tozeroy',
            hovertemplate="<b>Mes/Ano:</b> %{x}<br><b>Faturamento:</b> R$ %{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        xaxis_title="Referência",
        yaxis_title="Valor (R$)",
        template="plotly_white",
        showlegend=False,
        xaxis=dict(
            tickformat="%m/%Y",
            dtick="M1",
        )
    )
    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1ano", step="year", stepmode="backward"),
                dict(step="all")
            ]
        )
    )
    return fig, revenue_df

def create_losses_chart(df, columns_to_remove):

    df['Referência'] = df['Referência'].dt.to_period('M').dt.to_timestamp()
    losses_data = df[~df['CategoriaFinanceira'].isin(columns_to_remove)].groupby(['Referência', 'CategoriaFinanceira'])['Total'].sum().reset_index()

    fig = go.Figure()

    # Create a trace for each category
    colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3']

    for i, category in enumerate(losses_data['CategoriaFinanceira'].unique()):
        filtered_df = losses_data[losses_data['CategoriaFinanceira'] == category]
        color = colors[i]

        fig.add_trace(go.Scatter(
            x=filtered_df['Referência'],
            y=filtered_df['Total'],
            name=category,
            mode='lines+markers+text',
            fill='tozeroy',
            line=dict(color=color),
            text=filtered_df['Total'],
            texttemplate='%{text:.2s}',
            textposition='top center',
            textfont=dict(color=color),
        ))

    fig.update_layout(
        title="Evolução Temporal das Perdas por Categoria",
        xaxis_title="Data de Referência",
        yaxis_title="Prejuízo (R$)",
        template="plotly_white",
        hovermode="x unified",
        legend_title="Categorias",
        xaxis=dict(
            tickformat="%m/%Y",
            dtick="M1",
        )
    )
    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1ano", step="year", stepmode="backward"),
                dict(step="all")
            ]
        )
    )
    return fig, losses_data

def process_store_returns(df, top_n=5):
    """
    Processa dados de devolução e retorna gráficos e dataframes resumidos.
    
    Retorna:
    fig_valor, df_valor, fig_qtd, df_qtd
    """
    
    # --- 1. PROCESSAMENTO PARA VALOR TOTAL ---
    
    top_lojas_valor = df.groupby('Cliente/Fornecedor')['Total'].sum().nlargest(top_n).index
    
    # Filtra e pivota para o gráfico
    df_valor = df[df['Cliente/Fornecedor'].isin(top_lojas_valor)].pivot_table(
        index='MesAno', 
        columns='Cliente/Fornecedor', 
        values='Total', 
        aggfunc='sum'
    ).fillna(0)

    # --- 2. PROCESSAMENTO PARA QUANTIDADE DE NF ---
    top_lojas_qtd = df.groupby('Cliente/Fornecedor')['Total'].count().nlargest(top_n).index
    
    # Filtra e pivota para o gráfico
    df_qtd = df[df['Cliente/Fornecedor'].isin(top_lojas_qtd)].pivot_table(
        index='MesAno', 
        columns='Cliente/Fornecedor', 
        values='Total', 
        aggfunc='count'
    ).fillna(0)

    # --- 3. CRIAÇÃO DAS FIGURAS (Plotly GO) ---
    def gerar_barras(df_pivoted, label_y):
        fig = go.Figure()
        for loja in df_pivoted.columns:
            fig.add_trace(go.Bar(
                x=df_pivoted.index,
                y=df_pivoted[loja],
                name=str(loja)
            ))
        fig.update_layout(
            xaxis=dict(title='Mês/Ano', tickformat='%m/%Y', dtick='M1'),
            yaxis_title=label_y,
            barmode='group',
            hovermode='x unified',
            template='plotly_white'
        )
        return fig


    fig_valor = gerar_barras(df_valor, 'Valor (R$)')
    fig_qtd = gerar_barras(df_qtd, 'Qtd de Devoluções')

    return fig_valor, df_valor, fig_qtd, df_qtd


st.markdown("# :material/Chart_Data: Apresentação de Resultados")
pegar_manual = st.toggle("Desejo pegar arquivos manualmente", value=True, disabled=True)
st.markdown("Selecione os arquivos `.xls` ou `.xlsx` para unir as linhas em um único DataFrame.")

perfil = st.session_state.perfil

with st.sidebar:
    if st.button("Sair do Sistema"):
        st.session_state.user = None
        st.rerun() 
    st.markdown(f'# :blue[{perfil['nome']}]')
    st.markdown(f"{perfil['role'].title()}")

arquivos_carregados = st.file_uploader(
    "Escolha os arquivos Excel", 
    type=["xls", "xlsx"], 
    accept_multiple_files=True,
    disabled=not(pegar_manual)
)

if not arquivos_carregados:
    st.info("Aguardando o upload de arquivos para iniciar...")
    st.stop()

df = create_consolidated_dataframe(arquivos_carregados)
handle_pending_nfs(df)

st.markdown("# Filtro:")

opcoes_status = df['Status'].unique().tolist()
status_selecionados = st.segmented_control(
    'Selecione os Status para análise:',
    selection_mode='multi',
    options=opcoes_status,
    default=['NFe']
)
df = df[df['Status'].isin(status_selecionados)]
df_compra, df_venda, df_entrada, df_saida, df = process_dataframe(df)

st.markdown("# Faturamento")

fig_Faturamento, df_Faturamento = create_revenue_chart(df_venda)
st.plotly_chart(fig_Faturamento, width="stretch")

st.divider()
st.markdown("# Evolução Balanço Mensal")

balance_columns_to_remove = BALANCE_COLUMNS_TO_REMOVE
fig_BalancoFInanceiro, df_EvolucaoFinanceiro = create_financial_balance_evolution(df, balance_columns_to_remove)

st.plotly_chart(fig_BalancoFInanceiro, width='stretch')
with st.expander(":material/Settings: Detalhes"):
    st.markdown(f'### {len(balance_columns_to_remove)} Colunas Ignoradas:')
    for col in balance_columns_to_remove:
        st.write(col)
    st.markdown('### Gráfico em Tabela:')
    st.dataframe(
        df_EvolucaoFinanceiro
            .sort_index(ascending=False)
            .style.format(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
        column_config={
            '_index':st.column_config.DatetimeColumn('MesAno', format="MM/YYYY")
        },
        width='stretch',
    )
st.divider()


fig_losses, df_losses = create_losses_chart(df,LOSS_COLUMNS_TO_REMOVE)

st.markdown('# Perdas Gerais')
st.plotly_chart(fig_losses, width='stretch')

with st.expander(":material/Settings: Detalhes"):
    st.dataframe(
    df_losses
    .sort_index(ascending=False)
    .style.format({
        'Total': 'R$ {:.,2f}'.replace(',','x').replace('.',',').replace('x','.'),
        'Referência': lambda x: x.strftime('%m/%Y')
    })    
)
st.divider()


st.markdown('# Devolução Lojas')


df_store_return = df[df['CategoriaFinanceira']=='Devolução Loja']
number = st.number_input(
    "Digite Quantas lojas devem Mostrar:", value=5, placeholder="Insira um número..."
)
fig_ranking_valor, df_ranking_valor, fig_ranking_qtd, df_ranking_qtd = process_store_returns(df_store_return,number)

st.markdown(f'## TOP :blue[{number}] Maiores Valor Devolvido')
st.plotly_chart(fig_ranking_valor, width='stretch')
with st.expander(":material/Settings: Detalhes"):
    st.dataframe(
        df_ranking_valor
            .sort_index(ascending=False)
            .style.format(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
        column_config={
            '_index':st.column_config.DatetimeColumn('MesAno', format="MM/YYYY")
        },
        width='stretch',
    ) 
st.divider()

st.markdown(f'## TOP :blue[{number}] Maiores Qt Devolvida')
st.plotly_chart(fig_ranking_qtd, width='stretch')
with st.expander(":material/Settings: Detalhes"):
    st.dataframe(
        df_ranking_qtd
            .sort_index(ascending=False),
        column_config={
            '_index':st.column_config.DatetimeColumn('MesAno', format="MM/YYYY")
        },
        width='stretch',
    ) 
st.divider()

