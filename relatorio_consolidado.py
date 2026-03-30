import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


st.set_page_config(page_title="Graficos Diretoria", layout="wide")

if False:      #    Posteriormente usar ferramente de login
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user == None:
        st.markdown("## :material/Close: Area Restrita")
        st.markdown("Realize login")
        st.stop()

def cria_df_consolidado(lista_arquivos):
    lista_df = []
    with st.spinner('Processando arquivos...'):
        for arquivo in lista_arquivos:
            try:
                df_temp = pd.read_excel(arquivo)
                df_temp['Arquivo Origem'] = arquivo.name         
                lista_df.append(df_temp)
            except Exception as e:
                st.error(f"Erro ao ler {arquivo.name}: {e}")
                st.stop()

    df_final = pd.concat(lista_df, ignore_index=True)
    return df_final
def trata_df(df):
    df_loja_010 = df[df["Cód. Empresa"]!=10]
    if not df_loja_010.empty:
        st.divider()        
        st.error(":material/Close: ERRO - Loja diferente da 010")
        df_loja_010[["Status", "Cód. Empresa","Referência","Emissão","Número","Operação (Tipo)","Cliente/Fornecedor","Total","Arquivo Origem"]]
        st.divider()
        st.stop()

    nf_pendente = df[df["Status"]=="NF Pendente"]
    if not nf_pendente.empty:
        st.divider()
        st.error(f":material/Close: [{len(nf_pendente)}] NFs Pendentes")
        df = df[df["Status"]!="NF Pendente"]
        with st.expander("Verificar NFs"):
            nf_pendente[["Status", "Cód. Empresa","Referência","Emissão","Número","Operação (Tipo)","Cliente/Fornecedor","Total","Arquivo Origem"]]
        st.divider()

    df["Número"] = pd.to_numeric(df["Número"],errors="raise")
    df["Total"] = df["Total"].astype(str).str.replace(".","").str.replace(",",".")
    df["Total"] = pd.to_numeric(df["Total"],errors="raise")
    df["Referência"] = pd.to_datetime(df["Referência"],dayfirst=True,errors="coerce")   
    df["Emissão"] = pd.to_datetime(df["Emissão"],dayfirst=True,errors="coerce")   

    
    df_compra = df[df["Operação (Tipo)"]=="Compra"]
    df_venda = df[df["Operação (Tipo)"]=="Venda"]
    df_venda = df_venda[df_venda["Status"].isin(["NFe","NFCe"])]
    df_entrada = df[df["Operação (Tipo)"]=="Entrada"]
    df_saida = df[df["Operação (Tipo)"]=="Saída"]

    return df_compra, df_venda, df_entrada, df_saida, df

META_MENSAL = 4_000_000


st.title(":material/Chart_Data: Consolidador de Arquivos Excel")
pegar_manual = st.toggle("Desejo pegar arquivos manualmente", value=True,disabled=True)
st.markdown("Selecione os arquivos `.xls` ou `.xlsx` para unir as linhas em um único DataFrame.")

arquivos_carregados = st.file_uploader(
    "Escolha os arquivos Excel", 
    type=["xls", "xlsx"], 
    accept_multiple_files=True,
    disabled=not(pegar_manual)
)

if not pegar_manual:
    st.error("Em Desenvolimento - Aguarde...")
    st.stop()
    
if arquivos_carregados:
    df = cria_df_consolidado(arquivos_carregados)

    df_compra, df_venda, df_entrada, df_saida, df = trata_df(df)
    with st.sidebar:
        st.markdown("# Filtros")

        anos = df_compra['Referência'].dt.year.unique()
        ano_selecionado = st.multiselect("Selecione o Ano", options=sorted(anos), default=anos)
    if not ano_selecionado:
        st.info("Selecione o ano que deseja filtrar")
        st.stop()

    if False:

        df_compra = df_compra[df_compra['Referência'].dt.year.isin(ano_selecionado)]
        df_venda = df_venda[df_venda['Referência'].dt.year.isin(ano_selecionado)]

        df_compra = df_compra[df_compra["Status"].isin(["NFe","NFCe"])]
        df_venda = df_venda[df_venda["Status"].isin(["NFe","NFCe"])]

        total_vendas = df_venda['Total'].sum()
        ticket_medio_venda = df_venda['Total'].mean()
        qtd_clientes = df_venda['Cliente/Fornecedor'].nunique()

        total_compras = df_compra['Total'].sum()
        ticket_medio_compra = df_compra['Total'].mean()
        qtd_fornecedor = df_compra['Cliente/Fornecedor'].nunique()


    st.markdown("# Compra/Venda")
    periodo_compra_venda = df_venda["Referência"].dt.to_period("M").unique().astype(str).tolist()
    periodo_compra_venda_select = st.select_slider(
        "Selecione o Mês da Compra/Venda",
        options=periodo_compra_venda,
        value=periodo_compra_venda[-1]
    )
    periodo_compra_venda_select = pd.to_datetime(periodo_compra_venda_select)
    compra_venda_mes = periodo_compra_venda_select.month
    compra_venda_ano = periodo_compra_venda_select.year

    df_compra_venda = df[
        (df['Referência'].dt.month == compra_venda_mes) & 
        (df['Referência'].dt.year == compra_venda_ano)]
    
    df_compra_venda = df_compra_venda[df_compra_venda["Status"].isin(["NFe","NFCe"])]
    df_compra_venda = df_compra_venda.groupby("Operação (Tipo)")["Total"].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Compra/Venda", f"{df_compra_venda["Compra"]/df_compra_venda["Venda"]:,.2%}".replace(",", "X").replace(".", ",").replace("X", "."))
    c2.metric("Compra No Período", f"R$ {df_compra_venda["Compra"]:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    c3.metric("Vendas No Período", f"R$ {df_compra_venda["Venda"]:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    if False:
        st.markdown("## Vendas")
        m1, m2, m3 = st.columns(3)
        m1.metric("Venda Total", f"R$ {total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m2.metric("Ticket Médio", f"R$ {ticket_medio_venda:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m3.metric("Clientes Atendidos", qtd_clientes)
        
        st.markdown("## Compras")
        col1, col2, col3 = st.columns(3)
        col1.metric("Compra Total", f"R$ {total_compras:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("Ticket Médio", f"R$ {ticket_medio_compra:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col3.metric("Fornecedores", qtd_fornecedor)

    
    
    st.markdown("# :material/Bar_Chart: Evolução de Vendas")
    vendas_mensais = df_venda.set_index('Referência').resample('ME')['Total'].sum().reset_index()
    vendas_mensais['Mês/Ano'] = vendas_mensais['Referência'].dt.strftime('%m/%Y')

    compras_mensais = df_compra.set_index('Referência').resample('ME')['Total'].sum().reset_index()
    compras_mensais['Mês/Ano'] = compras_mensais['Referência'].dt.strftime('%m/%Y')
    
    fig_evolucao = px.area(
        vendas_mensais, 
        x='Mês/Ano', 
        y='Total', 
        title="Faturamento por Mês",
        markers=True,
        labels={'Total': 'Faturamento (R$)', 'Mês/Ano': 'Período'}
    )
    fig_evolucao.add_hline(
        y=META_MENSAL, line_dash="dot", annotation_text="Meta", line_color="red"
    )
    fig_evolucao.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1ano", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    st.plotly_chart(fig_evolucao, width="stretch")
    st.divider()

    def top10_clientes():
        # 5. Gráfico de Maiores Clientes (Top 10)
        st.subheader("🏆 Top 10 Clientes")
        top_clientes = df_venda.groupby('Cliente/Fornecedor')['Total'].sum().sort_values(ascending=False).head(10).reset_index()

        fig_clientes = px.bar(
            top_clientes, 
            x='Total', 
            y='Cliente/Fornecedor', 
            orientation='h',
            title="Ranking de Clientes por Volume de Compra",
            text_auto='.2s',
            color='Total',
            color_continuous_scale='Viridis'
        )
        fig_clientes.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_clientes, width="stretch")

        st.divider()
    #top10_clientes()

    # --- Configurações da Meta ---
    st.markdown("## :material/Target: Indicador de Meta (KPI)")
    periodos = df_venda['Referência'].dt.to_period('M').unique().astype(str).tolist()
    periodo_selecionado = st.select_slider(
        "Selecione o Mês de Consulta",
        options=periodos,
        value=periodos[-1] # Começa no mês mais recente
    )
    ultimo_mes = pd.to_datetime(periodo_selecionado)    
    mes_atual = ultimo_mes.month
    ano_atual = ultimo_mes.year

    # 2. Calcular Dias Úteis (Segunda a Sexta)
    todos_os_dias = pd.date_range(start=f'{ano_atual}-{mes_atual}-01', 
                                end=(ultimo_mes + pd.offsets.MonthEnd(0)))
    dias_uteis_totais = len([d for d in todos_os_dias if d.weekday() < 5]) # 0-4 são Seg-Sex
    dias_passados = len([d for d in todos_os_dias if d.weekday()<5 and d<= df_venda["Referência"].max()])

    df_venda_mes_atual = df_venda[
        (df_venda['Referência'].dt.month == mes_atual) & 
        (df_venda['Referência'].dt.year == ano_atual)]
    
    faturamento_mes_atual = df_venda_mes_atual['Total'].sum()


    percentual_meta = (faturamento_mes_atual / META_MENSAL) * 100
    progresso_tempo = (dias_passados / dias_uteis_totais) * 100
    
    meta_batida = percentual_meta>=progresso_tempo
    if dias_passados==dias_uteis_totais:
        if meta_batida:
            status = "✔ Meta Batida"
        else:
            status = "❌ Meta Não foi Batida"
    else:
        if meta_batida:
            status = "Acima do Esperado"
        else:
            status = "Abaixo do Esperado"

    # --- Visualização: Gráfico de Velocímetro (Gauge) ---
    fig_kpi = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = faturamento_mes_atual,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Faturamento vs Meta ({mes_atual}/{ano_atual})", 'font': {'size': 24}},
        delta = {
            'reference': META_MENSAL,
            'increasing': {'color': "green"},
            "valueformat": ".3s",
            #"valueformat": "R$,.2s",
        },
        gauge = {
            'axis': {
                'range': [None, META_MENSAL*1.2],
                'tickformat': '.3s',
                "dtick": META_MENSAL/8,
            },
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, META_MENSAL * 0.5], 'color': "#ffcfcf"}, #ffcfcf
                {'range': [META_MENSAL * 0.5, META_MENSAL * 0.8], 'color': '#fff3cf'},
                {'range': [META_MENSAL * 0.8, META_MENSAL], 'color': '#d9ffcf'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': META_MENSAL
            }
        }
    ))

    st.plotly_chart(fig_kpi, width="stretch")

    # --- Explicação Detalhada do KPI ---
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("Dias Úteis Decorridos", f"{dias_passados} de {dias_uteis_totais}")
    col_kpi2.metric("Meta Atingida", f"{percentual_meta:.1f}%")
    col_kpi3.metric("Tempo Decorrido",f"{progresso_tempo:.1f}%")
    col_kpi4.metric("Status da Meta", status)

    if percentual_meta < progresso_tempo:
        st.error(f"Atenção: Você já percorreu {progresso_tempo:.1f}% dos dias úteis, mas atingiu apenas {percentual_meta:.1f}% da meta.")
    else:
        st.success(f"Excelente! O ritmo de vendas ({percentual_meta:.1f}%) está superior ao tempo decorrido ({progresso_tempo:.1f}%).")

    st.space()
    st.header(":material/Calendar_Today: Análise de Faturamento Detalhado")

    df_diario = df_venda_mes_atual.set_index("Referência")["Total"].resample("D").sum().reset_index()
    df_diario['Semana'] = df_diario['Referência'].dt.strftime('%d/%m/%Y')    

    df_semanal = df_venda_mes_atual.set_index("Referência")["Total"].resample("W",label="left",closed="left").sum().reset_index()
    df_semanal['Semana'] = df_semanal['Referência'].dt.strftime('%d/%m/%Y')


    # Criando o gráfico de barras
    fig_semana = px.bar(
        df_semanal, 
        x="Semana", 
        y="Total",
        title="Faturamento Semanal",
        text_auto='.2s',
        labels={"Total": "Faturamento (R$)", "Referência": "Data"},
        color_discrete_sequence=["#007bff"], # Cor azul padrão
        color='Total',
        color_continuous_scale='Blues'
    )
    fig_semana.add_hline(
        y=META_MENSAL/(dias_uteis_totais/5),
        line_dash="dot",
        annotation_text=f"Meta: {META_MENSAL/(dias_uteis_totais/5):,.2f}",
        annotation_font_color="red",
        line_color="red"
    )

    # Ajustes finos de layout
    fig_semana.update_layout(
        template="plotly_white",
        hovermode="x unified"
    )
    st.plotly_chart(fig_semana, width="stretch")

    # Criando o gráfico de barras
    fig_dia = px.bar(
        df_diario, 
        x="Semana", 
        y="Total",
        title="Faturamento Diário",
        text_auto='.2s',
        labels={"Total": "Faturamento (R$)", "Referência": "Data"},
        color_discrete_sequence=["#007bff"], # Cor azul padrão
        color='Total',
        color_continuous_scale='Blues'
    )
    fig_dia.add_hline(
        y=META_MENSAL/dias_uteis_totais,
        line_dash="dot",
        annotation_text=f"Meta: {META_MENSAL/dias_uteis_totais:,.2f}",
        annotation_position="top left",
        annotation_font_color="red",
        line_color="red"
    )

    # Ajustes finos de layout
    fig_dia.update_layout(
        template="plotly_white",
        hovermode="x unified"
    )
    st.plotly_chart(fig_dia, width="stretch")














else:
    st.info("Aguardando o upload de arquivos para iniciar...")