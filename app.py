import streamlit as st
st.set_page_config(page_title="Relatóios MUMIX", layout="wide")

pages = {
    "Login":[
        st.Page("login.py",title="login",icon=":material/login:"),
        #st.Page("pages/login2.py",title="login2",icon=":material/login:"),
    ],
    "Diretoria": [
        st.Page("relatorio_consolidado.py", title="Faturamento", icon=":material/universal_currency_alt:"),
 
    ],
    "RH/DP": [
        st.Page("gestao_colaboradores.py", title="Gestão Colaboradores", icon=":material/emoji_people:"),

    ]
}

pg = st.navigation(pages,position="top")
pg.run()