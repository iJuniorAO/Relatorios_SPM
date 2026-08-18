import streamlit as st

st.set_page_config(page_title="Relatórios MUMIX", layout="wide")

login = st.Page("login.py", title="login", icon=":material/login:")


# diretoria

grupo_mumix = st.Page(
    "pages/grupo_mumix.py",
    title="Grupo Mumix",
    icon=":material/work:",
)


faturamento = st.Page(
    "pages/faturamento.py",
    title="Faturamento",
    icon=":material/universal_currency_alt:",
)


cmv = st.Page("pages/relatorio_cmv.py", title="CMV", icon=":material/bar_chart:")

resultado = st.Page(
    "pages/AR.py", title="Apresentação Resultado", icon=":material/area_chart:"
)

devolucao = st.Page(
    "pages/devolucoes.py",
    title="Devoluções Detalhado",
    icon=":material/stacked_line_chart:",
)

# rh/dp
gestao_colaboradores = st.Page(
    "pages/gestao_colaboradores.py",
    title="Gestão Colaboradores",
    icon=":material/emoji_people:",
)


# custo_pesosal = st.Page("pages/custo_pessoal.py", title="Custo Pessoal", icon=":material/payment_arrow_down:"),

pages = {
    "Diretoria": [grupo_mumix, faturamento, cmv, resultado, devolucao],
    "RH/DP": [gestao_colaboradores],
}

pg = st.navigation(pages, position="top")
pg.run()
