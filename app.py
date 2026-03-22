from __future__ import annotations

from datetime import datetime

import streamlit as st

from db import get_connection
from ia_ui import render_ia_tab
from mv_dashboard import render_plataformas, render_recorrencia, render_tickets_descontos
from queries import authenticate_user, list_units_for_user
from sidebar import render_sidebar
from tabs import tab_cardapio, tab_clientes, tab_metas, tab_vendas
from theme import inject_global_css

LOGO_URL = "https://d7jztl9hjt0p1.cloudfront.net/1.0.0.119/assets/images/home/logo.png"

st.set_page_config(
    page_title="Ital In House",
    page_icon=LOGO_URL,
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_state():
    for k, v in {"user": None, "loja_atual": None, "chat": [], "page": "vendas"}.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────

def pagina_login():
    st.markdown("""
<style>
section[data-testid='stSidebar']{display:none!important}
.main .block-container{
    max-width:460px!important;margin:0 auto!important;padding-top:8vh!important;
}
</style>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div style='text-align:center;margin-bottom:32px'>
    <img src='{LOGO_URL}' style='height:64px;object-fit:contain;margin-bottom:10px'/>
    <div style='color:#5A5A65;font-size:.7rem;font-weight:600;
                letter-spacing:.1em;text-transform:uppercase;margin-top:4px'>
        Portal do Franqueado
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("#### Acesso ao portal")

    with st.form("login_form"):
        email  = st.text_input("E-mail ou username", placeholder="seu@italinhouse.com")
        senha  = st.text_input("Senha", type="password", placeholder="••••••••")
        submit = st.form_submit_button("Entrar", use_container_width=True)

    if submit:
        if not email or not senha:
            st.warning("Preencha todos os campos.")
        else:
            try:
                user_data = authenticate_user(email, senha)
            except Exception as e:
                st.error(f"Erro ao conectar ao banco: {e}")
                user_data = None

            if user_data is None:
                st.error("Credenciais inválidas.")
            else:
                user_id = int(user_data["id"])
                role    = (user_data.get("role") or "").strip().lower()
                try:
                    lojas = list_units_for_user(user_id, role, user_data.get("id_unidades") or [])
                except Exception:
                    lojas = []

                st.session_state.user = {
                    "id":    user_id,
                    "email": user_data["email"],
                    "nome":  user_data.get("nome_completo") or user_data.get("username"),
                    "role":  role,
                    "lojas": [dict(u) for u in lojas],
                }
                st.session_state.loja_atual = None
                st.session_state.chat       = []
                st.session_state.page       = "visao_geral" if role == "admin" else "vendas"
                st.rerun()


# ─────────────────────────────────────────────
#  POPUP SELEÇÃO LOJA (franqueado 2+ lojas)
# ─────────────────────────────────────────────

def popup_selecao_loja():
    st.markdown("""
<style>
section[data-testid='stSidebar']{display:none!important}
.main .block-container{
    max-width:480px!important;margin:0 auto!important;padding-top:10vh!important;
}
</style>
""", unsafe_allow_html=True)

    lojas = st.session_state.user["lojas"]
    nome  = (st.session_state.user.get("nome") or "").split()[0]

    st.markdown(f"""
<div style='text-align:center;margin-bottom:20px'>
  <img src='{LOGO_URL}' style='height:48px;object-fit:contain'/>
</div>
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:20px;
            padding:32px 28px;margin-bottom:12px'>
  <div style='font-size:1.2rem;font-weight:800;color:#F5F5F7;margin-bottom:4px'>
    Olá, {nome}! 👋
  </div>
  <div style='color:#5A5A65;font-size:.85rem;margin-bottom:20px'>
    Você tem acesso a {len(lojas)} unidade{'s' if len(lojas) != 1 else ''}.
    Qual deseja visualizar?
  </div>
</div>
""", unsafe_allow_html=True)

    for loja in lojas:
        estado = loja.get("short_desc_state") or loja.get("estado") or ""
        label  = f"🏪  {loja['trade_name']}" + (f"  ·  {estado}" if estado else "")
        if st.button(label, use_container_width=True, key=f"loja_{loja['id']}"):
            st.session_state.loja_atual = loja
            st.rerun()


# ─────────────────────────────────────────────
#  PAGE HEADER
# ─────────────────────────────────────────────

def _page_header(titulo: str, subtitulo: str = ""):
    data = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:flex-end;
            margin-bottom:20px;padding-bottom:12px;
            border-bottom:1px solid #2A2A2F'>
  <div>
    {'<div style="color:#5A5A65;font-size:.62rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px">' + subtitulo + '</div>' if subtitulo else ''}
    <div style='color:#F5F5F7;font-size:1.35rem;font-weight:800;
                letter-spacing:-.02em'>{titulo}</div>
  </div>
  <div style='color:#5A5A65;font-size:.72rem'>{data}</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  DASHBOARD FRANQUEADO
# ─────────────────────────────────────────────

def pagina_dashboard():
    loja  = st.session_state.loja_atual
    trade = loja["trade_name"]
    uid   = int(loja["id"])
    user  = st.session_state.user
    role  = (user.get("role") or "franqueado").lower()

    ctx = render_sidebar(role)
    page = ctx["page"]
    days = ctx["days"]

    # ── Roteamento por página ──
    PAGE_TITLES = {
        "vendas":      ("📈 Vendas",              f"Unidade · {trade}"),
        "cardapio":    ("🍽️ Cardápio & Itens",    f"Unidade · {trade}"),
        "clientes":    ("👥 Clientes",             f"Unidade · {trade}"),
        "metas":       ("🎯 Metas",                f"Unidade · {trade}"),
        "plataformas": ("📡 Plataformas",          f"Unidade · {trade}"),
        "tickets":     ("🎟️ Tickets & Descontos",  f"Unidade · {trade}"),
        "recorrencia": ("🔄 Recorrência",          f"Unidade · {trade}"),
        "ia":          ("🤖 IA - IH",              f"Unidade · {trade}"),
    }

    titulo, sub = PAGE_TITLES.get(page, ("Dashboard", trade))
    _page_header(titulo, sub)

    if   page == "vendas":      tab_vendas(trade, uid, days)
    elif page == "cardapio":    tab_cardapio(trade, days)
    elif page == "clientes":    tab_clientes(trade)
    elif page == "metas":       tab_metas(trade, uid)
    elif page == "plataformas": render_plataformas(trade)
    elif page == "tickets":     render_tickets_descontos(trade)
    elif page == "recorrencia": render_recorrencia(trade)
    elif page == "ia":          render_ia_tab(user, loja)
    else:                       tab_vendas(trade, uid, days)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    init_state()
    inject_global_css()

    # Etapa 1 — Login
    if st.session_state.user is None:
        pagina_login()
        st.stop()

    # Checa conexão
    try:
        get_connection()
    except Exception as e:
        st.error(f"Falha na conexão PostgreSQL: {e}")
        st.stop()

    role = (st.session_state.user.get("role") or "").strip().lower()

    # ── Admin → sempre painel admin ──
    if role == "admin":
        if st.session_state.loja_atual is None:
            st.session_state.loja_atual = {"id": None, "trade_name": "__admin__"}
        from admin_dashboard import render_admin_panel
        render_admin_panel()
        st.stop()

    # ── Franqueado → seleção de loja ──
    if st.session_state.loja_atual is None:
        st.markdown(
            "<style>section[data-testid='stSidebar']{display:none!important}</style>",
            unsafe_allow_html=True,
        )
        lojas = st.session_state.user.get("lojas") or []
        if len(lojas) == 0:
            st.error("Você não tem nenhuma loja vinculada. Contate o administrador.")
            st.stop()
        elif len(lojas) == 1:
            st.session_state.loja_atual = lojas[0]
            st.rerun()
        else:
            popup_selecao_loja()
        st.stop()

    pagina_dashboard()


if __name__ == "__main__":
    main()
