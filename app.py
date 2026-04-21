import streamlit as st
st.set_page_config(page_title="Relatóios MUMIX", layout="wide")

pages = {
    "Login":[
        st.Page("login.py",title="login",icon=":material/login:"),
    ],
    "Diretoria": [
        st.Page("pages/faturamento.py", title="Faturamento", icon=":material/universal_currency_alt:"),
        st.Page("pages/relatorio_cmv.py", title="CMV", icon=":material/bar_chart:"),
 
    ],
    "RH/DP": [
        st.Page("pages/gestao_colaboradores.py", title="Gestão Colaboradores", icon=":material/emoji_people:"),
        # st.Page("pages/custo_pessoal.py", title="Custo Pessoal", icon=":material/payment_arrow_down:"),

    ]
}

pg = st.navigation(pages,position="top")
pg.run()