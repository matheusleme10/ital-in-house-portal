from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pandas as pd
import streamlit as st

from admin_dashboard import render_admin_panel
from ia_ui import render_ia_tab
from charts import (
    fig_barras_pedidos,
    fig_faturamento_diario,
    fig_faixa_freq,
    fig_gauge_metas,
    fig_metas_agrupadas,
    fig_pizza_categoria,
    fig_pizza_status,
    fig_scatter_rfm,
    fig_top_itens_horizontal,
)
from db import get_connection
from mv_dashboard import render_plataformas, render_recorrencia, render_tickets_descontos
from queries import (
    authenticate_user,
    clientes_faixa_frequencia,
    clientes_rfm_points,
    clientes_top50,
    itens_cardapio_list,
    kpi_clientes,
    kpi_vendas,
    kpi_vendas_extras,
    list_units_for_user,
    meta_mes_atual,
    metas_historico,
    pedidos_por_dia,
    receita_por_categoria,
    serie_temporal,
    status_vendas,
    top_itens,
)
from theme import inject_global_css

st.set_page_config(
    page_title="Ital In House",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _f(x) -> float:
    if x is None:
        return 0.0
    if isinstance(x, Decimal):
        return float(x)
    return float(x)


def fmt_brl(x) -> str:
    s = f"{_f(x):,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_delta_pct(cur: float, prev: float) -> tuple[str, str]:
    if prev == 0:
        if cur == 0:
            return "0%", "pos"
        return "↑ 100%", "pos"
    d = (cur - prev) / prev * 100
    if d >= 0:
        return f"↑ {abs(d):.1f}%", "pos"
    return f"↓ {abs(d):.1f}%", "neg"


def kpi_card(
    title: str,
    value: str,
    delta_text: str | None,
    delta_pos: bool | None,
    progress_pct: float,
    bar_label: str,
) -> None:
    p = max(0.0, min(float(progress_pct), 100.0))
    delta = ""
    if delta_text is not None and delta_pos is not None:
        cls = "ih-kpi-delta-pos" if delta_pos else "ih-kpi-delta-neg"
        delta = f'<span class="{cls}">{delta_text}</span>'
    st.markdown(f"""
<div class="ih-kpi-wrap">
  <div class="ih-kpi-head">
    <span class="ih-kpi-title">{title}</span>
    {delta}
  </div>
  <div class="ih-kpi-value">{value}</div>
  <div class="ih-kpi-bar-bg"><div class="ih-kpi-bar-fill" style="width:{p}%;"></div></div>
  <div class="ih-kpi-bar-label">{bar_label}</div>
</div>
""", unsafe_allow_html=True)


def init_state():
    for k, v in {"user": None, "loja_atual": None, "chat": []}.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────
#  PÁGINAS
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
        email  = st.text_input("E-mail", placeholder="seu@italinhouse.com")
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


def pagina_admin():
    render_admin_panel()


# ─────────────────────────────────────────────
#  DASHBOARD FRANQUEADO
# ─────────────────────────────────────────────

def pagina_dashboard():
    loja  = st.session_state.loja_atual
    trade = loja["trade_name"]
    uid   = int(loja["id"])
    user  = st.session_state.user
    lojas = user["lojas"]

    # ── Sidebar ──────────────────────────────
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
                        letter-spacing:.06em;text-transform:uppercase'>Franqueado</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        # Seletor de loja (só se tiver 2+)
        if len(lojas) > 1:
            st.markdown(
                "<div style='color:#5A5A65;font-size:.6rem;font-weight:600;"
                "letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px'>"
                "Unidade</div>",
                unsafe_allow_html=True,
            )
            nomes     = [l["trade_name"] for l in lojas]
            idx_atual = nomes.index(trade) if trade in nomes else 0
            escolha   = st.selectbox("", nomes, index=idx_atual,
                                     key="sb_loja_sel",
                                     label_visibility="collapsed")
            if escolha != trade:
                nova = next(l for l in lojas if l["trade_name"] == escolha)
                st.session_state.loja_atual = nova
                st.session_state.chat = []
                st.rerun()

        st.markdown(
            "<div style='color:#5A5A65;font-size:.6rem;font-weight:600;"
            "letter-spacing:.08em;text-transform:uppercase;margin:12px 0 4px'>"
            "Período (gráficos diários)</div>",
            unsafe_allow_html=True,
        )
        days = st.selectbox("", [7, 30, 90], index=1,
                            key="sb_days",
                            label_visibility="collapsed",
                            format_func=lambda x: f"{x} dias")

        st.markdown("<hr style='border-color:#2A2A2F;margin:12px 0'>",
                    unsafe_allow_html=True)

        if st.button("🚪 Sair", use_container_width=True, key="sb_sair"):
            st.session_state.user       = None
            st.session_state.loja_atual = None
            st.session_state.chat       = []
            st.rerun()

    # ── Header ───────────────────────────────
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

    # ── Tabs ─────────────────────────────────
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
#  TABS EXISTENTES
# ─────────────────────────────────────────────

def tab_vendas(trade: str, unidade_id: int, days: int):
    kv   = kpi_vendas(trade) or {}
    kx   = kpi_vendas_extras(trade) or {}
    meta = meta_mes_atual(unidade_id) or {}

    mes_atual = _f(kv.get("mes_atual"))
    mes_ant   = _f(kv.get("mes_anterior"))
    hoje      = _f(kv.get("hoje"))
    ontem     = _f(kx.get("fat_ontem"))
    ped_hj    = int(kv.get("pedidos_hoje") or 0)
    ped_ont   = int(kx.get("pedidos_ontem") or 0)
    ticket    = _f(kv.get("ticket_medio_geral"))
    ticket_ma = _f(kx.get("ticket_mes_anterior"))

    d1, d1b = fmt_delta_pct(mes_atual, mes_ant)
    prog1 = 0.0
    if meta and _f(meta.get("meta_vendas")) > 0:
        prog1 = _f(meta.get("realizado_vendas")) / _f(meta.get("meta_vendas")) * 100
    elif mes_ant > 0:
        prog1 = min(100.0, mes_atual / mes_ant * 100)
    else:
        prog1 = min(100.0, mes_atual / max(mes_atual, 1) * 100) if mes_atual else 0.0

    d2, d2b = fmt_delta_pct(float(ped_hj), float(ped_ont))
    prog2   = min(100.0, float(ped_hj) / max(float(ped_ont), 1.0) * 100) if ped_ont or ped_hj else 0.0

    d3, d3b = fmt_delta_pct(ticket, ticket_ma)
    prog3   = min(100.0, ticket / max(ticket_ma, 0.01) * 100) if ticket_ma or ticket else 0.0

    d4, d4b = fmt_delta_pct(hoje, ontem)
    prog4   = min(100.0, hoje / max(ontem, 0.01) * 100) if ontem or hoje else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Faturamento mês", fmt_brl(mes_atual), d1, d1b == "pos",
                 prog1, f"Meta / progresso: {prog1:.0f}%")
    with c2:
        kpi_card("Pedidos hoje", str(ped_hj), d2, d2b == "pos",
                 prog2, f"vs ontem: {ped_ont} pedidos")
    with c3:
        kpi_card("Ticket médio", fmt_brl(ticket), d3, d3b == "pos",
                 prog3, "vs ticket mês anterior")
    with c4:
        kpi_card("Faturamento hoje", fmt_brl(hoje), d4, d4b == "pos",
                 prog4, f"vs ontem: {fmt_brl(ontem)}")

    df_s  = pd.DataFrame(serie_temporal(trade, days))
    df_p  = pd.DataFrame(pedidos_por_dia(trade, days))
    df_st = pd.DataFrame(status_vendas(trade, days))

    a1, a2 = st.columns((1.4, 1))
    with a1:
        if not df_s.empty:
            st.plotly_chart(fig_faturamento_diario(df_s), use_container_width=True,
                            key="fig_faturamento_diario")
        else:
            st.info("Sem dados de série temporal")
    with a2:
        if not df_st.empty:
            st.plotly_chart(fig_pizza_status(df_st), use_container_width=True,
                            key="fig_pizza_status")
        else:
            st.info("Sem dados de status")

    if not df_p.empty:
        st.plotly_chart(fig_barras_pedidos(df_p), use_container_width=True,
                        key="fig_barras_pedidos")
    else:
        st.info("Sem dados de pedidos por dia")


def tab_cardapio(trade: str, days: int):
    rows = top_itens(trade, days, 15)
    df   = pd.DataFrame(rows)
    top1 = rows[0] if rows else None

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Item mais vendido",
                 (top1 or {}).get("produto") or "—",
                 None, None, 100.0 if top1 else 0.0, "Por receita no período")
    with c2:
        q = int((top1 or {}).get("qtd_vendida") or 0)
        kpi_card("Quantidade (top 1)", f"{q}", None, None,
                 min(100.0, q / max(q, 1) * 100), "Unidades vendidas")
    with c3:
        rec = _f((top1 or {}).get("receita_total"))
        kpi_card("Receita (top 1)", fmt_brl(rec), None, None,
                 100.0 if rec else 0.0, "Receita no período")

    b1, b2 = st.columns((1.2, 1))
    with b1:
        if not df.empty:
            st.plotly_chart(fig_top_itens_horizontal(df, 10), use_container_width=True,
                            key="fig_top_itens_horizontal")
        else:
            st.info("Sem dados de itens")
    with b2:
        df_cat = pd.DataFrame(receita_por_categoria(trade, days))
        if not df_cat.empty:
            st.plotly_chart(fig_pizza_categoria(df_cat), use_container_width=True,
                            key="fig_pizza_categoria")
        else:
            st.info("Sem dados de categoria")

    st.subheader("Detalhe — top itens")
    if df.empty:
        st.info("Sem dados de itens no período.")
    else:
        show = df.copy()
        for col in ["receita_total", "preco_medio"]:
            if col in show.columns:
                show[col] = show[col].map(fmt_brl)
        st.dataframe(show, use_container_width=True, hide_index=True)

    st.subheader("Cardápio cadastrado")
    try:
        menu = pd.DataFrame(itens_cardapio_list())
    except Exception as e:
        st.warning(f"Não foi possível carregar itens_cardapio: {e}")
        menu = pd.DataFrame()
    if menu.empty:
        st.caption("Nenhum registro em itens_cardapio.")
    else:
        st.dataframe(menu, use_container_width=True, hide_index=True)


def tab_clientes(trade: str):
    kc    = kpi_clientes(trade) or {}
    total = int(kc.get("total_clientes") or 0)
    tm    = _f(kc.get("ticket_medio"))
    fq    = _f(kc.get("freq_media"))
    rc    = _f(kc.get("recencia_media"))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total de clientes", f"{total}", None, None,
                 min(100.0, total / max(total, 1) * 10), "Distintos (documento)")
    with c2:
        kpi_card("Ticket médio", fmt_brl(tm), None, None,
                 75.0, "Base histórico tratado")
    with c3:
        kpi_card("Frequência média", f"{fq:.1f}", None, None,
                 min(100.0, fq * 10), "Visitas médias")
    with c4:
        kpi_card("Recência média", f"{rc:.0f} d", None, None,
                 min(100.0, 100.0 / max(rc, 1) * 10), "Dias (média)")

    df_f = pd.DataFrame(clientes_faixa_frequencia(trade))
    df_r = pd.DataFrame(clientes_rfm_points(trade, 400))
    df_t = pd.DataFrame(clientes_top50(trade))

    u1, u2 = st.columns((1, 1))
    with u1:
        if not df_f.empty:
            st.plotly_chart(fig_faixa_freq(df_f), use_container_width=True,
                            key="fig_faixa_freq")
        else:
            st.info("Sem dados de frequência")
    with u2:
        if not df_r.empty:
            st.plotly_chart(fig_scatter_rfm(df_r), use_container_width=True,
                            key="fig_scatter_rfm")
        else:
            st.info("Sem dados de RFM")

    st.subheader("Top 50 clientes")
    if df_t.empty:
        st.info("Sem clientes para esta unidade.")
    else:
        st.dataframe(df_t, use_container_width=True, hide_index=True)


def tab_metas(trade: str, unidade_id: int):
    hist = metas_historico(trade)
    df   = pd.DataFrame(hist)

    if df.empty:
        st.warning("Nenhuma meta cadastrada para esta unidade.")
        st.code(
            "INSERT INTO metas (unidade_id, mes, ano, meta_vendas, realizado_vendas, "
            "meta_clientes, realizado_clientes)\n"
            "VALUES (<id_unidade>, EXTRACT(MONTH FROM NOW())::int, "
            "EXTRACT(YEAR FROM NOW())::int, 100000, 0, 500, 0);",
            language="sql",
        )
        return

    latest = hist[0]
    prev   = hist[1] if len(hist) > 1 else None

    pv  = _f(latest.get("pct_vendas"))
    pc  = _f(latest.get("pct_clientes"))
    pv0 = _f((prev or {}).get("pct_vendas"))   if prev else 0.0
    pc0 = _f((prev or {}).get("pct_clientes")) if prev else 0.0

    d_pv = fmt_delta_pct(pv, pv0) if prev else ("—", "pos")
    d_pc = fmt_delta_pct(pc, pc0) if prev else ("—", "pos")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("% Meta vendas", f"{pv:.1f}%", d_pv[0], d_pv[1] == "pos",
                 min(100.0, pv), f"Mês {int(latest['mes']):02d}/{int(latest['ano'])}")
    with c2:
        kpi_card("% Meta clientes", f"{pc:.1f}%", d_pc[0], d_pc[1] == "pos",
                 min(100.0, pc), "Realizado vs meta")
    with c3:
        rv  = latest.get("realizado_vendas")
        rv0 = (prev or {}).get("realizado_vendas")
        dr, br = fmt_delta_pct(_f(rv), _f(rv0)) if prev else ("—", "pos")
        kpi_card("Realizado vendas", fmt_brl(rv), dr, br == "pos",
                 min(100.0, _f(rv) / max(_f(latest.get("meta_vendas")), 0.01) * 100),
                 "vs meta do mês")
    with c4:
        rc  = latest.get("realizado_clientes")
        rc0 = (prev or {}).get("realizado_clientes")
        dr2, br2 = fmt_delta_pct(float(_f(rc)), float(_f(rc0))) if prev else ("—", "pos")
        kpi_card("Realizado clientes", f"{int(_f(rc))}", dr2, br2 == "pos",
                 min(100.0, _f(rc) / max(_f(latest.get("meta_clientes")), 0.01) * 100),
                 "vs meta clientes")

    g1, g2 = st.columns((1.2, 1))
    with g1:
        if not df.empty:
            st.plotly_chart(fig_metas_agrupadas(df), use_container_width=True,
                            key="fig_metas_agrupadas")
        else:
            st.info("Sem dados de metas")
    with g2:
        st.plotly_chart(fig_gauge_metas(pv), use_container_width=True,
                        key="fig_gauge_metas")

    st.subheader("Histórico")
    st.dataframe(df, use_container_width=True, hide_index=True)


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

    # Etapa 2 — Seleção de loja
    if st.session_state.loja_atual is None:
        st.markdown(
            "<style>section[data-testid='stSidebar']{display:none!important}</style>",
            unsafe_allow_html=True,
        )
        role = (st.session_state.user.get("role") or "").strip().lower()
        if role == "admin":
            st.session_state.loja_atual = {"id": None, "trade_name": "__admin__"}
            st.rerun()
        else:
            lojas = st.session_state.user.get("lojas") or []
            if len(lojas) == 1:
                st.session_state.loja_atual = lojas[0]
                st.rerun()
            else:
                popup_selecao_loja()
            st.stop()

    # Etapa 3 — Dashboard
    if st.session_state.loja_atual["trade_name"] == "__admin__":
        pagina_admin()
    else:
        pagina_dashboard()


if __name__ == "__main__":
    main()
