import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import requests
import re
import locale


st.set_page_config(page_title="Colaboradores Ativos", layout="wide")
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

if False:   #   Posteriormente usar login
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user == None:
        st.markdown("## :material/Close: Area Restrita")
        st.markdown("Realize login")
        st.stop()



HOJE = datetime.now()
HOJE_DATA = pd.to_datetime(HOJE.date())
HOJE_MES = HOJE_DATA.month
HOJE_ANO =HOJE_DATA.year
ULTIMO_DIA_ANO = pd.to_datetime(f'{HOJE_DATA.year}-12-31')

link_arquivo = False
#link_arquivo = st.secrets["onedrive"]["bd_excel"]

@st.cache_data(ttl=7200, show_spinner=True, scope="session")
def carregar_dados_onedrive(input_texto):
    with st.spinner("Pegando Arquivos Automaticamente...",show_time=True):
        try:
            # 1. Limpeza: Se o usuário colou o <iframe>, extrai apenas a URL
            url_match = re.search(r'src="([^"]+)"', input_texto)
            url = url_match.group(1) if url_match else input_texto
            
            # 2. Ajuste para SharePoint Business
            # Se for link de embed do SharePoint, mudamos para o modo de download
            if "sharepoint.com" in url:

                if "embed.aspx" in url:
                    # Transforma o link de embed em um link de ação de download
                    url = url.replace("embed.aspx", "download.aspx")
                elif "download=1" not in url:
                    # Se for link de compartilhamento normal, força o download
                    url = url + ("&" if "?" in url else "?") + "download=1"
            else:
                # Caso seja OneDrive Pessoal
                url = url.replace("embed", "download")

            # 3. Faz a requisição
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            
            return response.text
        except Exception as e:
            st.error(f"Erro ao processar URL: {e}")
            return None


def importa_valida(df):
    df = df.drop(columns=["MesAdm","AnoAdm","AnosEmpresa","Tativo","MesDeslig","AnoDeslig","Exp 45 dias","Exp 90 dias", "Prazo EXP","MesAnv"])



    df_ativos = df[df["Status"].isin(["ATIVO","INSS"])]
    df_exp = df[df["Status"]=="EXPERIENCIA"]
    df_CNH = df[df["Status"]!="DESLIGADO"].dropna(subset=["Validade de CNH"]).copy()
    df_aniversario = df_ativos[["Colaborador","EMPRESA","Admissão","Status","Data de Nascimento"]]

    df_validacao_ativo = df[df["Status"]!="DESLIGADO"]
    erro_ativo = df_ativos[df_ativos["Desligamento"]== "Nat"]

    df_validacao_ativo = df_validacao_ativo.drop(columns=["Admissão","Desligamento","Data de Nascimento","Validade de CNH","Categoria CNH","Validade Exame Toxicologico"])
    df_info_vazio = df_validacao_ativo[df_validacao_ativo.isna().any(axis=1)].set_index("Colaborador")

    vazio_dt = df[["Colaborador","EMPRESA","Admissão","Data de Nascimento"]]
    vazio_dt = vazio_dt[vazio_dt.isnull().any(axis=1)].set_index("Colaborador")

    df_CNH = df_CNH[[ 'Colaborador', 'Cargo', 'EMPRESA', 'Status', 'Validade de CNH', 'Categoria CNH', 'Validade Exame Toxicologico', 'Telefone para Contato']]

    validacao_categoria = df_CNH[df_CNH["Categoria CNH"].isna()]
    validacao_categoria = df_CNH[["Colaborador","EMPRESA","Telefone para Contato","Categoria CNH"]]
    validacao_categoria = validacao_categoria.set_index("Colaborador")

    validacao_toxicologico = df_CNH[df_CNH["Validade Exame Toxicologico"].isna()] 
    validacao_toxicologico = validacao_toxicologico[["Colaborador", "EMPRESA", "Telefone para Contato", "Validade Exame Toxicologico"]]
    validacao_toxicologico = validacao_toxicologico.set_index("Colaborador")
    

    if not validacao_toxicologico.empty:
        st.warning(f"Erro no preenchimento referente a CNH")
        with st.expander(":material/Close: Verificar erros CNH"):
            if not validacao_toxicologico.empty:
                st.write(f"{len(validacao_toxicologico)} - Exame toxicologico não preenchido")
                validacao_toxicologico
            if not validacao_categoria.empty:
                st.write(f"{len(validacao_categoria)} - Categoria CNH não preenchido")
                validacao_categoria

    
    st.divider()
    return df,df_ativos, df_exp, df_CNH, df_aniversario, df_info_vazio, vazio_dt, validacao_toxicologico, erro_ativo


def trata_df_exp(df_exp):
    df_exp = df_exp[['Colaborador', 'Cargo', 'EMPRESA', 'Admissão', 'Desligamento', 'Salário Atual', 'Telefone para Contato', 'Sexo', 'Tem Filhos']]
    df_exp['Vence_30d'] = df_exp['Admissão'] + pd.Timedelta(days=30)
    df_exp['Vence_90d'] = df_exp['Admissão'] + pd.Timedelta(days=90)

    df_exp['Prazo_30_Dias'] = (df_exp['Vence_30d'] - HOJE_DATA).dt.days
    df_exp['Prazo_90_Dias'] = (df_exp['Vence_90d'] - HOJE_DATA).dt.days

    exp_30D = df_exp[df_exp["Prazo_30_Dias"]>0]
    exp_30D = exp_30D[["Colaborador","EMPRESA","Admissão","Vence_30d","Prazo_30_Dias"]]
    exp_30D_empresa = exp_30D[["Colaborador","EMPRESA"]].groupby("EMPRESA").count()
    exp_30D = exp_30D.set_index("Colaborador").sort_values("Admissão")

    exp_90D = df_exp[df_exp["Prazo_30_Dias"]<0]
    exp_90D = exp_90D[["Colaborador","EMPRESA","Admissão","Vence_90d","Prazo_90_Dias"]]
    exp_90D_empresa = exp_90D[["Colaborador","EMPRESA"]].groupby("EMPRESA").count()
    exp_90D = exp_90D.set_index("Colaborador").sort_values("Admissão")

    df_exp_vencido = df_exp[df_exp["Prazo_90_Dias"]<0]


    return df_exp, exp_30D, exp_30D_empresa, exp_90D, exp_90D_empresa, df_exp_vencido

def trata_df_CNH(df_CNH):
    vencimento_90 = df_CNH[df_CNH["Validade de CNH"] <= HOJE_DATA + pd.Timedelta(days=90)]
    vencimento_90 = vencimento_90[["Colaborador","Validade de CNH","Telefone para Contato"]]
    vencimento_90 = vencimento_90.set_index("Colaborador")
    vencimento_90 = vencimento_90.sort_values("Validade de CNH")
    
    
    vencimento_ano =df_CNH[df_CNH["Validade de CNH"]<= ULTIMO_DIA_ANO]
    vencimento_ano = vencimento_ano[["Colaborador","Validade de CNH","Telefone para Contato"]]
    vencimento_ano = vencimento_ano.set_index("Colaborador")
    vencimento_ano = vencimento_ano.sort_values("Validade de CNH")

    vencimento_toxicologico = df_CNH[df_CNH["Validade Exame Toxicologico"]<=HOJE_DATA+ pd.Timedelta(days=90)]
    vencimento_toxicologico = vencimento_toxicologico[["Colaborador","Validade Exame Toxicologico","Telefone para Contato"]]
    vencimento_toxicologico = vencimento_toxicologico.set_index("Colaborador")
    vencimento_toxicologico = vencimento_toxicologico.sort_values("Validade Exame Toxicologico")
    
    df_CNH = df_CNH.set_index("Colaborador")

    return df_CNH, vencimento_90, vencimento_ano, vencimento_toxicologico

def trata_df_aniv(df_aniversario,mes_aniversario):
    df_aniversario['Mês de Nascimento'] = df_aniversario['Data de Nascimento'].dt.month
    df_aniversario['Mês de Admissão'] = df_aniversario['Admissão'].dt.month
    


    niver_vida = df_aniversario[df_aniversario['Data de Nascimento'].dt.month == mes_aniversario].copy()
    niver_vida['Dia'] = niver_vida['Data de Nascimento'].dt.day

    niver_empresa = df_aniversario[df_aniversario['Admissão'].dt.month == mes_aniversario].copy()
    niver_empresa['Anos de Casa'] = HOJE_ANO - niver_empresa['Admissão'].dt.year
    niver_empresa['Dia'] = niver_empresa['Admissão'].dt.day

    niver_empresa = niver_empresa[niver_empresa['Anos de Casa'] > 0]

    anv_nascimento = df_aniversario['Mês de Nascimento'].value_counts().sort_index().reindex(range(1, 13), fill_value=0)
    anv_empresa = df_aniversario['Mês de Admissão'].value_counts().sort_index().reindex(range(1, 13), fill_value=0)

    df_plot = pd.DataFrame({
        'Mês': range(1, 13),
        'Aniv. Nascimento': anv_nascimento.values,
        'Aniv. Empresa': anv_empresa.values
    }).melt(id_vars='Mês', var_name='Tipo', value_name='Quantidade')

    meses_nome = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
    df_plot['Mês Nome'] = df_plot['Mês'].map(meses_nome)

    fig = px.bar(df_plot, 
                x='Mês Nome', 
                y='Quantidade', 
                color='Tipo',
                barmode='group',  # Este comando coloca as barras lado a lado
                title='Comparativo Mensal: Nascimento vs. Empresa',
                color_discrete_map={'Aniv. Nascimento': '#004777', 'Aniv. Empresa': '#E40039'},
                category_orders={"Mês Nome": list(meses_nome.values())},
                text_auto=True) # Adiciona os números em cima das barras

    fig.update_layout(
        xaxis_title="Meses",
        yaxis_title="Total de Colaboradores",
        legend_title="Categoria",
        plot_bgcolor='rgba(0,0,0,0)' # Fundo limpo
    )

    niver_vida = niver_vida [["Colaborador", "EMPRESA","Status","Dia"]].set_index("Colaborador")
    niver_empresa = niver_empresa[["Colaborador","EMPRESA","Status","Dia","Anos de Casa"]].set_index("Colaborador").sort_values("Anos de Casa",ascending=False)
    return niver_vida,niver_empresa,fig

def trata_turn_over(df):
    
    #hoje = pd.Timestamp.now()
    
    inicio_periodo = HOJE - pd.DateOffset(months=12)
    meses = pd.date_range(start=inicio_periodo, end=HOJE, freq='MS')
    
    historico = []

    for mes in meses:
        ativos = df[(df['Admissão'] <= mes) & 
                    ((df['Desligamento'].isna()) | (df['Desligamento'] > mes))].shape[0]
        
        entradas = df[(df['Admissão'].dt.month == mes.month) & 
                    (df['Admissão'].dt.year == mes.year)].shape[0]
        
        saidas = df[(df['Desligamento'].dt.month == mes.month) & 
                    (df['Desligamento'].dt.year == mes.year)].shape[0]
        
        # Cálculo de Turnover (Média de Entradas/Saídas sobre Ativos do mês anterior/atual)
        # Fórmula comum: ((Entradas + Saídas) / 2) / Ativos
        taxa_turnover = 0
        if ativos > 0:
            taxa_turnover = round(((entradas + saidas) / 2) / ativos * 100, 2)
            
        historico.append({
            'Mês': mes.strftime('%b/%Y'),
            'Ativos': ativos,
            'Entradas': entradas,
            'Saídas': saidas,
            'Turnover %': taxa_turnover
        })

    df_metrics = pd.DataFrame(historico)
    
    turnover_por_cargo = df[df['Status'] == 'DESLIGADO'].groupby('Cargo').size().reset_index(name='Total Desligamentos')
    

    return {
        "df_mensal": df_metrics,
        "turnover_cargo": turnover_por_cargo.sort_values(by='Total Desligamentos', ascending=False),
        "media_turnover": round(df_metrics['Turnover %'].mean(), 2)
    }

def processar_faixa_etaria(df):
    # Calcular a idade
    df['Idade'] = df['Data de Nascimento'].apply(
        lambda x: HOJE_ANO - x.year - ((HOJE_MES, HOJE.day) < (x.month, x.day))
    )
    
    # Definir os cortes e os nomes das faixas
    bins = [0, 18, 25, 35, 45, 60, 100]
    labels = ['Até 18 anos', '19-25 anos', '26-35 anos', '36-45 anos', '46-60 anos', 'Mais de 60']
    df['Faixa Etária'] = pd.cut(df['Idade'], bins=bins, labels=labels, right=False)

    df['Faixa Etária'] = pd.Categorical(
    df['Faixa Etária'], 
    categories=labels, 
    ordered=True
    )
    df = df.sort_values('Faixa Etária')
        
    return df

def processar_dados_piramide(df):
    """
    Agrupa os dados por Faixa Etária e Sexo, transformando o 
    contingente masculino em valores negativos para o gráfico.
    """
    # Agrupamento e contagem
    df_agrupado = df.groupby(['Faixa Etária', 'Sexo']).size().reset_index(name='Contagem')
    
    # Separando os dados
    msc = df_agrupado[df_agrupado['Sexo'] == 'MASCULINO'].copy()
    fem = df_agrupado[df_agrupado['Sexo'] == 'FEMININO'].copy()
    
    # Invertendo o valor do masculino para a esquerda (negativo)
    msc['Contagem'] = msc['Contagem'] * -1
    
    return msc, fem


st.markdown("# :material/Bar_chart: Gestão de Colaboradores")

pegar_automatico = st.toggle("Deseja Pegar Arquivos Automaticamente?",value=False,disabled=True)
if pegar_automatico:
    st.info("EM DESENVOLVIMENTO...")
arquivos_carregados = st.file_uploader("Carregue seu arquivo Excel ou CSV", type=['csv', 'xlsx'])

if arquivos_carregados: 
    if arquivos_carregados.name.endswith('.csv'):
        df = pd.read_csv(arquivos_carregados)
    else:
        df = pd.read_excel(arquivos_carregados)

    st.markdown("# :material/Filter_Alt: Filtros")
    empresa = list(df["EMPRESA"].unique())
    empresa_selecionada = st.multiselect("Empresas",empresa,placeholder="Selecione a empresa",default=empresa)
    
    if empresa_selecionada==[]:
        st.space()
        st.info("Selecione ao menos 1 empresa acima")
        st.stop()
    
    df = df[df["EMPRESA"].isin(empresa_selecionada)]
    
    df, df_ativos, df_exp, df_CNH, df_aniversario, df_info_vazio, vazio_dt, validacao_toxicologico, erro_ativo = importa_valida(df)
    df_exp, exp_30D, exp_30D_empresa, exp_90D, exp_90D_empresa, df_exp_vencido = trata_df_exp(df_exp)
    df_CNH, vencimento_90, vencimento_ano, vencimento_toxicologico = trata_df_CNH(df_CNH)
    metrics = trata_turn_over(df)
    df_idade = processar_faixa_etaria(df_ativos)

    st.markdown("# Erros e Avisos")
    if df_exp_vencido.empty and vencimento_90.empty and vencimento_toxicologico.empty:
        st.success(":material/Check: Nenhum alerta crítico pendente")
    else:
        st.error(":material/Close: ALERTA CRÍTICO")
    if not df_exp_vencido.empty:
        st.warning(f":material/Do_Not_Disturb_On: {len(df_exp_vencido)} Experiências Vencidas")
    if not vencimento_90.empty:
        st.error(f":material/Id_Card: {len(vencimento_90)} CNHs vencendo")
    if not vencimento_toxicologico.empty:
        st.error(f":material/Id_Card: {len(vencimento_toxicologico)} Exame(s) vencendo")

    st.space()
    if not df_info_vazio.empty:
        st.error(f"{len(df_info_vazio)} Linhas Vazias")
        with st.expander(":material/Do_Not_Disturb_On: Verificar linhas vazias"):
            col_vazio = df_info_vazio.columns
            for col in col_vazio:
                lin_vazia = df_info_vazio[df_info_vazio[col].isna()]
                if not lin_vazia.empty:
                    st.write(f"Linha vazia em: {col}")
                    lin_vazia[["EMPRESA",col]]

        if not erro_ativo.empty:
            st.write(erro_ativo)
        if not vazio_dt.empty:
            st.error(f" {len(vazio_dt)} Datas não preenchidas")
            with st.expander(":material/Do_Not_Disturb_On: Verificar Datas Vazias"):
                st.dataframe(vazio_dt.style.format({"Admissão":"{:%d/%m/%Y}","Data de Nascimento":"{:%d/%m/%Y}"},na_rep=""))
        st.divider()







    st.space("medium")
    tabs = st.tabs(["Visão Geral", "Prazos e Alertas", "Aniversariantes", "Turn-Over"])

    with tabs[0]:

        df_ativos = df_ativos.copy()

        df_cont_empresa = df_ativos['EMPRESA'].value_counts().reset_index().rename(columns={"count":"Qt Colaboradores"})
        fig_cont_empresa = px.pie(
            df_cont_empresa,
            values='Qt Colaboradores',
            names='EMPRESA',
            hole=0.6,
            color_discrete_sequence=px.colors.qualitative.Pastel)
        df_cont_empresa = df_cont_empresa.set_index("EMPRESA")
        
        df_cont_genero = df_ativos.groupby(["EMPRESA","Sexo"]).size().reset_index(name="Total")        
        fig_cont_genero = px.bar(
            df_cont_genero,
            x ="Total",
            y="EMPRESA", 
            color="Sexo",
            barmode="group",
            text_auto=True,
            #title="",
            #color_discrete_map={'M': '#004777', 'F': '#E40039'}, # Azul para M, Vermelho/Rosa para F
            color_discrete_map={'MASCULINO': '#004777', 'FEMININO': '#E40039'},

            #debbug
            
            labels={'EMPRESA': 'Unidade/Empresa', 'count': 'Total de Pessoas', 'Sexo': 'Gênero'}
        )
        fig_cont_genero.update_layout(
            yaxis={'categoryorder':'total ascending'}
        )

        st.markdown("# Colaboradores")
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        col_kpi1.metric("Colaboradores Ativos", len(df_ativos))
        col_kpi2.metric("Contratos em Exp.", len(df_exp))
        col_kpi3.metric("Motoristas", len(df_CNH))
        #col_kpi4.metric("Aniversariantes do Mês", len(niver_vida)+len(niver_empresa))

        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Distribuição por Empresa")
            st.dataframe(df_cont_empresa)
            st.space("large")

            
        with c2:
            st.plotly_chart(fig_cont_empresa, width="content")

        st.markdown("### Colaboradores por Gênero")
        st.plotly_chart(fig_cont_genero,width="stretch")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Distribuição por Faixa Etária")

            df_counts = df_idade['Faixa Etária'].value_counts(sort=False).reset_index()
            df_counts.columns = ['Faixa Etária', 'Quantidade']
            
            fig_bar = px.bar(
                df_counts, 
                x='Faixa Etária', 
                y='Quantidade',
                text='Quantidade',
                color='Faixa Etária',
                color_discrete_sequence=px.colors.qualitative.Prism,
                template="plotly_white"
            )
            fig_bar.update_traces(textposition='outside')
            st.plotly_chart(fig_bar, width="stretch")

        with col2:
            st.subheader("Percentual por Gênero/Sexo")
            # Gráfico de Pizza para complementar a análise demográfica
            fig_pie = px.pie(
                df_idade, 
                names='Sexo', 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_pie, width="stretch")



    with tabs[1]:
        st.markdown("# Experiência")
        
        st.markdown("### Experiência Vencida")
        if df_exp_vencido.empty:
            st.info("Sem Colaborador com experiência vencida")
        else:
            st.error(f"{len(df_exp_vencido)} Colaboradores com experiência vencida")
            df_exp_vencido

        st.markdown("## Colaborador em experiência por Empresa")
        st.markdown(f"### Experiência 30 Dias | :blue[{len(exp_30D)} Colaboradores]")
        col1, col2 = st.columns([2,4])
        
        col1.dataframe(exp_30D_empresa)
        col2.dataframe(exp_30D.style.format({"Admissão": "{:%d/%m/%Y}","Vence_30d": "{:%d/%m/%Y}"}))
 
        st.markdown(f"### Experiência 90 Dias | :blue[{len(exp_90D)} Colaboradores]")
        coluna1, coluna2 = st.columns([2,4])

        coluna1.dataframe(exp_90D_empresa)
        coluna2.dataframe(exp_90D.style.format({"Admissão": "{:%d/%m/%Y}","Vence_90d": "{:%d/%m/%Y}"}))

        st.divider()

        st.markdown(("# CNH"))
        
        estilo_padrao = {
            "Validade de CNH": "{:%d/%m/%Y}", 
            "Salário Atual": "R$ {:,.2f}"
        }
        st.write((f"### Motoristas Ativos | :blue[{len(df_CNH)} Motoristas]"))
        st.write(df_CNH.style.format({"Validade de CNH": "{:%d/%m/%Y}","Validade Exame Toxicologico": "{:%d/%m/%Y}"},na_rep="-"))

        st.space()
        st.markdown(("## Vencimento CNH"))
        co1, co2, co3 = st.columns(3)

        with co1:
            st.markdown(("### :material/Hourglass: CNH Vencimento em 90 dias"))
            if vencimento_90.empty:
                st.info((":material/Check: Nenhuma CNH vencendo nos próximos 90 dias."))
            else:
                st.write(vencimento_90.style.format({"Validade de CNH": "{:%d/%m/%Y}"}))
        with co2:
            st.markdown(("### :material/Hourglass_Bottom: CNH Vencimento até fim do ano"))
            if vencimento_ano.empty:
                st.info((":material/Check: Nenhuma CNH vencendo até fim do ano."))
            else:
                st.warning(f"{len(vencimento_ano)} CNH vencendo até o fim do ano")
                st.write(vencimento_ano.style.format({"Validade de CNH": "{:%d/%m/%Y}"}))
        with co3:
            st.markdown(("### :material/Hourglass: Exame Vencimento em 90 dias"))
            if vencimento_toxicologico.empty:
                st.info((":material/Check: Nenhuma Exame vencendo nos próximos 90 dias."))
            else:
                st.write(vencimento_toxicologico.style.format({"Validade Exame Toxicologico": "{:%d/%m/%Y}"}))
 
    with tabs[2]:

        mes_anv_selecionado = st.select_slider("Selecione o mês: ",range(1,13),value=HOJE_MES)
        niver_vida,niver_empresa,niver_grafico = trata_df_aniv(df_aniversario, mes_anv_selecionado)

        st.markdown(f"# :blue[{len(niver_vida)+len(niver_empresa)} |] Aniversariantes :blue[{datetime(HOJE_ANO,mes_anv_selecionado,1).strftime("%B").title()}]")
    

        c1, c2 = st.columns(2)
        
        c1.markdown(f"### Aniversário Nascimento :blue[| {len(niver_vida)}]")
        c1.dataframe(niver_vida)
        c2.markdown(f"### Aniversário Empresa :blue[| {len(niver_empresa)}]")
        c2.dataframe(niver_empresa)


        st.plotly_chart(niver_grafico, width="stretch")

    with tabs[3]:
    
        col1, col2, col3 = st.columns(3)
        col1.metric("Colaboradores Ativos", len(df_ativos))
        col2.metric("Média Turnover (12m)", f"{metrics['media_turnover']}%")
        col3.metric("Total de Saídas (Período)", metrics['df_mensal']['Saídas'].sum())

        # Gráfico de Evolução Mensal
        st.subheader("Evolução de Entradas vs Saídas")
        fig_evolucao = px.line(
            metrics['df_mensal'], x='Mês', y=['Entradas', 'Saídas'], 
            markers=True,
            color_discrete_sequence=['#2ecc71', '#e74c3c'])
        
        st.plotly_chart(fig_evolucao, width="stretch")

        # Visão por Cargo e Tabela Detalhada
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Desligamentos por Cargo - TOP10")
            fig_cargo = px.bar(metrics['turnover_cargo'].head(10), x='Total Desligamentos', y='Cargo', 
                            orientation='h', color_discrete_sequence=['#004777'])
            st.plotly_chart(fig_cargo, width="stretch")

        with c2:
            st.subheader("Dados Consolidados")
            st.dataframe(metrics['df_mensal'].set_index("Mês"), width="stretch")
                

else:
    st.info("Aguardando upload do arquivo para gerar os indicadores.")
    