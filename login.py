import streamlit as st
from supabase import create_client, Client

# Configurações do Supabase (Substitua pelos seus dados)
SUPABASE_URL = st.secrets["SUPABASE"]["URL"]
SUPABASE_KEY = st.secrets["SUPABASE"]["KEY"]

# Inicializa o cliente
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# --- Funções de Lógica ---

def realizar_login(email, senha):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        return res.user
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

def buscar_dados_perfil(user_id):
    # Busca as informações da tabela que você criou
    try:
        res = supabase.table("perfis").select("*").eq("id", user_id).single().execute()
        return res.data
    except:
        return None

# --- Interface Streamlit ---

st.set_page_config(page_title="Sistema de Acesso", layout="wide")
if "user" not in st.session_state:
    st.session_state.user = None
    
if st.session_state.user is None:
    tab_login, tab_cadastro = st.tabs(["Acessar Conta", "Novo Registro"])

    with tab_login:
        with st.form("form_login"):
            email_log = st.text_input("E-mail")
            senha_log = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                usuario = realizar_login(email_log, senha_log)
                if usuario:
                    st.session_state.user = usuario
                    st.rerun()

    with tab_cadastro:
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

else:
    # Carregamos os dados do perfil do banco
    perfil = buscar_dados_perfil(st.session_state.user.id)
    user_primeiro_nome = perfil["nome"].split()[0]
    
    # Sidebar
    st.sidebar.title("Menu")
    if perfil:
        with st.sidebar:
            st.markdown(f"Usuário: {perfil['nome']}")
            st.markdown(f"Dep: {perfil['dept']}")

            if st.button("Sair do Sistema"):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()

    # Conteúdo Principal
    st.title("Página Principal")
    
    if perfil:
        st.markdown(f"### Bem-vindo(a), :blue[{user_primeiro_nome}] !")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Status", perfil['status'])
        col2.metric("Departamento", perfil['dept'])
        col3.metric("Permissão", perfil['permissoes'])
    else:
        st.warning("Seu perfil ainda não foi processado ou o e-mail não foi confirmado.")