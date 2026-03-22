"""
Sidebar profissional — Ital In House
Dois estados: expandida (ícone + nome) e colapsada (só ícones).
Navegação via st.session_state.page — sem recarregar o app.
"""

from datetime import datetime

import streamlit as st

LOGO_URL = "https://d7jztl9hjt0p1.cloudfront.net/1.0.0.119/assets/images/home/logo.png"

# ─────────────────────────────────────────────
#  MENU CONFIG
# ─────────────────────────────────────────────

MENU_FRANQUEADO = [
    {"id": "vendas",       "icon": "📈", "label": "Vendas"},
    {"id": "cardapio",     "icon": "🍽️", "label": "Cardápio & Itens"},
    {"id": "clientes",     "icon": "👥", "label": "Clientes"},
    {"id": "metas",        "icon": "🎯", "label": "Metas"},
    {"id": "plataformas",  "icon": "📡", "label": "Plataformas"},
    {"id": "tickets",      "icon": "🎟️", "label": "Tickets & Descontos"},
    {"id": "recorrencia",  "icon": "🔄", "label": "Recorrência"},
    {"id": "ia",           "icon": "🤖", "label": "IA - IH"},
]

MENU_ADMIN = [
    {"id": "visao_geral",  "icon": "📊", "label": "Visão Geral"},
    {"id": "ranking",      "icon": "🏆", "label": "Ranking"},
    {"id": "vendas",       "icon": "📈", "label": "Vendas"},
    {"id": "cardapio",     "icon": "🍽️", "label": "Cardápio"},
    {"id": "clientes",     "icon": "👥", "label": "Clientes"},
    {"id": "metas",        "icon": "🎯", "label": "Metas"},
    {"id": "plataformas",  "icon": "📡", "label": "Plataformas"},
    {"id": "tickets",      "icon": "🎟️", "label": "Tickets"},
    {"id": "recorrencia",  "icon": "🔄", "label": "Recorrência"},
    {"id": "usuarios",     "icon": "👤", "label": "Usuários"},
    {"id": "ia",           "icon": "🤖", "label": "IA - IH"},
]

# ─────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────

def _inject_sidebar_css(collapsed: bool):
    width     = "64px"  if collapsed else "240px"
    txt_disp  = "none"  if collapsed else "block"
    logo_disp = "none"  if collapsed else "block"
    sub_disp  = "none"  if collapsed else "block"
    search_disp = "none" if collapsed else "block"
    sec_disp  = "none"  if collapsed else "block"

    st.markdown(f"""
<style>
/* ── Sidebar container ── */
[data-testid="stSidebar"] > div:first-child {{
    width: {width} !important;
    min-width: {width} !important;
    max-width: {width} !important;
    background: #141416 !important;
    border-right: 1px solid #2A2A2F !important;
    padding: 0 !important;
    transition: width .25s ease;
    overflow-x: hidden !important;
}}
[data-testid="stSidebar"] {{
    width: {width} !important;
    min-width: {width} !important;
    transition: width .25s ease;
}}
/* Ajusta conteúdo principal */
.main .block-container {{
    padding-left: 1.5rem !important;
    padding-top: 1rem !important;
}}

/* ── Esconde toggle nativo ── */
[data-testid="collapsedControl"] {{ display: none !important; }}
button[data-testid="baseButton-header"] {{ display: none !important; }}

/* ── Esconde textos quando colapsado ── */
.sb-txt       {{ display: {txt_disp} !important; }}
.sb-logo-img  {{ display: {logo_disp} !important; }}
.sb-sub       {{ display: {sub_disp} !important; }}
.sb-search    {{ display: {search_disp} !important; }}
.sb-sec-label {{ display: {sec_disp} !important; }}
.sb-footer-txt{{ display: {txt_disp} !important; }}

/* ── Scrollbar fina ── */
[data-testid="stSidebar"] ::-webkit-scrollbar {{ width: 4px; }}
[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {{
    background: #2A2A2F; border-radius: 2px;
}}

/* ── Remove padding padrão do sidebar ── */
[data-testid="stSidebar"] .block-container {{
    padding: 0 !important;
    margin: 0 !important;
}}
[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important;
    border: none !important;
    color: #A0A0A8 !important;
    font-weight: 500 !important;
    font-size: .82rem !important;
    text-align: left !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    transition: background .15s, color .15s !important;
    width: 100% !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: #1C1C1F !important;
    color: #F5F5F7 !important;
}}

/* Botão ativo */
[data-testid="stSidebar"] .stButton.active-btn > button {{
    background: rgba(200,16,46,.15) !important;
    color: #C8102E !important;
    font-weight: 700 !important;
    border-left: 3px solid #C8102E !important;
    padding-left: 9px !important;
}}

/* Selectbox */
[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
    background: #0C0C0E !important;
    border: 1px solid #2A2A2F !important;
    border-radius: 8px !important;
    font-size: .78rem !important;
}}
[data-testid="stSidebar"] .stSelectbox label {{
    font-size: .6rem !important;
    color: #5A5A65 !important;
    font-weight: 600 !important;
    letter-spacing: .08em !important;
    text-transform: uppercase !important;
}}

/* Input de busca */
[data-testid="stSidebar"] div[data-baseweb="input"] > div {{
    background: #1C1C1F !important;
    border: 1px solid #2A2A2F !important;
    border-radius: 8px !important;
    font-size: .8rem !important;
}}
[data-testid="stSidebar"] div[data-baseweb="input"]:focus-within > div {{
    border-color: #C8102E !important;
}}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  RENDER SIDEBAR
# ─────────────────────────────────────────────

def render_sidebar(role: str) -> dict:
    """
    Renderiza a sidebar e retorna:
    {
      "page": str,      # página ativa
      "days": int,      # período selecionado
      "trade": str,     # loja selecionada (trade_name) ou None
      "loja_obj": dict, # dict completo da loja ou None
    }
    """
    user  = st.session_state.user or {}
    lojas = user.get("lojas") or []

    # ── Inicializa estados ──
    if "sidebar_collapsed" not in st.session_state:
        st.session_state.sidebar_collapsed = False

    if "page" not in st.session_state:
        st.session_state.page = "visao_geral" if role == "admin" else "vendas"

    if "sb_search" not in st.session_state:
        st.session_state.sb_search = ""

    collapsed = st.session_state.sidebar_collapsed
    menu      = MENU_ADMIN if role == "admin" else MENU_FRANQUEADO

    _inject_sidebar_css(collapsed)

    with st.sidebar:
        # ── TOPO: Logo + Hamburger ──
        col_logo, col_ham = st.columns([0.78, 0.22]) if not collapsed else st.columns([0.1, 0.9])
        with col_logo:
            if not collapsed:
                st.markdown(f"""
<div style='padding:14px 12px 8px'>
  <img src='{LOGO_URL}' class='sb-logo-img'
       style='height:32px;object-fit:contain;display:block'/>
  <div class='sb-sub' style='color:#5A5A65;font-size:.55rem;font-weight:600;
              letter-spacing:.1em;text-transform:uppercase;margin-top:5px'>
    Portal {'Admin' if role == 'admin' else 'do Franqueado'}
  </div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        with col_ham:
            st.markdown("<div style='padding-top:12px'>", unsafe_allow_html=True)
            icon = "◀" if not collapsed else "▶"
            if st.button(icon, key="sb_toggle", help="Expandir/Recolher menu"):
                st.session_state.sidebar_collapsed = not collapsed
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#2A2A2F;margin:0 0 8px'>",
                    unsafe_allow_html=True)

        # ── BUSCA ──
        if not collapsed:
            st.markdown("<div class='sb-search' style='padding:0 10px 8px'>",
                        unsafe_allow_html=True)
            busca = st.text_input("", placeholder="🔍  Buscar página...",
                                  key="sb_search_input",
                                  label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            busca = ""

        # ── MENU ──
        if not collapsed:
            st.markdown(
                "<div class='sb-sec-label' style='color:#5A5A65;font-size:.58rem;"
                "font-weight:700;letter-spacing:.1em;text-transform:uppercase;"
                "padding:0 12px 6px'>Menu</div>",
                unsafe_allow_html=True,
            )

        # Filtra itens pelo busca
        itens = [m for m in menu
                 if busca.lower() in m["label"].lower()] if busca else menu

        for item in itens:
            is_active = (st.session_state.page == item["id"])
            label     = item["icon"] if collapsed else f"{item['icon']}  {item['label']}"

            # Marca o botão ativo via CSS injection temporário
            if is_active:
                st.markdown(f"""
<style>
div[data-testid="stSidebar"] div[data-testid="stButton"]:has(button[kind="secondary"]:nth-of-type(1)) {{}}
</style>
<div style='padding:0 8px 2px'>
  <div style='background:rgba(200,16,46,.12);border-left:3px solid #C8102E;
              border-radius:8px;padding:8px 12px;display:flex;align-items:center;
              gap:8px;cursor:default'>
    <span style='font-size:1rem'>{item['icon']}</span>
    {'<span class="sb-txt" style="color:#C8102E;font-size:.82rem;font-weight:700">'
     + item['label'] + '</span>' if not collapsed else ''}
  </div>
</div>""", unsafe_allow_html=True)
            else:
                if st.button(label, key=f"nav_{item['id']}", use_container_width=True):
                    st.session_state.page = item["id"]
                    st.rerun()

        # ── FILTROS ──
        st.markdown("<hr style='border-color:#2A2A2F;margin:10px 0 8px'>",
                    unsafe_allow_html=True)

        if not collapsed:
            st.markdown(
                "<div class='sb-sec-label' style='color:#5A5A65;font-size:.58rem;"
                "font-weight:700;letter-spacing:.1em;text-transform:uppercase;"
                "padding:0 12px 6px'>Filtros</div>",
                unsafe_allow_html=True,
            )

        # Seletor de loja
        loja_obj  = None
        trade_sel = None

        if collapsed:
            # Modo colapsado: só mostra ícone de loja
            st.markdown("<div style='text-align:center;padding:6px 0;color:#5A5A65;font-size:1rem'>🏪</div>",
                        unsafe_allow_html=True)
        else:
            if role == "admin":
                opts    = ["— Todas as lojas —"] + [l["trade_name"] for l in lojas]
                loja_cur = st.session_state.loja_atual or {}
                trade_cur = loja_cur.get("trade_name") or ""
                idx_cur  = opts.index(trade_cur) if trade_cur in opts else 0
                escolha  = st.selectbox("Loja", opts, index=idx_cur,
                                        key="sb_loja_adm", label_visibility="visible")
                if escolha == "— Todas as lojas —":
                    loja_obj  = {"id": None, "trade_name": "__admin__"}
                    trade_sel = None
                else:
                    loja_obj  = next((l for l in lojas if l["trade_name"] == escolha), None)
                    trade_sel = escolha

            elif len(lojas) > 1:
                nomes    = [l["trade_name"] for l in lojas]
                cur_trade = (st.session_state.loja_atual or {}).get("trade_name", "")
                idx_cur   = nomes.index(cur_trade) if cur_trade in nomes else 0
                escolha   = st.selectbox("Loja", nomes, index=idx_cur,
                                         key="sb_loja_franc", label_visibility="visible")
                loja_obj  = next((l for l in lojas if l["trade_name"] == escolha), None)
                trade_sel = escolha
            else:
                if lojas:
                    loja_obj  = lojas[0]
                    trade_sel = lojas[0]["trade_name"]
                    st.markdown(
                        f"<div style='padding:0 12px 4px'>"
                        f"<div style='color:#5A5A65;font-size:.58rem;font-weight:600;"
                        f"letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px'>Loja</div>"
                        f"<div style='color:#F5F5F7;font-size:.75rem;font-weight:700;"
                        f"background:#1C1C1F;border-radius:8px;padding:7px 10px'>"
                        f"🏪 {trade_sel}</div></div>",
                        unsafe_allow_html=True,
                    )

        # Período
        if collapsed:
            st.markdown("<div style='text-align:center;padding:6px 0;color:#5A5A65;font-size:1rem'>📅</div>",
                        unsafe_allow_html=True)
        else:
            days = st.selectbox("Período", [7, 30, 90], index=1,
                                key="sb_days", label_visibility="visible",
                                format_func=lambda x: f"{x} dias")

        # ── FOOTER: usuário ──
        nome    = user.get("nome") or "Usuário"
        iniciais = "".join(p[0].upper() for p in nome.split()[:2]) or "?"
        role_label = "Admin" if role == "admin" else "Franqueado"

        st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#2A2A2F;margin:12px 0 0'>",
                    unsafe_allow_html=True)

        if collapsed:
            st.markdown(f"""
<div style='text-align:center;padding:10px 0'>
  <div style='width:32px;height:32px;border-radius:50%;background:#C8102E;
              display:inline-flex;align-items:center;justify-content:center;
              color:white;font-size:.68rem;font-weight:800'>{iniciais}</div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div style='padding:10px 12px 14px;display:flex;align-items:center;gap:10px'>
  <div style='width:34px;height:34px;border-radius:50%;background:#C8102E;
              display:flex;align-items:center;justify-content:center;
              color:white;font-size:.7rem;font-weight:800;flex-shrink:0'>{iniciais}</div>
  <div style='flex:1;min-width:0' class='sb-footer-txt'>
    <div style='color:#F5F5F7;font-size:.78rem;font-weight:700;
                white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{nome}</div>
    <div style='color:#C8102E;font-size:.6rem;font-weight:600;
                letter-spacing:.06em;text-transform:uppercase'>{role_label}</div>
  </div>
  <div style='flex-shrink:0'>
""", unsafe_allow_html=True)

        # Botão sair
        if not collapsed:
            if st.button("🚪", key="sb_sair", help="Sair"):
                for k in ["user", "loja_atual", "chat", "page"]:
                    st.session_state.pop(k, None)
                st.rerun()
            st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            if st.button("🚪", key="sb_sair_col", help="Sair", use_container_width=True):
                for k in ["user", "loja_atual", "chat", "page"]:
                    st.session_state.pop(k, None)
                st.rerun()

    # ── Sincroniza loja_atual com session_state ──
    if loja_obj and loja_obj != st.session_state.get("loja_atual"):
        st.session_state.loja_atual = loja_obj
        st.session_state.chat = []
        st.rerun()

    # ── Retorna contexto para o app usar ──
    days_val = st.session_state.get("sb_days", 30)

    return {
        "page":     st.session_state.page,
        "days":     days_val,
        "trade":    trade_sel or (st.session_state.loja_atual or {}).get("trade_name"),
        "loja_obj": loja_obj or st.session_state.get("loja_atual"),
    }
