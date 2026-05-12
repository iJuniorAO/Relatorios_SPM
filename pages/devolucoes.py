import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Configuração inicial da página
st.set_page_config(page_title="Análise de Devoluções", layout="wide")

# 3 gerais
def rel_geral_devolucao(df):
    """
    param: df
    
    output1: fig (x: %m/%Y, y1='Valor Total (R$)', y2='qtd')
    
    """
    df_temp = df.copy()
    df_temp['MES_ANO'] = df_temp['DATA NF'].dt.strftime('%m/%Y')
    
    # Agrupamos somando o valor e contando as linhas (itens)
    df_grouped = df_temp.groupby('MES_ANO').agg({
        'VALOR TOTAL': 'sum',
        'DATA NF': 'count' # Conta quantas devoluções ocorreram
    }).reset_index()
    
    df_grouped.rename(columns={'DATA NF': 'Qtd Ocorrencia'}, inplace=True)
    
    # Ordenação cronológica
    df_grouped['sort_date'] = pd.to_datetime(df_grouped['MES_ANO'], format='%m/%Y')
    df_grouped = df_grouped.sort_values('sort_date')

    # Criar figura com eixo Y secundário
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Adicionar linha de Valor Total (Eixo Y Principal)
    fig.add_trace(
        go.Scatter(
            x=df_grouped['MES_ANO'], 
            y=df_grouped['VALOR TOTAL'], 
            name="Valor Total (R$)",
            mode='lines+markers+text',
            text=df_grouped['VALOR TOTAL'],
            textposition="top center",
            texttemplate='%{text:.2s}',
            line=dict(color='royalblue', width=3)
        ),
        secondary_y=False,
    )

    # Adicionar linha de Quantidade de Itens (Eixo Y Secundário)
    fig.add_trace(
        go.Scatter(
            x=df_grouped['MES_ANO'], 
            y=df_grouped['Qtd Ocorrencia'], 
            name="Qtd Itens",
            mode='lines+markers+text',
            text=df_grouped['Qtd Ocorrencia'],
            textposition="bottom center",
            line=dict(color='orange', width=3, dash='dot') # Linha pontilhada para diferenciar
        ),
        secondary_y=True,
    )

    # Configurações de layout
    fig.update_layout(
        title="Valor Total vs Qtd de Itens Devolvidos por Mês",
        xaxis_title="Mês/Ano",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Nomear os eixos
    fig.update_yaxes(title_text="Valor Total (R$)", secondary_y=False)
    fig.update_yaxes(title_text="Quantidade de Itens", secondary_y=True)
    
    return fig, df_grouped[['MES_ANO', 'VALOR TOTAL', 'Qtd Ocorrencia']]

def rel_tipo_devolucao(df):
    """
    param: df

    output: 1.Fig - x=%m/%Y y=Qtd erros

    """
    df_temp = df.copy()
    df_temp['MES_ANO'] = df_temp['DATA NF'].dt.strftime('%m/%Y')
    
    # Agrupamento dinâmico
    # df_grouped = df_temp.groupby(['MES_ANO', 'Imp/Qual'])['VALOR TOTAL'].sum().unstack(fill_value=0).reset_index()
    df_grouped = df_temp.groupby(['MES_ANO', 'Imp/Qual'])['VALOR TOTAL'].count().unstack(fill_value=0).reset_index()
    
    # Ordenação
    df_grouped['sort_date'] = pd.to_datetime(df_grouped['MES_ANO'], format='%m/%Y')
    df_grouped = df_grouped.sort_values('sort_date').drop(columns=['sort_date'])

    fig = go.Figure()
    for col in df_grouped.columns[1:]:
        fig.add_trace(
            go.Bar(
                x=df_grouped['MES_ANO'],
                y=df_grouped[col],
                name=col,
                text=df_grouped[col],
                textposition='auto',
                cliponaxis=False
            )
        )
    
    fig.update_layout(
        barmode='stack',
        title="Tipo de Devolução (Imp/Qual) por Mês",
        xaxis_title="Mês/Ano",
        yaxis_title="Quantidade Ocorrência",
    )
    return fig, df_grouped

def rel_valor_tipo_devolucao(df):
    """
    param: df

    output: 1.Fig - x=%m/%Y y=Valor Total (R$)

    """
    df_temp = df.copy()
    df_temp['MES_ANO'] = df_temp['DATA NF'].dt.strftime('%m/%Y')
    
    # Agrupamento dinâmico por soma de valor
    df_grouped = df_temp.groupby(['MES_ANO', 'Imp/Qual'])['VALOR TOTAL'].sum().unstack(fill_value=0).reset_index()
    
    # Ordenação
    df_grouped['sort_date'] = pd.to_datetime(df_grouped['MES_ANO'], format='%m/%Y')
    df_grouped = df_grouped.sort_values('sort_date').drop(columns=['sort_date'])

    fig = go.Figure()
    for col in df_grouped.columns[1:]:
        fig.add_trace(
            go.Bar(
                x=df_grouped['MES_ANO'],
                y=df_grouped[col],
                name=col,
                text=df_grouped[col],
                texttemplate='%{text:.2s}',
                textposition='auto',
                cliponaxis=False
            )
        )
    
    fig.update_layout(
        barmode='stack',
        title="Valor Tipo de Devolução (Imp/Qual) por Mês",
        xaxis_title="Mês/Ano",
        yaxis_title="Valor Total (R$)",
    )
    return fig, df_grouped

# 2 motivos I
def rel_valor_motivo_devolucao(df, remove_qualidade):
    """
    param: df
    
    output: fig x=%m/%Y, y='Valor/Tipo'
    """
    df_temp = df.copy()

    if remove_qualidade:
        df_temp = df_temp[df_temp["Imp/Qual"]!="Qualidade"]

    df_temp['MES_ANO'] = df_temp['DATA NF'].dt.strftime('%m/%Y')

    df_temp["MOTIVO"] = df_temp["MOTIVO DO PROBLEMA"].str.split()
    df_temp["SUBMOTIVO"] = df_temp["MOTIVO"].str[2:].str.join(" ")
    df_temp["MOTIVO"] = df_temp["MOTIVO"].str[0]

    
    # df_grouped = df_temp.groupby(['MES_ANO', 'MOTIVO DO PROBLEMA'])['VALOR TOTAL'].sum().unstack(fill_value=0).reset_index()
    df_grouped = df_temp.groupby(['MES_ANO', 'MOTIVO'])['VALOR TOTAL'].sum().unstack(fill_value=0).reset_index()
    
    # Ordenação
    df_grouped['sort_date'] = pd.to_datetime(df_grouped['MES_ANO'], format='%m/%Y')
    df_grouped = df_grouped.sort_values('sort_date').drop(columns=['sort_date'])

    fig = go.Figure()
    for col in df_grouped.columns[1:]:
        fig.add_trace(go.Bar(x=df_grouped['MES_ANO'], y=df_grouped[col], name=col))
    
    fig.update_layout(barmode='stack', title="Motivo da Devolução por Mês (R$)", xaxis_title="Mês/Ano")
    return fig, df_grouped.set_index('MES_ANO')

def rel_qt_motivo_devolucao(df, remove_qualidade):
    """
    param: df
    output: fig x=%m/%Y y=qtd/Motivo
    """
    df_temp = df.copy()

    if remove_qualidade:
        df_temp = df_temp[df_temp["Imp/Qual"]!="Qualidade"]
    df_temp['MES_ANO'] = df_temp['DATA NF'].dt.strftime('%m/%Y')

    df_temp["MOTIVO"] = df_temp["MOTIVO DO PROBLEMA"].str.split()
    df_temp["SUBMOTIVO"] = df_temp["MOTIVO"].str[2:].str.join(" ")
    df_temp["MOTIVO"] = df_temp["MOTIVO"].str[0]

    
    # df_grouped = df_temp.groupby(['MES_ANO', 'MOTIVO DO PROBLEMA'])['VALOR TOTAL'].sum().unstack(fill_value=0).reset_index()
    df_grouped = df_temp.groupby(['MES_ANO', 'MOTIVO'])['VALOR TOTAL'].count().unstack(fill_value=0).reset_index()
    
    # Ordenação
    df_grouped['sort_date'] = pd.to_datetime(df_grouped['MES_ANO'], format='%m/%Y')
    df_grouped = df_grouped.sort_values('sort_date').drop(columns=['sort_date'])

    fig = go.Figure()
    for col in df_grouped.columns[1:]:
        fig.add_trace(go.Bar(x=df_grouped['MES_ANO'], y=df_grouped[col], name=col))
    
    fig.update_layout(barmode='stack', title="Motivo da Devolução por Mês (qtd)", xaxis_title="Mês/Ano")
    return fig, df_grouped.set_index('MES_ANO')

# 2 motivos II
def rel_valor_motivo_devolucao_II(df):
    """
    param: df
    
    output: fig x=%m/%Y, y='Valor/Tipo'
    """
    df_temp = df.copy()
    df_temp['MES_ANO'] = df_temp['DATA NF'].dt.strftime('%m/%Y')
    
    df_grouped = df_temp.groupby(['MES_ANO', 'MOTIVO DO PROBLEMA'])['VALOR TOTAL'].sum().unstack(fill_value=0).reset_index()
    
    # Ordenação
    df_grouped['sort_date'] = pd.to_datetime(df_grouped['MES_ANO'], format='%m/%Y')
    df_grouped = df_grouped.sort_values('sort_date').drop(columns=['sort_date'])

    fig = go.Figure()
    for col in df_grouped.columns[1:]:
        fig.add_trace(go.Bar(x=df_grouped['MES_ANO'], y=df_grouped[col], name=col))
    
    fig.update_layout(barmode='stack', title="Motivo da Devolução por Mês (R$)", xaxis_title="Mês/Ano")
    return fig, df_grouped.set_index('MES_ANO')

def rel_qt_motivo_devolucao_II(df):
    """
    param: df
    output: fig x=%m/%Y y=qtd/Motivo
    """
    df_temp = df.copy()
    df_temp['MES_ANO'] = df_temp['DATA NF'].dt.strftime('%m/%Y')

    # df_temp["MOTIVO"] = df_temp["MOTIVO DO PROBLEMA"].str.split()
    # df_temp["SUBMOTIVO"] = df_temp["MOTIVO"].str[2:].str.join(" ")
    # df_temp["MOTIVO"] = df_temp["MOTIVO"].str[0]

    
    df_grouped = df_temp.groupby(['MES_ANO', 'MOTIVO DO PROBLEMA'])['VALOR TOTAL'].count().unstack(fill_value=0).reset_index()
    # df_grouped = df_temp.groupby(['MES_ANO', 'MOTIVO'])['VALOR TOTAL'].count().unstack(fill_value=0).reset_index()
    
    # Ordenação
    df_grouped['sort_date'] = pd.to_datetime(df_grouped['MES_ANO'], format='%m/%Y')
    df_grouped = df_grouped.sort_values('sort_date').drop(columns=['sort_date'])

    fig = go.Figure()
    for col in df_grouped.columns[1:]:
        fig.add_trace(go.Bar(x=df_grouped['MES_ANO'], y=df_grouped[col], name=col))
    
    fig.update_layout(barmode='stack', title="Motivo da Devolução por Mês (qtd)", xaxis_title="Mês/Ano")
    return fig, df_grouped.set_index('MES_ANO')

# pendencia financeira
def rel_pendencia_financeira(df):
    """
    param: df
    output: fig1/fig2
    fig1: pendencia qt x SIM/NAO
    fig2: x=%m/%Y y=pendencia SIM
    """
    # --- 1º PREPARAÇÃO DE DADOS (PIZZA - GERAL) ---
    df_pizza = df.groupby('PENDENTE')['VALOR TOTAL'].sum().reset_index()
    df_pizza['Status'] = df_pizza['PENDENTE'].apply(lambda x: 'Pendente' if x == 'SIM' else 'Resolvido')

    # --- 2º PREPARAÇÃO DE DADOS (BARRA - MENSAL APENAS PENDENTES) ---
    df_temp = df.copy()
    df_temp['MES_ANO'] = df_temp['DATA NF'].dt.strftime('%m/%Y')
    
    # Filtramos apenas o que é SIM e agrupamos por mês
    df_pendentes_mes = df_temp[df_temp['PENDENTE'] == 'SIM'].groupby('MES_ANO')['VALOR TOTAL'].sum().reset_index()
    
    # Ordenação cronológica para o gráfico de barras
    df_pendentes_mes['sort_date'] = pd.to_datetime(df_pendentes_mes['MES_ANO'], format='%m/%Y')
    df_pendentes_mes = df_pendentes_mes.sort_values('sort_date').drop(columns=['sort_date'])

    # --- CRIAÇÃO DOS GRÁFICOS LADO A LADO ---
    fig = make_subplots(
        rows=1, cols=2, 
        specs=[[{"type": "pie"}, {"type": "bar"}]],
        subplot_titles=("Pendência Financeira", "Evolução de Pendências por Mês")
    )

    # Adicionando o gráfico de Pizza (Geral)
    fig.add_trace(
        go.Pie(
            labels=df_pizza['Status'], 
            values=df_pizza['VALOR TOTAL'], 
            hole=.3,
            marker=dict(colors=['#636EFA','#EF553B' ]) # Vermelho para Pendente, Azul para Resolvido
        ),
        row=1, col=1
    )

    # Adicionando o gráfico de Barras (Mensal)
    fig.add_trace(
        go.Bar(
            x=df_pendentes_mes['MES_ANO'], 
            y=df_pendentes_mes['VALOR TOTAL'],
            text=df_pendentes_mes['VALOR TOTAL'],
            texttemplate='%{text:.2s}',
            textposition='auto',
            marker_color='indianred',
            name="Pendente"
        ),
        row=1, col=2
    )

    fig.update_layout(
        height=500, 
        showlegend=True,
        title_text="Análise Consolidada de Pendências Financeiras"
    )

    return fig, df_pendentes_mes

# 4 clientes (df_mensal)
def rel_prod_qtd(df):
    df_grouped = df.groupby(['PRODUTO','MOTIVO DO PROBLEMA'])['QTD [UN/KG]'].sum().sort_values(ascending=False).reset_index()
    fig = go.Figure(go.Bar(x=df_grouped['PRODUTO'], y=df_grouped['QTD [UN/KG]'], marker_color='teal'))
    fig.update_layout(title="Produtos x Qtd Devolvida", xaxis_title="Produto", yaxis_title="Quantidade")
    return fig, df_grouped

def rel_prod_valor(df):
    df_grouped = df.groupby(['PRODUTO','MOTIVO DO PROBLEMA'])['VALOR TOTAL'].sum().sort_values(ascending=False).reset_index()
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

# input dados
def carregar_dados(caminho_arquivo, sheet=None):
    with st.spinner('Carrgando arquivos Excel...',show_time=True):
        df = pd.read_excel(caminho_arquivo, sheet_name=sheet,engine='openpyxl')
        return df
# valida df inputado
def valida_df_selecionado(df):
    ocorrencias_com_erro = 0
    def mostra_erro(msg,mostra_df=False):
        st.error(f'Erro ao escolher aba do Excel - {msg}')
        with st.expander('Detalhes'):
            st.markdown('### :red[5 Primeiras linhas]')
            if mostra_df:
                st.dataframe(df.head())            
            st.stop()

    df.columns = df.columns.str.strip()
    if 'DATA NF' not in df.columns:
        if 'DATA' in df.columns:
            df['DATA NF'] = df['DATA']
        else:
            mostra_erro('Não encontrado coluna: "DATA NF" ',True)
    if 'Imp/Qual' not in df.columns:
        mostra_erro('Não encontrado coluna: "Imp/Qual" ',True)

    
    datas_vazias = df[df['DATA NF'].isna()]
    if not datas_vazias.empty:
        ocorrencias_com_erro += len(datas_vazias)
        df = df[df['DATA NF'].notna()].reset_index(drop=True)
        with st.expander(f':red[{len(datas_vazias)} "DATA NF"] em Branco'):
            st.dataframe(datas_vazias)
    
    impqual_vazio = df[df['Imp/Qual'].isna()]
    if not impqual_vazio.empty:
        ocorrencias_com_erro += len(impqual_vazio)
        df = df[df['Imp/Qual'].notna()].reset_index(drop=True)
        with st.expander(f':red[{len(impqual_vazio)} "Improprio/Qualidade"] em Branco'):
            st.dataframe(impqual_vazio)

    resp_vazio = df[df["RESP. LANÇAMENTO"].isna()]
    if not resp_vazio.empty:
        ocorrencias_com_erro += len(resp_vazio)
        df = df[df['RESP. LANÇAMENTO'].notna()].reset_index(drop=True)
        with st.expander(f':red[{len(resp_vazio)} "RESPONSÁVEL LANÇAMENTO"] em Branco'):
            st.dataframe(resp_vazio)

    
    qtd_vazio = df[df['QTD [UN/KG]'].isna()]
    if not qtd_vazio.empty:
        ocorrencias_com_erro += len(qtd_vazio)
        df = df[df['QTD [UN/KG]'].notna()].reset_index(drop=True)
        with st.expander(f':red[{len(qtd_vazio)} "Quantidade UN/KG"] em Branco'):
            st.dataframe(qtd_vazio)
    
    
    vlr_total_vazio = df[df['VALOR TOTAL'].isna()]
    if not vlr_total_vazio.empty:
        ocorrencias_com_erro += len(vlr_total_vazio)
        df = df[df['VALOR TOTAL'].notna()].reset_index(drop=True)
        with st.expander(f':red[{len(vlr_total_vazio)} "VALOR TOTAL"] em Branco'):
            st.dataframe(vlr_total_vazio)
    

    # pendente_vazio = df[df["PENDENTE"].isna()]
    # pendente_vazio

    # loja_vazio = df[df['NOME CLIENTE/FORNECEDOR'].isna()]
    # loja_vazio

    # produto_vazio = df[df["PRODUTO"].isna()]
    # produto_vazio

    # motivo_vazio = df[df["MOTIVO DO PROBLEMA"].isna()]
    # motivo_vazio
    
    # produto_vazio = df[df["PRODUTO"].isna()]
    # produto_vazio

    # df['QTD [UN/KG]'] = pd.to_numeric(df['QTD [UN/KG]'],errors='coerce')

    st.space()
    return df, ocorrencias_com_erro


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
df = resp[aba_selecionada]

df, erros_ocorrencia = valida_df_selecionado(df)

with st.expander('Resumo das informações'):
    st.write(f"Foram carregados :red[{len(df)} ocorrências]")
    st.write(f"Forem encontrados :red[ {erros_ocorrencia} ocorrências com erro ] ")
    st.write(f'Abaixo estão as 5 primeiras linhas da aba :red["{aba_selecionada}"]')
    st.dataframe(df.head())
st.space()


# --- SEÇÃO 1: RELATÓRIOS TOTAIS ---
st.markdown("# Análise Geral")
fig_geral, df_geral = rel_geral_devolucao(df)
st.plotly_chart(fig_geral, width='stretch')
with st.expander(":material/visibility: Mostrar Tabela"):
    st.dataframe(
        df_geral
        .sort_values(by='MES_ANO',ascending=False)
        .style.format({
        'VALOR TOTAL': 'R$ {:.,2f}'.replace(',','x').replace('.',',').replace('x','.'),
        }) 
        , width='stretch',hide_index=True)

c1, c2 = st.columns(2)

with c1:
    fig_tipo_valor, df_tipo_valor = rel_valor_tipo_devolucao(df)
    st.plotly_chart(fig_tipo_valor, width='stretch')
    with st.expander(":material/visibility: Mostrar Tabela"):
        st.dataframe(
            df_tipo_valor
            .sort_values(by='MES_ANO', ascending=False)
            .style.format(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if isinstance(x, (int, float)) else x),
            width='stretch', hide_index=True)
with c2:
    fig_tipo, df_tipo = rel_tipo_devolucao(df)
    st.plotly_chart(fig_tipo, width='stretch')
    with st.expander(":material/visibility: Mostrar Tabela"):
        st.dataframe(
            df_tipo
            .sort_values(by='MES_ANO',ascending=False)
            ,width='stretch', hide_index=True)

    
st.divider()
st.markdown("# Análise por Tipo")
filtro_avaria = st.checkbox('Retirar Problema Qualidade')
col1, col2 = st.columns(2)
with col1:
    fig_valor_devolucao, dev_valor_devolucao = rel_valor_motivo_devolucao(df, filtro_avaria)
    st.plotly_chart(fig_valor_devolucao, width='stretch')
    with st.expander(":material/visibility: Mostrar Tabela"):
        st.dataframe(
            dev_valor_devolucao
            .sort_values(by='MES_ANO',ascending=False)
            .style.format(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
            width='stretch',
            #  hide_index=True
            )

with col2:
    fig_qt_devolucao, dev_qt_devolucao = rel_qt_motivo_devolucao(df, filtro_avaria)
    st.plotly_chart(fig_qt_devolucao, width='stretch')
    with st.expander(":material/visibility: Mostrar Tabela"):
        st.dataframe(
            dev_qt_devolucao
            .sort_values(by='MES_ANO',ascending=False),
            width='stretch',
            #  hide_index=True
            )


st.markdown("# Análise por Tipo Detalhado")
c_1, c_2 = st.columns(2)
with c_1:

    fig_valor_devolucao_II, dev_valor_devolucao_II = rel_valor_motivo_devolucao_II(df)
    st.plotly_chart(fig_valor_devolucao_II, width='stretch')
    with st.expander(":material/visibility: Mostrar Tabela"):
        st.dataframe(
            dev_valor_devolucao_II
            .sort_values(by='MES_ANO',ascending=False)
            .style.format(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
            width='stretch',
            )

with c_2:
    fig_qt_devolucao_II, dev_qt_devolucao_II = rel_qt_motivo_devolucao_II(df)
    st.plotly_chart(fig_qt_devolucao_II, width='stretch')
    with st.expander(":material/visibility: Mostrar Tabela"):
        st.dataframe(
            dev_qt_devolucao_II
            .sort_values(by='MES_ANO',ascending=False),
            width='stretch',
            )
st.divider()



fig_pendencia_financeira, df_pendencia_financeira = rel_pendencia_financeira(df)
st.markdown("# Pendência Financeira")
st.write(f"Valor a pagar total: R$ {df_pendencia_financeira["VALOR TOTAL"].sum():,.2f}".replace(',','x').replace('.',',').replace('x','.'))
st.plotly_chart(fig_pendencia_financeira)
with st.expander(":material/visibility: Mostrar Tabela"):
    st.dataframe(
        df_pendencia_financeira
        .style.format({"VALOR TOTAL": "R$ {:.,2f}".replace(',','x').replace('.',',').replace('x','.')}),
        width='stretch',
        hide_index=True
        )
st.divider()

# --- SEÇÃO 2: ANÁLISE DO ÚLTIMO MÊS ---
st.header(":material/Search: Detalhamento Mensal")

# Input para seleção de mês (Padrão: último mês disponível na base)
meses_disponiveis = df['DATA NF'].dt.to_period('M').unique().astype(str)
# meses_disponiveis = df['DATA NF'].dt.to_period('M').unique()

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
    st.dataframe(
        d3
        .style.format({
        'VALOR TOTAL': 'R$ {:.,2f}'.replace(',','x').replace('.',',').replace('x','.'),
        }) 
        , width='stretch', hide_index=True)

with col_b:
    # Produtos x Valor
    f2, d2 = rel_prod_valor(df_mensal)
    st.plotly_chart(f2, width='stretch')
    st.dataframe(
        d2
        .style.format({
        'VALOR TOTAL': 'R$ {:.,2f}'.replace(',','x').replace('.',',').replace('x','.'),
        }) 
        , width='stretch', hide_index=True)

    # Clientes x Itens
    f4, d4 = rel_cliente_itens(df_mensal)
    st.plotly_chart(f4, width='stretch')
    st.dataframe(d4, width='stretch', hide_index=True)
