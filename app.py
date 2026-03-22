from __future__ import annotations

from datetime import datetime

import streamlit as st

from admin_dashboard import render_admin_panel
from db import get_connection
from ia_ui import render_ia_tab
from mv_dashboard import render_plataformas, render_recorrencia, render_tickets_descontos
from queries import authenticate_user, list_units_for_user
from tabs import fmt_brl, fmt_delta_pct, kpi_card, tab_cardapio, tab_clientes, tab_metas, tab_vendas
from theme import inject_global_css

st.set_page_config(
    page_title="Ital In House",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_state():
    for k, v in {"user": None, "loja_atual": None, "chat": []}.items():
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

    st.markdown("""
<div style='text-align:center;margin-bottom:32px'>
    <div style='font-size:2.4rem;font-weight:800;letter-spacing:-.02em'>
        <span style='color:#F5F5F7'>Ital</span>
        <span style='color:#C8102E'> In House</span>
    </div>
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
                    id_unidades = user_data.get("id_unidades") or []
                    lojas = list_units_for_user(user_id, role, id_unidades)
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
                st.rerun()


# ─────────────────────────────────────────────
#  SELEÇÃO DE LOJA (só franqueado com 2+ lojas)
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
#  DASHBOARD FRANQUEADO
# ─────────────────────────────────────────────

def pagina_dashboard():
    loja  = st.session_state.loja_atual
    trade = loja["trade_name"]
    uid   = int(loja["id"])
    user  = st.session_state.user
    lojas = user["lojas"]
    role  = (user.get("role") or "franqueado").lower()

    # ── Sidebar ──
    with st.sidebar:
        st.markdown(f"""
<div style='text-align:center;padding:8px 0 14px'>
    <div style='font-size:1.15rem;font-weight:800;letter-spacing:-.02em'>
        <span style='color:#F5F5F7'>Ital</span>
        <span style='color:#C8102E'> In House</span>
    </div>
    <div style='color:#5A5A65;font-size:.58rem;font-weight:600;
                letter-spacing:.09em;text-transform:uppercase;margin-top:2px'>
        Portal do Franqueado
    </div>
</div>
<hr style='border-color:#2A2A2F;margin:0 0 12px'>
<div style='background:#1C1C1F;border:1px solid #2A2A2F;border-radius:10px;
            padding:10px 12px;margin-bottom:12px'>
    <div style='display:flex;align-items:center;gap:10px'>
        <div style='width:32px;height:32px;border-radius:50%;background:#C8102E;
                    display:flex;align-items:center;justify-content:center;
                    color:white;font-size:.68rem;font-weight:800;flex-shrink:0'>
            {(user.get("nome") or "?")[:2].upper()}
        </div>
        <div>
            <div style='color:#F5F5F7;font-size:.78rem;font-weight:700;line-height:1.2'>
                {user.get("nome") or "Usuário"}
            </div>
            <div style='color:#C8102E;font-size:.6rem;font-weight:600;
                        letter-spacing:.06em;text-transform:uppercase'>
                {role.capitalize()}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        if len(lojas) > 1:
            st.markdown(
                "<div style='color:#5A5A65;font-size:.6rem;font-weight:600;"
                "letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px'>"
                "Unidade</div>", unsafe_allow_html=True)
            nomes     = [l["trade_name"] for l in lojas]
            idx_atual = nomes.index(trade) if trade in nomes else 0
            escolha   = st.selectbox("", nomes, index=idx_atual,
                                     key="sb_loja_sel", label_visibility="collapsed")
            if escolha != trade:
                nova = next(l for l in lojas if l["trade_name"] == escolha)
                st.session_state.loja_atual = nova
                st.session_state.chat = []
                st.rerun()

        st.markdown(
            "<div style='color:#5A5A65;font-size:.6rem;font-weight:600;"
            "letter-spacing:.08em;text-transform:uppercase;margin:12px 0 4px'>"
            "Período (gráficos diários)</div>", unsafe_allow_html=True)
        days = st.selectbox("", [7, 30, 90], index=1, key="sb_days",
                            label_visibility="collapsed",
                            format_func=lambda x: f"{x} dias")

        st.markdown("<hr style='border-color:#2A2A2F;margin:12px 0'>",
                    unsafe_allow_html=True)

        if st.button("🚪 Sair", use_container_width=True, key="sb_sair"):
            st.session_state.user       = None
            st.session_state.loja_atual = None
            st.session_state.chat       = []
            st.rerun()

    # ── Header ──
    st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:16px'>
    <div>
        <div style='color:#5A5A65;font-size:.62rem;font-weight:600;
                    letter-spacing:.1em;text-transform:uppercase'>Dashboard</div>
        <div style='color:#F5F5F7;font-size:1.45rem;font-weight:800;
                    letter-spacing:-.02em;margin-top:2px'>🏪 {trade}</div>
    </div>
    <div style='color:#C8102E;font-size:.72rem;font-weight:600'>
        {datetime.now().strftime("%d/%m/%Y %H:%M")}
    </div>
</div>
""", unsafe_allow_html=True)

    # ── Tabs ──
    t1, t2, t3, t4, t_plat, t_tick, t_recorr, t_ia = st.tabs([
        "📈  Vendas",
        "🍽️  Cardápio & Itens",
        "👥  Clientes",
        "🎯  Metas",
        "📡  Plataformas",
        "🎟️  Tickets & Descontos",
        "🔄  Recorrência",
        "🤖  IA - IH",
    ])

    with t1:
        tab_vendas(trade, uid, days)
    with t2:
        tab_cardapio(trade, days)
    with t3:
        tab_clientes(trade)
    with t4:
        tab_metas(trade, uid)
    with t_plat:
        render_plataformas(trade)
    with t_tick:
        render_tickets_descontos(trade)
    with t_recorr:
        render_recorrencia(trade)
    with t_ia:
        render_ia_tab(st.session_state.user, st.session_state.loja_atual)


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

    # ── Admin → SEMPRE painel admin, nunca sai dele ──
    if role == "admin":
        if st.session_state.loja_atual is None:
            st.session_state.loja_atual = {"id": None, "trade_name": "__admin__"}
        render_admin_panel()
        st.stop()

    # ── Franqueado → seleção de loja ou dashboard ──
    if st.session_state.loja_atual is None:
        st.markdown(
            "<style>section[data-testid='stSidebar']{display:none!important}</style>",
            unsafe_allow_html=True,
        )
        lojas = st.session_state.user.get("lojas") or []
        if len(lojas) == 1:
            st.session_state.loja_atual = lojas[0]
            st.rerun()
        elif len(lojas) == 0:
            st.error("Você não tem nenhuma loja vinculada. Contate o administrador.")
            st.stop()
        else:
            popup_selecao_loja()
        st.stop()

    pagina_dashboard()


if __name__ == "__main__":
    main()
