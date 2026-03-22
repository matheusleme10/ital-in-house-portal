"""Tabs compartilhadas — usadas pelo dashboard franqueado e pelo painel admin."""

from decimal import Decimal

import pandas as pd
import streamlit as st

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
from queries import (
    clientes_faixa_frequencia,
    clientes_rfm_points,
    clientes_top50,
    itens_cardapio_list,
    kpi_clientes,
    kpi_vendas,
    kpi_vendas_extras,
    meta_mes_atual,
    metas_historico,
    pedidos_por_dia,
    receita_por_categoria,
    serie_temporal,
    status_vendas,
    top_itens,
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


# ─────────────────────────────────────────────
#  TABS
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
                            key=f"fig_fat_{trade}")
        else:
            st.info("Sem dados de série temporal")
    with a2:
        if not df_st.empty:
            st.plotly_chart(fig_pizza_status(df_st), use_container_width=True,
                            key=f"fig_pizza_{trade}")
        else:
            st.info("Sem dados de status")

    if not df_p.empty:
        st.plotly_chart(fig_barras_pedidos(df_p), use_container_width=True,
                        key=f"fig_ped_{trade}")
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
                            key=f"fig_top_{trade}")
        else:
            st.info("Sem dados de itens")
    with b2:
        df_cat = pd.DataFrame(receita_por_categoria(trade, days))
        if not df_cat.empty:
            st.plotly_chart(fig_pizza_categoria(df_cat), use_container_width=True,
                            key=f"fig_cat_{trade}")
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
        kpi_card("Ticket médio", fmt_brl(tm), None, None, 75.0, "Base histórico tratado")
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
                            key=f"fig_freq_{trade}")
        else:
            st.info("Sem dados de frequência")
    with u2:
        if not df_r.empty:
            st.plotly_chart(fig_scatter_rfm(df_r), use_container_width=True,
                            key=f"fig_rfm_{trade}")
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
                            key=f"fig_metas_{trade}")
        else:
            st.info("Sem dados de metas")
    with g2:
        st.plotly_chart(fig_gauge_metas(pv), use_container_width=True,
                        key=f"fig_gauge_{trade}")

    st.subheader("Histórico")
    st.dataframe(df, use_container_width=True, hide_index=True)
