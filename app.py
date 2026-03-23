"""
App principal — Ital In House
Admin e Franqueado usam o mesmo painel unificado (render_admin_panel).
A lógica de permissão e visual é gerenciada dentro do admin_dashboard.py.
"""

from __future__ import annotations

import streamlit as st

from db import get_connection
from queries import authenticate_user, list_units_for_user
from theme import inject_global_css

LOGO_URL = "https://d7jztl9hjt0p1.cloudfront.net/1.0.0.119/assets/images/home/logo.png"

st.set_page_config(
    page_title="Ital In House",
    page_icon=LOGO_URL,
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _init():
    for k, v in {"user": None, "loja_atual": None, "chat": []}.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────

def _login():
    st.markdown("""
<style>
section[data-testid='stSidebar']{display:none!important}
header[data-testid="stHeader"]{display:none!important}
.main .block-container{
    max-width:460px!important;
    margin:0 auto!important;
    padding-top:8vh!important;
}
</style>""", unsafe_allow_html=True)

    st.markdown(f"""
<div style='text-align:center;margin-bottom:32px'>
  <img src='{LOGO_URL}'
       style='height:68px;object-fit:contain;margin-bottom:12px'/>
  <div style='color:#5A5A65;font-size:.68rem;font-weight:600;
              letter-spacing:.14em;text-transform:uppercase'>
    Portal do Franqueado
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("#### Acesso ao portal")

    with st.form("login_form"):
        email  = st.text_input("E-mail ou username", placeholder="seu@italinhouse.com")
        senha  = st.text_input("Senha", type="password", placeholder="••••••••")
        submit = st.form_submit_button("Entrar →", use_container_width=True)

    if submit:
        if not email or not senha:
            st.warning("Preencha e-mail e senha.")
            return

        try:
            user_data = authenticate_user(email.strip(), senha)
        except Exception as e:
            st.error(f"Erro na conexão: {e}")
            return

        if user_data is None:
            st.error("Credenciais inválidas. Verifique e-mail e senha.")
            return

        user_id = int(user_data["id"])
        role    = (user_data.get("role") or "franqueado").strip().lower()

        try:
            lojas = list_units_for_user(user_id, role, user_data.get("id_unidades") or [])
        except Exception:
            lojas = []

        st.session_state.user = {
            "id":    user_id,
            "email": user_data.get("email", ""),
            "nome":  user_data.get("nome_completo") or user_data.get("username") or "Usuário",
            "role":  role,
            "lojas": [dict(u) for u in lojas],
        }
        st.session_state.chat = []

        # Loja inicial
        if role == "admin":
            st.session_state.loja_atual = {"id": None, "trade_name": "__admin__"}
        elif len(lojas) == 1:
            st.session_state.loja_atual = dict(lojas[0])
        else:
            st.session_state.loja_atual = None  # popup de seleção

        st.rerun()


# ─────────────────────────────────────────────
#  POPUP SELEÇÃO LOJA (franqueado 2+ lojas)
# ─────────────────────────────────────────────

def _selecao_loja():
    st.markdown("""
<style>
section[data-testid='stSidebar']{display:none!important}
header[data-testid="stHeader"]{display:none!important}
.main .block-container{
    max-width:500px!important;
    margin:0 auto!important;
    padding-top:10vh!important;
}
</style>""", unsafe_allow_html=True)

    user  = st.session_state.user
    lojas = user["lojas"]
    nome  = (user.get("nome") or "").split()[0]

    st.markdown(f"""
<div style='text-align:center;margin-bottom:24px'>
  <img src='{LOGO_URL}' style='height:52px;object-fit:contain'/>
</div>
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:20px;
            padding:32px 28px;margin-bottom:12px'>
  <div style='font-size:1.2rem;font-weight:800;color:#F5F5F7;margin-bottom:6px'>
    Olá, {nome}! 👋
  </div>
  <div style='color:#5A5A65;font-size:.85rem;margin-bottom:22px'>
    Você tem acesso a <strong style='color:#A0A0A8'>{len(lojas)} unidades</strong>.
    Selecione qual deseja visualizar:
  </div>
</div>""", unsafe_allow_html=True)

    for loja in lojas:
        estado = loja.get("short_desc_state") or loja.get("estado") or ""
        label  = f"🏪  {loja['trade_name']}" + (f"  ·  {estado}" if estado else "")
        if st.button(label, use_container_width=True, key=f"sel_{loja['id']}"):
            st.session_state.loja_atual = dict(loja)
            st.rerun()


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    _init()
    inject_global_css()

    # 1. Não logado → login
    if st.session_state.user is None:
        _login()
        st.stop()

    # 2. Checa conexão DB
    try:
        get_connection()
    except Exception as e:
        st.error(f"Falha na conexão com o banco de dados: {e}")
        st.stop()

    user  = st.session_state.user
    role  = (user.get("role") or "franqueado").lower()
    lojas = user.get("lojas") or []

    # 3. Franqueado sem loja selecionada → seleção ou erro
    if role != "admin" and st.session_state.loja_atual is None:
        st.markdown(
            "<style>section[data-testid='stSidebar']{display:none!important}"
            "header[data-testid='stHeader']{display:none!important}</style>",
            unsafe_allow_html=True,
        )
        if len(lojas) == 0:
            st.error("❌ Você não tem nenhuma loja vinculada. Contate o administrador.")
            if st.button("🚪 Sair"):
                st.session_state.clear()
                st.rerun()
            st.stop()
        elif len(lojas) == 1:
            st.session_state.loja_atual = dict(lojas[0])
            st.rerun()
        else:
            _selecao_loja()
            st.stop()

    # 4. Admin e Franqueado com loja → painel unificado
    from admin_dashboard import render_admin_panel
    render_admin_panel()


if __name__ == "__main__":
    main()
