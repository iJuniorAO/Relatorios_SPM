import streamlit as st
from supabase import create_client, Client

@st.cache_resource(show_spinner=True,scope='session')
def inicia_conexao_bancoDados():
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase

def realizar_login(email, senha):
    try:
        resposta = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        return resposta
    except Exception as e:
        st.error(f"Erro no login: {e}")
        return None

def cadastrar_usuario(nome, email, senha, departamento):
    try:
        # 1. Cria o usuário no Auth (Sistema de Login)
        auth_res = supabase.auth.sign_up({"email": email, "password": senha})
        
        if auth_res.user:
            user_uuid = auth_res.user.id
            
            # 2. Cria a linha na sua tabela 'perfis' manualmente
            perfil_data = {
                "id": user_uuid,
                "nome": nome,
                "dept": departamento,
                "status": "ativo",
                "permissoes": "leitura"
            }
            
            supabase.table("perfis").insert(perfil_data).execute()
            st.success("Cadastro realizado! Verifique seu e-mail (se a confirmação estiver ativa).")
        else:
            st.error("Erro ao gerar usuário. Verifique se o e-mail já existe.")
            
    except Exception as e:
        st.error(f"Erro no processo de cadastro: {e}")

def buscar_perfil_bd(user_id):
    # Busca as informações da tabela que você criou
    try:
        res = supabase.table("perfis").select("*").eq('user_id',user_id).execute()
        res = res.data[0]

        return res
    except:
        return None

st.set_page_config(page_title="Sistema de Acesso", layout="wide")
supabase = inicia_conexao_bancoDados()


if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.session = None
    
if st.session_state.user is None:   #   usuario não logou
    tab_login, tab_cadastro = st.tabs(["Acessar Conta", "Novo Registro"])

    with tab_login:
        with st.form("form_login"):
            email_log = st.text_input("E-mail")
            senha_log = st.text_input("Senha", type="password")
            
            if st.form_submit_button("Entrar"):
                usuario = realizar_login(email_log, senha_log)
                if usuario:
                    st.session_state.user = usuario.user
                    st.session_state.session = usuario.session
                    st.rerun()
    with tab_cadastro:
        st.write("Em desenvolvimento...")
    if False: # CADASTRO
        with st.form("form_cadastro"):
            novo_nome = st.text_input("Nome Completo")
            novo_dept = st.selectbox("Seu Departamento", ["Administrativo","Financeiro", "RH", "TI", "Logística"])
            novo_email = st.text_input("E-mail de Cadastro")
            nova_senha = st.text_input("Defina uma Senha", type="password", help="Mínimo 6 caracteres")
            
            if st.form_submit_button("Criar Conta"):
                if novo_nome and novo_email and len(nova_senha) >= 6:
                    cadastrar_usuario(novo_nome, novo_email, nova_senha, novo_dept)
                else:
                    st.warning("Preencha todos os campos corretamente.")
else:   # LOGIN CONCLUÍDO
    perfil = buscar_perfil_bd(st.session_state.user.id)    

    if 'perfil' not in st.session_state:
        st.session_state.perfil = perfil

    with st.sidebar:
        if st.button("Sair do Sistema"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
            
        st.markdown(f'### :blue[{perfil['nome']}] !')
        st.markdown(f"{perfil['role'].title()}")

    if st.button("Sair do Sistema"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    




    st.markdown('# Home')
    st.markdown(f'### Bem vindo :blue[{perfil['nome']}] !')
    c1, c2, c3 = st.columns(3)
    c1.metric('Departamento',f':blue[{perfil['dept']}]')
    c2.metric('Permisões',f' :blue[{perfil['role'].title()}]')
    
    if perfil:
        if perfil['status'] != 'ativo':
            st.error(f'Entrar em contato com equipe técnica - status [{perfil['status']}]')
            st.markdown('Devido ao :red[status pendente] alguns acessos poderão ser limitados')