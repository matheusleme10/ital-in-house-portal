"""Painel administrativo — Ital In House.
Navegação via sidebar. Sem loja → dados consolidados. Com loja → dados da loja.
"""

from datetime import datetime
from decimal import Decimal

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from admin_queries import (
    clientes_faixa_rede, clientes_rfm_rede, clientes_top50_rede,
    kpi_admin, kpi_clientes_rede, kpi_vendas_rede, kpi_vendas_rede_extras,
    pedidos_rede, ranking_lojas, receita_categoria_rede,
    serie_admin, serie_rede, status_rede, top_itens_rede,
)
from charts import (
    fig_barras_pedidos, fig_faturamento_diario, fig_faixa_freq,
    fig_pizza_categoria, fig_pizza_status, fig_scatter_rfm,
    fig_top_itens_horizontal,
)
from ia_ui import render_ia_tab
from mv_dashboard import render_plataformas, render_recorrencia, render_tickets_descontos
from sidebar import render_sidebar
from tabs import fmt_brl, fmt_delta_pct, kpi_card, tab_cardapio, tab_clientes, tab_metas, tab_vendas
from theme import PLOTLY_THEME, inject_global_css
from user_management import render_gerenciar_usuarios

LOGO_URL = "https://d7jztl9hjt0p1.cloudfront.net/1.0.0.119/assets/images/home/logo.png"


def _f(x) -> float:
    if x is None: return 0.0
    if isinstance(x, Decimal): return float(x)
    return float(x)


def _kpi(label, valor, delta="", pos=True):
    cor = "#22C55E" if pos else "#EF4444"
    bg  = "rgba(34,197,94,.12)" if pos else "rgba(239,68,68,.12)"
    d   = (f"<div style='display:inline-block;background:{bg};color:{cor};"
           f"font-size:.62rem;font-weight:600;padding:2px 8px;"
           f"border-radius:99px;margin-top:4px'>{delta}</div>") if delta else ""
    st.markdown(f"""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:12px;padding:14px 18px'>
  <div style='color:#5A5A65;font-size:.6rem;font-weight:600;
              letter-spacing:.09em;text-transform:uppercase;margin-bottom:6px'>{label}</div>
  <div style='color:#F5F5F7;font-size:1.5rem;font-weight:800;letter-spacing:-.02em'>{valor}</div>
  {d}
</div>""", unsafe_allow_html=True)


def _page_header(titulo: str, sub: str = "", badge: str = ""):
    badge_html = ""
    if badge:
        badge_html = (f"<span style='background:rgba(200,16,46,.12);color:#C8102E;"
                      f"font-size:.6rem;font-weight:700;padding:3px 10px;"
                      f"border-radius:99px;margin-left:10px;vertical-align:middle'>"
                      f"{badge}</span>")
    data = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:flex-end;
            margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid #2A2A2F'>
  <div>
    {'<div style="color:#5A5A65;font-size:.62rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px">' + sub + '</div>' if sub else ''}
    <div style='color:#F5F5F7;font-size:1.35rem;font-weight:800;letter-spacing:-.02em'>
      {titulo}{badge_html}
    </div>
  </div>
  <div style='color:#5A5A65;font-size:.72rem'>{data}</div>
</div>
""", unsafe_allow_html=True)


def _aviso_sem_mv(icone, nome):
    st.info(f"{icone} Os dados de **{nome}** são semanais por unidade. "
            f"Selecione uma loja no menu lateral para visualizar.")


# ─────────────────────────────────────────────
#  ABAS CONSOLIDADAS DA REDE
# ─────────────────────────────────────────────

def _vendas_rede(dias):
    kv = kpi_vendas_rede(dias)
    kx = kpi_vendas_rede_extras(dias)

    ma, mp   = _f(kv.get("mes_atual")), _f(kv.get("mes_anterior"))
    hj, on   = _f(kv.get("hoje")), _f(kx.get("fat_ontem"))
    phj, pon = int(kv.get("pedidos_hoje") or 0), int(kx.get("pedidos_ontem") or 0)
    tk, tkm  = _f(kv.get("ticket_medio_geral")), _f(kx.get("ticket_mes_anterior"))

    d1, d1b = fmt_delta_pct(ma, mp)
    d2, d2b = fmt_delta_pct(float(phj), float(pon))
    d3, d3b = fmt_delta_pct(tk, tkm)
    d4, d4b = fmt_delta_pct(hj, on)

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Faturamento mês (rede)", fmt_brl(ma), d1, d1b=="pos", min(100.0, ma/max(mp,.01)*100) if mp else 0, "vs mês anterior")
    with c2: kpi_card("Pedidos hoje (rede)",    str(phj),      d2, d2b=="pos", min(100.0, phj/max(pon,1)*100) if pon or phj else 0, f"vs ontem: {pon}")
    with c3: kpi_card("Ticket médio (rede)",    fmt_brl(tk),   d3, d3b=="pos", min(100.0, tk/max(tkm,.01)*100) if tkm else 0, "vs mês anterior")
    with c4: kpi_card("Faturamento hoje (rede)",fmt_brl(hj),   d4, d4b=="pos", min(100.0, hj/max(on,.01)*100) if on else 0, f"vs ontem: {fmt_brl(on)}")

    df_s  = pd.DataFrame(serie_rede(dias))
    df_p  = pd.DataFrame(pedidos_rede(dias))
    df_st = pd.DataFrame(status_rede(dias))

    a1, a2 = st.columns((1.4, 1))
    with a1:
        st.plotly_chart(fig_faturamento_diario(df_s), use_container_width=True, key="fg_fat_r") if not df_s.empty else st.info("Sem dados")
    with a2:
        st.plotly_chart(fig_pizza_status(df_st), use_container_width=True, key="fg_st_r") if not df_st.empty else st.info("Sem dados")
    if not df_p.empty:
        st.plotly_chart(fig_barras_pedidos(df_p), use_container_width=True, key="fg_ped_r")


def _cardapio_rede(dias):
    rows = top_itens_rede(dias, 15)
    df   = pd.DataFrame(rows)
    top1 = rows[0] if rows else None

    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Top item (rede)", (top1 or {}).get("produto") or "—", None, None, 100.0 if top1 else 0.0, "Por receita")
    with c2:
        q = int((top1 or {}).get("qtd_vendida") or 0)
        kpi_card("Quantidade top 1", f"{q}", None, None, 100.0, "Unidades vendidas")
    with c3:
        rec = _f((top1 or {}).get("receita_total"))
        kpi_card("Receita top 1", fmt_brl(rec), None, None, 100.0 if rec else 0.0, "Receita no período")

    b1, b2 = st.columns((1.2, 1))
    with b1:
        if not df.empty: st.plotly_chart(fig_top_itens_horizontal(df, 10), use_container_width=True, key="fg_top_r")
        else: st.info("Sem dados")
    with b2:
        df_cat = pd.DataFrame(receita_categoria_rede(dias))
        if not df_cat.empty: st.plotly_chart(fig_pizza_categoria(df_cat), use_container_width=True, key="fg_cat_r")
        else: st.info("Sem dados")

    if not df.empty:
        show = df.copy()
        for col in ["receita_total", "preco_medio"]:
            if col in show.columns: show[col] = show[col].map(fmt_brl)
        st.dataframe(show, use_container_width=True, hide_index=True)


def _clientes_rede():
    kc    = kpi_clientes_rede()
    total = int(kc.get("total_clientes") or 0)
    tm    = _f(kc.get("ticket_medio"))
    fq    = _f(kc.get("freq_media"))
    rc    = _f(kc.get("recencia_media"))

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Total clientes (rede)", f"{total:,}", None, None, min(100.0, total/max(total,1)*10), "Distintos")
    with c2: kpi_card("Ticket médio (rede)",   fmt_brl(tm), None, None, 75.0, "Histórico")
    with c3: kpi_card("Frequência média",       f"{fq:.1f}", None, None, min(100.0, fq*10), "Visitas médias")
    with c4: kpi_card("Recência média",         f"{rc:.0f} d", None, None, min(100.0, 100.0/max(rc,1)*10), "Dias")

    df_f = pd.DataFrame(clientes_faixa_rede())
    df_r = pd.DataFrame(clientes_rfm_rede(400))
    df_t = pd.DataFrame(clientes_top50_rede())

    u1, u2 = st.columns((1, 1))
    with u1:
        if not df_f.empty: st.plotly_chart(fig_faixa_freq(df_f), use_container_width=True, key="fg_fq_r")
        else: st.info("Sem dados")
    with u2:
        if not df_r.empty: st.plotly_chart(fig_scatter_rfm(df_r), use_container_width=True, key="fg_rfm_r")
        else: st.info("Sem dados")

    st.subheader("Top 50 clientes da rede")
    if not df_t.empty: st.dataframe(df_t, use_container_width=True, hide_index=True)
    else: st.info("Sem dados de clientes.")


# ─────────────────────────────────────────────
#  RENDER PRINCIPAL
# ─────────────────────────────────────────────

def render_admin_panel():
    inject_global_css()

    # Sidebar fixa — sem o collapse nativo
    st.markdown("""
<style>
[data-testid="collapsedControl"]{display:none!important}
.main .block-container{padding-top:1rem!important}
</style>""", unsafe_allow_html=True)

    ctx       = render_sidebar("admin")
    page      = ctx["page"]
    days      = ctx["days"]
    trade     = ctx["trade"]
    loja_obj  = ctx["loja_obj"] or {}
    loja_id   = loja_obj.get("id")
    is_geral  = not trade or trade == "__admin__"
    badge     = f"Rede toda" if is_geral else trade

    # ── Títulos por página ──
    TITLES = {
        "visao_geral":  ("📊 Visão Geral",          "Painel Administrativo"),
        "ranking":      ("🏆 Ranking de Lojas",      "Painel Administrativo"),
        "vendas":       ("📈 Vendas",                "Rede toda" if is_geral else trade),
        "cardapio":     ("🍽️ Cardápio & Itens",     "Rede toda" if is_geral else trade),
        "clientes":     ("👥 Clientes",              "Rede toda" if is_geral else trade),
        "metas":        ("🎯 Metas",                 trade if not is_geral else ""),
        "plataformas":  ("📡 Plataformas",           trade if not is_geral else ""),
        "tickets":      ("🎟️ Tickets & Descontos",  trade if not is_geral else ""),
        "recorrencia":  ("🔄 Recorrência",           trade if not is_geral else ""),
        "usuarios":     ("👤 Gerenciar Usuários",    "Administração"),
        "ia":           ("🤖 IA - IH",               "Rede toda" if is_geral else trade),
    }

    titulo, sub = TITLES.get(page, ("Dashboard", ""))
    _page_header(titulo, sub, badge if page not in ("visao_geral","ranking","usuarios") else "")

    # ── Roteamento ──

    # VISÃO GERAL
    if page == "visao_geral":
        kv     = kpi_admin(days)
        fat    = float(kv.get("faturamento_total") or 0)
        ped    = int(kv.get("total_pedidos") or 0)
        tick   = float(kv.get("ticket_medio") or 0)
        nlojas = int(kv.get("total_lojas") or 0)

        c1, c2, c3, c4 = st.columns(4)
        with c1: _kpi("💰 Faturamento total", f"R$ {fat:,.2f}")
        with c2: _kpi("🛒 Total de pedidos",  f"{ped:,}")
        with c3: _kpi("🎟️ Ticket médio",      f"R$ {tick:,.2f}")
        with c4: _kpi("🏪 Lojas com vendas",  str(nlojas))

        st.markdown("<br>", unsafe_allow_html=True)
        serie = serie_admin(days)
        if serie:
            datas = [s.get("data") for s in serie]
            fats  = [float(s.get("faturamento") or 0) for s in serie]
            fig   = go.Figure()
            fig.add_trace(go.Scatter(
                x=datas, y=fats, mode="lines", fill="tozeroy",
                line=dict(color="#C8102E", width=2.2),
                fillcolor="rgba(200,16,46,.07)",
                hovertemplate="R$ %{y:,.2f}<extra></extra>",
            ))
            fig.update_layout(**PLOTLY_THEME, height=360)
            fig.update_layout(yaxis=dict(
                gridcolor="#1C1C1F", showline=False,
                tickfont=dict(color="#8A8A95", size=11),
                tickprefix="R$ ", tickformat=",.0f", zeroline=False,
            ))
            fig.update_layout(title=dict(
                text=f"Faturamento diário — últimos {days} dias",
                font=dict(color="#C8C8D0", size=13), x=0,
            ))
            st.plotly_chart(fig, use_container_width=True, key="adm_serie_vg")
        else:
            st.info("Sem dados de série temporal no período.")

    # RANKING
    elif page == "ranking":
        ranking = ranking_lojas(days)
        if ranking:
            max_fat = max(float(r.get("faturamento") or 0) for r in ranking) or 1
            cores   = {1: "#F59E0B", 2: "#A0A0A8", 3: "#C8102E"}
            for i, row in enumerate(ranking[:20]):
                pos      = i + 1
                fat      = float(row.get("faturamento") or 0)
                pct      = fat / max_fat * 100
                lj       = row.get("trade_name") or "—"
                cor      = cores.get(pos, "#3A3A4A")
                st.markdown(f"""
<div style='display:flex;align-items:center;gap:12px;
            padding:10px 0;border-bottom:1px solid #1C1C1F'>
  <div style='color:{cor};font-size:.78rem;font-weight:800;width:28px;
              flex-shrink:0;text-align:center'>#{pos}</div>
  <div style='flex:1;min-width:0'>
    <div style='color:#F5F5F7;font-size:.85rem;font-weight:700;
                white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{lj}</div>
    <div style='background:#1C1C1F;border-radius:99px;height:4px;margin-top:6px'>
      <div style='width:{pct:.0f}%;height:4px;border-radius:99px;
                  background:linear-gradient(90deg,#C8102E,#E8304A)'></div>
    </div>
  </div>
  <div style='text-align:right;flex-shrink:0'>
    <div style='color:#F5F5F7;font-size:.85rem;font-weight:700'>R$ {fat:,.0f}</div>
    <div style='color:#5A5A65;font-size:.68rem'>{int(row.get("pedidos") or 0)} pedidos</div>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.info("Sem dados de faturamento no período.")

    # VENDAS
    elif page == "vendas":
        if is_geral:
            _vendas_rede(days)
        else:
            tab_vendas(trade, loja_id or 0, days)

    # CARDÁPIO
    elif page == "cardapio":
        if is_geral:
            _cardapio_rede(days)
        else:
            tab_cardapio(trade, days)

    # CLIENTES
    elif page == "clientes":
        if is_geral:
            _clientes_rede()
        else:
            tab_clientes(trade)

    # METAS
    elif page == "metas":
        if is_geral:
            st.info("🎯 Metas são configuradas por loja. Selecione uma loja no menu lateral.")
        else:
            tab_metas(trade, loja_id or 0)

    # PLATAFORMAS
    elif page == "plataformas":
        if is_geral:
            _aviso_sem_mv("📡", "Plataformas")
        else:
            render_plataformas(trade)

    # TICKETS
    elif page == "tickets":
        if is_geral:
            _aviso_sem_mv("🎟️", "Tickets & Descontos")
        else:
            render_tickets_descontos(trade)

    # RECORRÊNCIA
    elif page == "recorrencia":
        if is_geral:
            _aviso_sem_mv("🔄", "Recorrência")
        else:
            render_recorrencia(trade)

    # USUÁRIOS
    elif page == "usuarios":
        render_gerenciar_usuarios()

    # IA
    elif page == "ia":
        render_ia_tab(st.session_state.user, st.session_state.loja_atual)
