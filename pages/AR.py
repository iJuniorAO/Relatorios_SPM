import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Constants
REQUIRED_ROLES = ['administrador', 'usuario']
COMPANY_CODE = 10
PENDING_STATUS = ["NF Pendente"]
OPERATION_TYPES = ['Compra', 'Venda', 'Entrada', 'Saída']
VALID_STATUSES = ["NFe", "NFCe"]
COLUNAS_EXPORT = ["Hora", "Status da Nfe", "NFC-e", "Status da NFC-e", "Status Evento de NFC-e", "Usuário", "MesAno", "Mes_Ref", "Ano_Ref", "Mes_Ano"]

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

def handle_pending_nfs(df):
    """Handle pending NFs by filtering them out and showing a warning."""
    pending_nfs = df[df["Status"].isin(PENDING_STATUS)]
    
    if not pending_nfs.empty:
        st.divider()
        st.error(f":material/Close: [{len(pending_nfs)}] NFs Pendentes")
        with st.expander("Verificar NFs"):
            st.dataframe(pending_nfs)
        st.divider()
    return df

def process_dataframe(df):
    """Process the consolidated dataframe: validate, clean, and categorize."""
    def validate_company_code(df):
        """Validate that all records are for the correct company code."""
        df_wrong_company = df[df["Cód. Empresa"] != COMPANY_CODE]
        if not df_wrong_company.empty:
            st.divider()
            st.error(":material/Close: ERRO - Loja diferente da 010")
            st.dataframe(df_wrong_company)
            st.divider()
            st.stop()
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
    
    validate_company_code(df)
    df = df.drop(columns=COLUMNS_TO_DROP)
    # df = handle_pending_nfs(df)
    df = convert_data_types(df)
    df = add_date_columns(df)
    df = categorize_financial_operations(df)
    return filter_dataframes(df) + (df,)

def criar_balanco_devolucao(df):
    grouped_df = df.groupby(["MesAno", "CategoriaFinanceira"])["Total"].sum().unstack()

    grouped_df = grouped_df[["Devolução Fornecedor", "Devolução Loja"]]
    grouped_df["Devolução Loja"] = -grouped_df["Devolução Loja"]
    grouped_df["Balanço"] = grouped_df.sum(axis=1)

    df_export = df[df["CategoriaFinanceira"].isin(["Devolução Fornecedor", "Devolução Loja"])]
    df_export = df_export.drop(columns=COLUNAS_EXPORT)

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
    fig.update_layout(
        xaxis_title="Mês/Ano",
        yaxis_title="Valor (R$)",
        template="plotly_white",
        showlegend=False,
        xaxis=dict(
            tickformat="%m/%Y",
            dtick="M1",
        ),
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

    return fig, grouped_df, df_export

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
    revenue_df = df[df["CategoriaFinanceira"]=="Venda"]
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

def create_losses_chart(df):

    df['Referência'] = df['Referência'].dt.to_period('M').dt.to_timestamp()
    losses_data = df[df['CategoriaFinanceira'] != 'Devolução Fornecedor'].groupby(['Referência', 'CategoriaFinanceira'])['Total'].sum().reset_index()

    'concat', losses_data
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


st.markdown("# :material/Chart_Data: Apresentação de Resultados")
pegar_manual = st.toggle("Desejo pegar arquivos manualmente", value=True, disabled=True)
st.markdown("Selecione os arquivos `.xls` ou `.xlsx` para unir as linhas em um único DataFrame.")

check_authentication()
perfil = st.session_state.perfil


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

with st.sidebar:
    if st.button("Sair do Sistema"):
        st.session_state.user = None
        st.rerun() 
    st.markdown(f'# :blue[{perfil['nome']}]')
    st.markdown(f"{perfil['role'].title()}")
    
    # Download button for the dataframe
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download DataFrame",
        data=csv,
        file_name='dataframe.csv',
        mime='text/csv'
    )

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

df['Referência'] = df['Referência'].dt.to_period('M').dt.to_timestamp()
df_grouped = df.groupby(['Referência', 'CategoriaFinanceira'])['Total'].sum().reset_index()

# fig_Faturamento, df_Faturamento = create_revenue_chart(df_venda)
fig_Faturamento, df_Faturamento = create_revenue_chart(df_grouped)
st.plotly_chart(fig_Faturamento, width="stretch")

st.divider()
st.markdown("# Evolução Balanço Financeiro")

columns_to_remove = BALANCE_COLUMNS_TO_REMOVE
fig_BalancoFInanceiro, df_EvolucaoFinanceiro = create_financial_balance_evolution(df, columns_to_remove)

st.plotly_chart(fig_BalancoFInanceiro, width='stretch')
with st.expander(":material/Settings: Detalhes"):
    st.markdown(f'### {len(columns_to_remove)} Colunas Ignoradas:')
    for col in columns_to_remove:
        st.write(col)
    st.markdown('### Gráfico em Tabela:')
    st.dataframe(
        df_EvolucaoFinanceiro.style.format(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
        width='stretch'
    )
st.divider()

fig_losses, df_output = create_losses_chart(df_saida)

st.markdown('# Perdas')
st.plotly_chart(fig_losses, width='stretch')

with st.expander(":material/Settings: Detalhes"):
    st.dataframe(df_output)

df_devolucao_loja = df_entrada[df_entrada["CategoriaFinanceira"]=="Devolução Loja"]


st.markdown('# Balanço Devolução')
fig_balanco_dev, df_balanco_dev, df_balanco_dev_2 = criar_balanco_devolucao(df)

st.plotly_chart(fig_balanco_dev, width='stretch')
with st.expander(":material/Settings: Detalhes"):
    st.dataframe(df_balanco_dev)
    st.dataframe(df_balanco_dev_2)
