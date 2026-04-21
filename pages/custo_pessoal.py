import streamlit as st
import pandas as pd
import plotly.express as px

# 1. FUNÇÃO DE TRATAMENTO DE DADOS E CÁLCULOS
def processar_folha(df, FGTS, INSS_PATRONAL, DSR_PADRAO):
    df = df.drop(columns={"FGTS","INSS Patronal","Férias","1/3 de Férias","FGTS Férias","INSS Patronal Férias","13º Salário", "FGTS 13º","INSS Patronal 13º","DSR/Horas Extras","INSS Patronal H.E.","FGTS H.E.","Custo total (Salario +Verbas)","TOTAL BENEFÍCIOS","CUSTO PESSOAS MÊS","CUSTO TOTAL RESCISÃO","CUSTO TOTAL (FOLHA + RESCISÃO)"})

    colunasNumericas = ['Salario', 'Salario Familia',
        'Horas Extras', 'Gratificação', 'Premiação', 'Vale Combustível ECXPAY',
        'Recarga Mobilidade ECXPAY', 'Recarga VT / ECXPAY', 'Vale Compras',
        'Cesta básica VA/VR', 'VA + VR ECXPAY', 'RESCISÃO', 'FGTS/Multa 40%']
    

    listaColunasZeradas = []
    for col in colunasNumericas:
        df[col] = pd.to_numeric(df[col],errors="coerce")
        listaColunasZeradas.append(df[df[col].isna()][["Nome","Empresa",col]])
    
    df = df[df["Salario"]>0]

    df['FGTS'] = df['Salario'] * FGTS
    df['INSS Patronal'] = df['Salario'] * INSS_PATRONAL

    df['DSR/Horas Extras'] = df['Horas Extras'] / DSR_PADRAO # Estimativa padrão
    df["subtotal_HrsExtras"] = df["DSR/Horas Extras"]+df["Horas Extras"]

    # --- Provisões de Férias e 13º ---
    df['Férias'] = df['Salario'] / 12
    df['1/3 de Férias'] = df['Férias'] / 3
    df['13º Salário'] = df['Salario'] / 12

    df["subtotal_Ferias"] = df["Férias"]+df["1/3 de Férias"]+df["13º Salário"]


    # Encargos sobre provisões
    df['FGTS Férias'] = (df['Férias'] + df['1/3 de Férias']) * FGTS
    df['INSS Patronal Férias'] = (df['Férias'] + df['1/3 de Férias']) * INSS_PATRONAL
    df['FGTS 13º'] = df['13º Salário'] * FGTS
    df['INSS Patronal 13º'] = df['13º Salário'] * INSS_PATRONAL

    df["subtotal_Encargos"] = df["FGTS Férias"]+df["INSS Patronal Férias"]+df["FGTS 13º"]+df["INSS Patronal 13º"]

    # --- Rescisão ---
    df['FGTS/Multa 40%'] = df['RESCISÃO'] * 0.40 # Exemplo simplificado

    # --- Totais ---
    df['subtotal_funcionario (Salario+Verbas)'] = (
        df['Salario'] + df['FGTS'] + df['INSS Patronal'] + 
        df["subtotal_HrsExtras"]+
        df['subtotal_Ferias'] +
        df["subtotal_Encargos"]+
        df['Gratificação'] + df['Premiação']
    )

    df['TOTAL RESCISÃO'] = df['RESCISÃO'] + df['FGTS/Multa 40%']

    df['TOTAL BENEFÍCIOS'] = (
        df['Vale Combustível ECXPAY'] + df['Recarga Mobilidade ECXPAY'] + 
        df['Recarga VT / ECXPAY'] + df['Vale Compras'] + 
        df['Cesta básica VA/VR'] + df['VA + VR ECXPAY']
    )

    df['CUSTO PESSOAS MÊS'] = df['subtotal_funcionario (Salario+Verbas)'] + df['TOTAL BENEFÍCIOS']
    df['CUSTO TOTAL (FOLHA+RESCISÃO)'] = df['CUSTO PESSOAS MÊS'] + df['TOTAL RESCISÃO']
    df_analise = df[["Nome","Cargo","Empresa","Salario","subtotal_HrsExtras","subtotal_Ferias","subtotal_Encargos","subtotal_funcionario (Salario+Verbas)","TOTAL RESCISÃO","TOTAL BENEFÍCIOS","CUSTO PESSOAS MÊS","CUSTO TOTAL (FOLHA+RESCISÃO)"]]


    return df_analise, listaColunasZeradas

# 2. INTERFACE STREAMLIT
def main():
    st.set_page_config(page_title="Relatório de Custo de Pessoal", layout="wide")
    st.title(":material/area_chart: Dashboard de Gestão de Folha e Custos")

    st.header("Configurações")
    uploaded_file = st.file_uploader("Suba seu arquivo Excel/CSV", type=["xlsx", "csv"])

    if uploaded_file:
        # Carregar dados
        if uploaded_file.name.endswith('.xlsx'):
            df_raw = pd.read_excel(uploaded_file,sheet_name=None,header=0)
        else:
            df_raw = pd.read_csv(uploaded_file,sheet_name=None,header=0)


        st.markdown("# :material/Filter_Alt: Filtros")
        c1, c2 = st.columns(2)
        with c1:
            aba_selecionada = st.selectbox("Selecione a aba da planilha",df_raw.keys())
            print(df_raw.keys())
            df_raw = df_raw[aba_selecionada]
        with c2:
            loja_selecionada = st.multiselect("Selecione filtro de loja",df_raw["Empresa"].unique(),default=df_raw["Empresa"].unique())
            df_raw = df_raw[df_raw["Empresa"].isin(loja_selecionada)]
        with st.expander("Configurações"):
            FGTS = st.number_input("Valor do FGTS (%)",0.0,100.0,8.0)
            INSS_PATRONAL = st.number_input("Valor do INSS Patronal (%)",0.0,100.0,0.273,format="%0.3f")
            INSS_PATRONAL = st.number_input("Valor do INSS Patronal (%)",0.0,100.0,0.273,format="%0.3f")
            DSR_PADRAO = st.number_input("DSR Padrão (dias)",0,30,4)
            

            FGTS /=100
            INSS_PATRONAL /=100



        # Processamento
        with st.spinner('Calculando verbas e encargos...'):
            df_final, lista_zerada = processar_folha(df_raw, FGTS, INSS_PATRONAL, DSR_PADRAO)

        st.divider()

        lista_zerada

        # --- MÉTRICAS GERAIS ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Custo Total Folha", f"R$ {df_final['CUSTO PESSOAS MÊS'].sum():,.2f}")
        m2.metric("Total Benefícios", f"R$ {df_final['TOTAL BENEFÍCIOS'].sum():,.2f}")
        m3.metric("Total Rescisões", f"R$ {df_final['CUSTO TOTAL RESCISÃO'].sum():,.2f}")

        # --- GRÁFICOS ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Custo por Cargo")
            fig_cargo = px.bar(df_final, x='Cargo', y='CUSTO PESSOAS MÊS', color='Empresa', barmode='group')
            st.plotly_chart(fig_cargo, use_container_width=True)

        with col_right:
            st.subheader("Composição do Custo (Top 10 Funcionários)")
            fig_pizza = px.pie(df_final.nlargest(10, 'CUSTO PESSOAS MÊS'), values='CUSTO PESSOAS MÊS', names='Nome')
            st.plotly_chart(fig_pizza, use_container_width=True)

        # --- TABELA DE DADOS ---
        st.subheader("Visualização Detalhada")
        st.dataframe(df_final.style.format(precision=2, decimal=','))

        # --- DOWNLOAD ---
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar Relatório Processado", csv, "relatorio_custos_completo.csv", "text/csv")
    
    else:
        st.info("Aguardando upload do arquivo para gerar os cálculos e gráficos.")

if __name__ == "__main__":
    main()