"""
Tabs compartilhadas — Admin + Franqueado
Lógica retroativa: usa ontem (ou último dia com dados) em vez de hoje.
Cache TTL=600s em todas as queries pesadas para troca instantânea de páginas.
"""

from decimal import Decimal

import pandas as pd
import streamlit as st

from charts import (
    fig_barras_pedidos, fig_faturamento_diario, fig_faixa_freq,
    fig_gauge_metas, fig_metas_agrupadas, fig_pizza_categoria,
    fig_pizza_status, fig_scatter_rfm, fig_top_itens_horizontal,
)
from queries import (
    clientes_faixa_frequencia, clientes_rfm_points, clientes_top50,
    itens_cardapio_list, kpi_clientes, kpi_vendas, kpi_vendas_extras,
    meta_mes_atual, metas_historico, pedidos_por_dia,
    receita_por_categoria, serie_temporal, status_vendas, top_itens,
)


# ─────────────────────────────────────────────
#  CACHE — TTL 600s (10 min) em tudo
# ─────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def _kpi_vendas_c(trade):        return kpi_vendas(trade)

@st.cache_data(ttl=600, show_spinner=False)
def _kpi_vendas_extras_c(trade): return kpi_vendas_extras(trade)

@st.cache_data(ttl=600, show_spinner=False)
def _serie_c(trade, days):       return serie_temporal(trade, days)

@st.cache_data(ttl=600, show_spinner=False)
def _pedidos_c(trade, days):     return pedidos_por_dia(trade, days)

@st.cache_data(ttl=600, show_spinner=False)
def _status_c(trade, days):      return status_vendas(trade, days)

@st.cache_data(ttl=600, show_spinner=False)
def _top_itens_c(trade, days, limit): return top_itens(trade, days, limit)

@st.cache_data(ttl=600, show_spinner=False)
def _cat_c(trade, days):         return receita_por_categoria(trade, days)

@st.cache_data(ttl=600, show_spinner=False)
def _kpi_cli_c(trade):           return kpi_clientes(trade)

@st.cache_data(ttl=600, show_spinner=False)
def _faixa_c(trade):             return clientes_faixa_frequencia(trade)

@st.cache_data(ttl=600, show_spinner=False)
def _rfm_c(trade, limit):        return clientes_rfm_points(trade, limit)

@st.cache_data(ttl=600, show_spinner=False)
def _top50_c(trade):             return clientes_top50(trade)

@st.cache_data(ttl=600, show_spinner=False)
def _cardapio_c():               return itens_cardapio_list()

@st.cache_data(ttl=600, show_spinner=False)
def _meta_c(uid):                return meta_mes_atual(uid)

@st.cache_data(ttl=600, show_spinner=False)
def _metas_hist_c(trade):        return metas_historico(trade)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _f(x) -> float:
    if x is None: return 0.0
    if isinstance(x, Decimal): return float(x)
    return float(x)


def fmt_brl(x) -> str:
    s = f"{_f(x):,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_delta_pct(cur: float, prev: float) -> tuple[str, str]:
    if prev == 0:
        return ("↑ 100%", "pos") if cur > 0 else ("—", "pos")
    d = (cur - prev) / prev * 100
    return (f"{abs(d):.1f}%", "pos") if d >= 0 else (f"{abs(d):.1f}%", "neg")


# ─────────────────────────────────────────────
#  KPI CARD — STRIPE STYLE
# ─────────────────────────────────────────────

def kpi_card(
    title: str,
    value: str,
    delta_text: str | None,
    delta_pos: bool | None,
    progress_pct: float,
    bar_label: str,
    icon: str = "",
) -> None:
    p = max(0.0, min(float(progress_pct or 0), 100.0))

    delta_html = ""
    if delta_text and delta_pos is not None:
        cor   = "#22C55E" if delta_pos else "#EF4444"
        bg    = "rgba(34,197,94,.1)" if delta_pos else "rgba(239,68,68,.1)"
        arrow = "↑" if delta_pos else "↓"
        delta_html = (
            f"<div style='display:inline-flex;align-items:center;gap:4px;"
            f"background:{bg};color:{cor};font-size:.66rem;font-weight:700;"
            f"padding:3px 10px;border-radius:99px;margin-top:6px'>"
            f"{arrow} {delta_text}"
            f"</div>"
        )

    icon_html = f"<span style='font-size:1rem;margin-right:5px'>{icon}</span>" if icon else ""
    bar_color = "#22C55E" if delta_pos else "#C8102E" if delta_pos is False else "#C8102E"

    st.markdown(f"""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:14px;
            padding:18px 20px;position:relative;overflow:hidden'>
  <div style='position:absolute;top:0;left:0;right:0;height:3px;
              background:{bar_color};opacity:.55;border-radius:14px 14px 0 0'></div>
  <div style='color:#5A5A65;font-size:.6rem;font-weight:600;
              letter-spacing:.09em;text-transform:uppercase;margin-bottom:8px'>
    {icon_html}{title}
  </div>
  <div style='color:#F5F5F7;font-size:1.6rem;font-weight:800;
              letter-spacing:-.03em;line-height:1'>{value}</div>
  {delta_html}
  <div style='margin-top:12px'>
    <div style='display:flex;justify-content:space-between;
                color:#5A5A65;font-size:.58rem;margin-bottom:4px'>
      <span>{bar_label}</span><span>{p:.0f}%</span>
    </div>
    <div style='background:#1C1C1F;border-radius:99px;height:3px'>
      <div style='width:{p}%;height:3px;border-radius:99px;
                  background:{bar_color};transition:width .5s ease'></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  TAB VENDAS — retroativo (ontem, não hoje)
# ─────────────────────────────────────────────

def tab_vendas(trade: str, unidade_id: int, days: int):
    kv   = _kpi_vendas_c(trade) or {}
    kx   = _kpi_vendas_extras_c(trade) or {}
    meta = _meta_c(unidade_id) or {}

    mes_atual = _f(kv.get("mes_atual"))
    mes_ant   = _f(kv.get("mes_anterior"))
    ticket    = _f(kv.get("ticket_medio_geral"))
    ticket_ma = _f(kx.get("ticket_mes_anterior"))

    # Retroativo: usa ontem (ou último dia com dados) em vez de hoje
    fat_ref  = _f(kx.get("fat_ontem"))   # último dia com dados
    ped_ref  = int(kx.get("pedidos_ontem") or 0)
    fat_ant  = _f(kx.get("fat_ant") or 0)
    ped_ant  = int(kx.get("ped_ant") or 0)
    ref_lbl  = kx.get("ref_label") or "ontem"

    d1, d1b = fmt_delta_pct(mes_atual, mes_ant)
    d2, d2b = fmt_delta_pct(float(ped_ref), float(ped_ant))
    d3, d3b = fmt_delta_pct(ticket, ticket_ma)
    d4, d4b = fmt_delta_pct(fat_ref, fat_ant)

    prog1 = 0.0
    if meta and _f(meta.get("meta_vendas")) > 0:
        prog1 = min(100.0, _f(meta.get("realizado_vendas")) / _f(meta.get("meta_vendas")) * 100)
    elif mes_ant > 0:
        prog1 = min(100.0, mes_atual / mes_ant * 100)

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Faturamento mês",      fmt_brl(mes_atual), d1, d1b=="pos",
                      prog1, "vs mês anterior", "💰")
    with c2: kpi_card(f"Pedidos ({ref_lbl})",  str(ped_ref),       d2, d2b=="pos",
                      min(100, ped_ref/max(ped_ant,1)*100) if ped_ant else 0,
                      f"vs anterior: {ped_ant}", "🛒")
    with c3: kpi_card("Ticket médio",           fmt_brl(ticket),    d3, d3b=="pos",
                      min(100, ticket/max(ticket_ma,.01)*100) if ticket_ma else 0,
                      "vs mês anterior", "🎟️")
    with c4: kpi_card(f"Fat. ({ref_lbl})",      fmt_brl(fat_ref),   d4, d4b=="pos",
                      min(100, fat_ref/max(fat_ant,.01)*100) if fat_ant else 0,
                      f"vs anterior: {fmt_brl(fat_ant)}", "📅")

    df_s  = pd.DataFrame(_serie_c(trade, days))
    df_p  = pd.DataFrame(_pedidos_c(trade, days))
    df_st = pd.DataFrame(_status_c(trade, days))

    a1, a2 = st.columns((1.4, 1))
    with a1:
        if not df_s.empty: st.plotly_chart(fig_faturamento_diario(df_s), use_container_width=True, key=f"fig_fat_{trade}")
        else: st.info("Sem dados de série temporal")
    with a2:
        if not df_st.empty: st.plotly_chart(fig_pizza_status(df_st), use_container_width=True, key=f"fig_st_{trade}")
        else: st.info("Sem dados de status")
    if not df_p.empty:
        st.plotly_chart(fig_barras_pedidos(df_p), use_container_width=True, key=f"fig_ped_{trade}")


# ─────────────────────────────────────────────
#  TAB CARDÁPIO
# ─────────────────────────────────────────────

def tab_cardapio(trade: str, days: int):
    rows = _top_itens_c(trade, days, 15)
    df   = pd.DataFrame(rows)
    top1 = rows[0] if rows else None

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Item mais vendido",
                 (top1 or {}).get("produto") or "—",
                 None, None, 100.0 if top1 else 0.0, "Por receita no período", "🥇")
    with c2:
        q = int((top1 or {}).get("qtd_vendida") or 0)
        kpi_card("Quantidade (top 1)", f"{q:,}", None, None, 100.0, "Unidades vendidas", "📦")
    with c3:
        rec = _f((top1 or {}).get("receita_total"))
        kpi_card("Receita (top 1)", fmt_brl(rec), None, None,
                 100.0 if rec else 0.0, "Receita no período", "💵")

    b1, b2 = st.columns((1.2, 1))
    with b1:
        if not df.empty: st.plotly_chart(fig_top_itens_horizontal(df, 10), use_container_width=True, key=f"fig_top_{trade}")
        else: st.info("Sem dados de itens")
    with b2:
        df_cat = pd.DataFrame(_cat_c(trade, days))
        if not df_cat.empty: st.plotly_chart(fig_pizza_categoria(df_cat), use_container_width=True, key=f"fig_cat_{trade}")
        else: st.info("Sem dados de categoria")

    st.subheader("Detalhe — top itens")
    if df.empty:
        st.info("Sem dados de itens no período.")
    else:
        show = df.copy()
        for col in ["receita_total", "preco_medio"]:
            if col in show.columns:
                show[col] = show[col].map(fmt_brl)
        st.dataframe(show, use_container_width=True, hide_index=True)

    # ── INSIGHT PROATIVO: Mix Massas vs Acompanhamentos ──
    try:
        df_full = pd.DataFrame(_top_itens_c(trade, days, 50))
        if not df_full.empty and "categoria" in df_full.columns:
            df_full["tipo"] = df_full["categoria"].apply(
                lambda c: "🍝 Massas" if any(
                    k in str(c).lower() for k in ["massa", "macarr", "penne", "espaguete", "fettuc", "talh"]
                ) else "🥗 Acompanhamentos"
            )
            mix = df_full.groupby("tipo")["receita_total"].sum().reset_index()
            if len(mix) > 1:
                total_mix = mix["receita_total"].sum()
                mix["pct"] = mix["receita_total"] / total_mix * 100
                st.markdown("---")
                st.markdown("**🍽️ Mix de Vendas — Massas vs Acompanhamentos**")
                m1, m2 = st.columns(2)
                for _, row in mix.iterrows():
                    col = m1 if "Massa" in row["tipo"] else m2
                    with col:
                        kpi_card(row["tipo"], fmt_brl(row["receita_total"]),
                                 f"{row['pct']:.1f}% do mix", row["pct"] >= 50,
                                 row["pct"], "% da receita do período")
    except Exception:
        pass


# ─────────────────────────────────────────────
#  TAB CLIENTES
# ─────────────────────────────────────────────

def tab_clientes(trade: str):
    kc    = _kpi_cli_c(trade) or {}
    total = int(kc.get("total_clientes") or 0)
    tm    = _f(kc.get("ticket_medio"))
    fq    = _f(kc.get("freq_media"))
    rc    = _f(kc.get("recencia_media"))

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Total de clientes", f"{total:,}", None, None,
                      min(100.0, total/max(total,1)*10), "Distintos (documento)", "👥")
    with c2: kpi_card("Ticket médio",      fmt_brl(tm), None, None,
                      75.0, "Histórico tratado", "💳")
    with c3: kpi_card("Frequência média",  f"{fq:.1f}×", None, None,
                      min(100.0, fq*10), "Visitas médias", "🔄")
    with c4: kpi_card("Recência média",    f"{rc:.0f} dias", None, None,
                      min(100.0, max(0, 100.0 - rc)), "Dias desde última compra", "📆")

    df_f = pd.DataFrame(_faixa_c(trade))
    df_r = pd.DataFrame(_rfm_c(trade, 400))
    df_t = pd.DataFrame(_top50_c(trade))

    u1, u2 = st.columns(2)
    with u1:
        if not df_f.empty: st.plotly_chart(fig_faixa_freq(df_f), use_container_width=True, key=f"fig_fq_{trade}")
        else: st.info("Sem dados de frequência")
    with u2:
        if not df_r.empty: st.plotly_chart(fig_scatter_rfm(df_r), use_container_width=True, key=f"fig_rfm_{trade}")
        else: st.info("Sem dados de RFM")

    st.subheader("Top 50 clientes")
    if df_t.empty:
        st.info("Sem clientes para esta unidade.")
    else:
        st.dataframe(df_t, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
#  TAB METAS
# ─────────────────────────────────────────────

def tab_metas(trade: str, unidade_id: int):
    hist = _metas_hist_c(trade)
    df   = pd.DataFrame(hist)

    if df.empty:
        st.warning("Nenhuma meta cadastrada para esta unidade.")
        st.code(
            "INSERT INTO metas (unidade_id, mes, ano, meta_vendas, realizado_vendas,\n"
            "                   meta_clientes, realizado_clientes)\n"
            "VALUES (<id>, EXTRACT(MONTH FROM NOW())::int,\n"
            "        EXTRACT(YEAR FROM NOW())::int, 100000, 0, 500, 0);",
            language="sql",
        )
        return

    latest = hist[0]
    prev   = hist[1] if len(hist) > 1 else None

    pv  = _f(latest.get("pct_vendas"))
    pc  = _f(latest.get("pct_clientes"))
    pv0 = _f((prev or {}).get("pct_vendas"))
    pc0 = _f((prev or {}).get("pct_clientes"))

    d_pv = fmt_delta_pct(pv, pv0) if prev else ("—", "pos")
    d_pc = fmt_delta_pct(pc, pc0) if prev else ("—", "pos")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("% Meta vendas",    f"{pv:.1f}%", d_pv[0], d_pv[1]=="pos",
                      min(100.0, pv), f"Mês {int(latest.get('mes',0)):02d}/{int(latest.get('ano',0))}", "🎯")
    with c2: kpi_card("% Meta clientes",  f"{pc:.1f}%", d_pc[0], d_pc[1]=="pos",
                      min(100.0, pc), "Realizado vs meta", "👥")
    with c3:
        rv  = _f(latest.get("realizado_vendas"))
        rv0 = _f((prev or {}).get("realizado_vendas"))
        dr, br = fmt_delta_pct(rv, rv0) if prev else ("—", "pos")
        kpi_card("Realizado vendas", fmt_brl(rv), dr, br=="pos",
                 min(100.0, rv/max(_f(latest.get("meta_vendas")), 0.01)*100),
                 "vs meta do mês", "💰")
    with c4:
        rc  = _f(latest.get("realizado_clientes"))
        rc0 = _f((prev or {}).get("realizado_clientes"))
        dr2, br2 = fmt_delta_pct(rc, rc0) if prev else ("—", "pos")
        kpi_card("Realizado clientes", f"{int(rc):,}", dr2, br2=="pos",
                 min(100.0, rc/max(_f(latest.get("meta_clientes")), 0.01)*100),
                 "vs meta clientes", "🛍️")

    g1, g2 = st.columns((1.2, 1))
    with g1:
        if not df.empty: st.plotly_chart(fig_metas_agrupadas(df), use_container_width=True, key=f"fig_metas_{trade}")
        else: st.info("Sem dados")
    with g2:
        st.plotly_chart(fig_gauge_metas(pv), use_container_width=True, key=f"fig_gauge_{trade}")

    st.subheader("Histórico")
    st.dataframe(df, use_container_width=True, hide_index=True)
