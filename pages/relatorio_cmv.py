import streamlit as st
from utils import carregar_dados, calcular_metricas, CMV_fig_TOPMargem, CMV_fig_TOPFaturamento, CMV_fig_Fin_Margem2, CMV_fig_Margem_Margem2

st.set_page_config(page_title="Relatório CMV", layout="wide")

#   LOGIN
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.session = None

if (st.session_state.user == None) or (st.session_state.perfil['status']!='ativo') or (st.session_state.perfil['role'] not in ['administrador', 'usuario']):
    st.markdown("## :material/Close: Area Restrita")
    if st.button('Realizar login'):
        st.switch_page('login.py')
    st.stop()

perfil = st.session_state.perfil

st.title(":material/Bar_Chart: Relatório CMV")

# Sidebar para carregar o arquivo
with st.sidebar:
    if st.button("Sair do Sistema"):
        st.session_state.user = None
        st.rerun() 
    st.markdown(f'# :blue[{perfil['nome']}]')
    st.markdown(f"{perfil['role'].title()}")
    st.divider()

    st.markdown("# Configurações")
    arquivo = st.file_uploader("Escolha o arquivo Excel", type=['xlsx'])
    fator_giro = st.number_input("Digite a porcentagem desejada do giro do produto",0.0,100.0,2.0,format="%.2f",step=1.0)
    ignora_margem_ficticia = st.toggle("Deseja ignorar magem >90%?")
if arquivo:
    # Chama as funções do arquivo de processamento
    resposta = carregar_dados(arquivo)

    if resposta["erro"]:
        st.stop("Não foi possível carregar arquivo...")
        st.stop()
    else:
        df_bruto = resposta["df"]

    if ignora_margem_ficticia:
        df_bruto = df_bruto[df_bruto["Margem (%)"]<90].copy()

    df_processado, alertas, resumo = calcular_metricas(df_bruto,fator_giro)

    # Exibição de Métricas (Cards)
    col1, col2, col3 = st.columns(3)
    col1.metric("Faturamento Total", f"R$ {resumo['faturamento']:,.2f}")
    col2.metric("CMV Total", f"R$ {resumo['cmv_total']:,.2f}")
    col3.metric("Margem CMV", f"{resumo['margem']:.2f}%")


    num_alertas = sum(not alertas[alerta].empty for alerta in alertas)
    
    st.markdown("# :material/Flash_On: Central de Alertas")
    st.markdown(f"### :red[{num_alertas}] Tipos de Alertas")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Margem Baixa + Estoque Alto", "Baixo Giro", "Margem Negativa", "Estoque Negativo"])

    with tab1:
        if not alertas['alerta_margem'].empty:
            st.markdown(f"### {len(alertas['alerta_margem'])} Margem e Giro Baixo")
            st.write(f"|- Margem abaixo do CMV: :blue[{resumo['margem']:.2f}%]")
            st.write(f"|- Giro de estoque em :blue[{fator_giro}%]")
            st.dataframe(alertas['alerta_margem'], width="stretch",height="content")
        else:
            st.success("Nenhum produto com estoque crítico e margem baixa.")

    with tab2:
        if not alertas['alerta_giro'].empty:
            st.markdown(f"### {len(alertas['alerta_giro'])} Produtos com Baixo Giro")
            st.write(f"|- Giro de estoque em :blue[{fator_giro}%]")
            st.dataframe(alertas['alerta_giro'], width="stretch",height="content")

    with tab3:
        if not alertas['alerta_prejuizo'].empty:
            st.markdown(f"### {len(alertas['alerta_prejuizo'])} Produtos com Margem Negativa")
            st.dataframe(alertas['alerta_prejuizo'], width="stretch",height="content")
        else:
            st.success("Excelente! Nenhum produto com margem negativa.")
    with tab4:
        if not alertas['alerta_negativo'].empty:
            st.markdown(f"### {len(alertas["alerta_negativo"])} Produtos com Estoque Negativo")
            st.dataframe(alertas['alerta_negativo'], width="stretch",height="content")
        else:
            st.success("Excelente! Nenhum produto com estoque negativa.")


    st.divider()
    st.markdown("# :material/Bar_Chart: Gráficos")
    
    fig_TopMargem = CMV_fig_TOPMargem(df_processado)
    st.plotly_chart(fig_TopMargem, width="stretch",height="content")

    fig_TopFaturamento  = CMV_fig_TOPFaturamento(df_processado)
    st.plotly_chart(fig_TopFaturamento, width="stretch")

    fig_teste = CMV_fig_Fin_Margem2(df_processado)
    st.plotly_chart(fig_teste, width="stretch")

    fig_teste2 = CMV_fig_Margem_Margem2(df_processado)
    st.plotly_chart(fig_teste2, width="stretch")

    # Exibição da Tabela
    st.divider()
    st.markdown("# Detalhamento de Produtos")
    st.dataframe(df_processado)
    
    busca = st.text_input("Filtrar por nome do produto")
    if busca:
        df_filtrado = df_processado[df_processado['Nome'].str.contains(busca, case=False)]
        st.write(df_filtrado)
else:
    st.info("Aguardando upload do arquivo Excel para gerar o relatório (aba lateral).")