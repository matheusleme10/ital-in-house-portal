"""Painel administrativo — Ital In House."""

from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from admin_queries import kpi_admin, ranking_lojas, serie_admin
from ia_ui import render_ia_tab
from mv_dashboard import render_plataformas, render_recorrencia, render_tickets_descontos
from user_management import render_gerenciar_usuarios
from theme import PLOTLY_THEME, inject_global_css


def _header_html(data_str: str) -> str:
    return f"""
<div style='display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:8px'>
  <div>
    <div style='color:#5A5A65;font-size:.62rem;font-weight:600;
                letter-spacing:.1em;text-transform:uppercase'>Visão geral da rede</div>
    <div style='color:#F5F5F7;font-size:1.45rem;font-weight:800;
                letter-spacing:-.02em;margin-top:2px'>📊 Painel Administrativo</div>
  </div>
  <div style='color:#C8102E;font-size:.72rem;font-weight:600'>{data_str}</div>
</div>"""


def _kpi_card(label: str, valor: str, delta: str = "", delta_pos: bool = True):
    cor_delta = "#22C55E" if delta_pos else "#EF4444"
    bg_delta  = "rgba(34,197,94,.12)" if delta_pos else "rgba(239,68,68,.12)"
    delta_html = (
        f"<div style='display:inline-block;background:{bg_delta};color:{cor_delta};"
        f"font-size:.62rem;font-weight:600;padding:2px 8px;border-radius:99px;margin-top:4px'>"
        f"{delta}</div>"
    ) if delta else ""

    st.markdown(f"""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:12px;
            padding:14px 18px;transition:border-color .2s'>
  <div style='color:#5A5A65;font-size:.6rem;font-weight:600;
              letter-spacing:.09em;text-transform:uppercase;margin-bottom:6px'>{label}</div>
  <div style='color:#F5F5F7;font-size:1.5rem;font-weight:800;
              letter-spacing:-.02em'>{valor}</div>
  {delta_html}
</div>""", unsafe_allow_html=True)


def render_admin_panel():
    inject_global_css()

    # Sem sidebar para admin
    st.markdown("""
<style>
section[data-testid='stSidebar']{display:none!important}
.main .block-container{padding-left:2rem!important;padding-right:2rem!important}
</style>""", unsafe_allow_html=True)

    dias_map = {"7 dias": 7, "30 dias": 30, "90 dias": 90}

    # ── Header ──
    st.markdown(_header_html(datetime.now().strftime("%d/%m/%Y %H:%M")),
                unsafe_allow_html=True)

    # ── Controles em linha ──
    cc1, cc2, cc3, cc4 = st.columns([1.2, 2, 1.4, 0.7])
    with cc1:
        periodo = st.selectbox("Período", list(dias_map.keys()), index=1,
                               key="adm_periodo", label_visibility="collapsed")
    with cc2:
        opts    = ["— Visão geral —"] + [l["trade_name"] for l in st.session_state.user["lojas"]]
        escolha = st.selectbox("Loja", opts, index=0,
                               key="adm_loja", label_visibility="collapsed")
        if escolha == "— Visão geral —":
            if st.session_state.loja_atual.get("trade_name") != "__admin__":
                st.session_state.loja_atual = {"id": None, "trade_name": "__admin__"}
                st.session_state.chat = []
                st.rerun()
        else:
            nova = next(l for l in st.session_state.user["lojas"]
                        if l["trade_name"] == escolha)
            if st.session_state.loja_atual != nova:
                st.session_state.loja_atual = nova
                st.session_state.chat = []
                st.rerun()
    with cc4:
        if st.button("🚪 Sair", key="adm_sair", use_container_width=True):
            for k in ["user", "loja_atual", "chat"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("<hr style='border-color:#2A2A2F;margin:10px 0 16px'>",
                unsafe_allow_html=True)

    dias = dias_map[periodo]

    # Verifica se está em visão geral ou loja específica
    loja_atual     = st.session_state.loja_atual
    trade_atual    = loja_atual.get("trade_name")
    is_visao_geral = (trade_atual == "__admin__" or not trade_atual)

    # ── Abas ──
    t_geral, t_rank, t_plat, t_tick, t_recorr, t_usuarios, t_ia = st.tabs([
      "📊  Visão Geral",
      "🏆  Ranking",
      "📡  Plataformas",
      "🎟️  Tickets & Descontos",
      "🔄  Recorrência",
      "👥  Usuários",        # ← nova
      "🤖  IA - IH",
    ])

    # ══════════ ABA 1 — VISÃO GERAL ══════════
    with t_geral:
        kv     = kpi_admin(dias)
        fat    = float(kv.get("faturamento_total") or 0)
        ped    = int(kv.get("total_pedidos") or 0)
        tick   = float(kv.get("ticket_medio") or 0)
        nlojas = int(kv.get("total_lojas") or 0)

        c1, c2, c3, c4 = st.columns(4)
        with c1: _kpi_card("💰 Faturamento total", f"R$ {fat:,.2f}")
        with c2: _kpi_card("🛒 Total de pedidos",  f"{ped:,}")
        with c3: _kpi_card("🎟️ Ticket médio",      f"R$ {tick:,.2f}")
        with c4: _kpi_card("🏪 Lojas com vendas",  str(nlojas))

        st.markdown("<br>", unsafe_allow_html=True)

        serie = serie_admin(dias)
        if serie:
            datas = [s.get("data") for s in serie]
            fats  = [float(s.get("faturamento") or 0) for s in serie]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=datas, y=fats,
                mode="lines", fill="tozeroy",
                line=dict(color="#C8102E", width=2.2),
                fillcolor="rgba(200,16,46,.07)",
                hovertemplate="R$ %{y:,.2f}<extra></extra>",
            ))
            # ── FIX: dois update_layout separados evita conflito de 'title' ──
            fig.update_layout(**PLOTLY_THEME, height=340)
            fig.update_layout(
                yaxis=dict(
                    gridcolor="#1C1C1F",
                    showline=False,
                    tickfont=dict(color="#8A8A95", size=11),
                    tickprefix="R$ ",
                    tickformat=",.0f",
                    zeroline=False,
                )
            )
            fig.update_layout(
                title=dict(
                    text=f"Faturamento diário — últimos {dias} dias",
                    font=dict(color="#C8C8D0", size=13),
                    x=0,
                )
            )
            st.plotly_chart(fig, use_container_width=True, key="adm_serie")
        else:
            st.info("Sem dados de série temporal no período.")

    # ══════════ ABA 2 — RANKING ══════════
    with t_rank:
        ranking = ranking_lojas(dias)
        st.markdown("""
<div style='color:#5A5A65;font-size:.6rem;font-weight:600;
            letter-spacing:.1em;text-transform:uppercase;margin-bottom:14px'>
  🏆 Ranking de lojas por faturamento
</div>""", unsafe_allow_html=True)

        if ranking:
            max_fat = max(float(r.get("faturamento") or 0) for r in ranking) or 1
            cores   = {1: "#F59E0B", 2: "#A0A0A8", 3: "#C8102E"}

            for i, row in enumerate(ranking[:20]):
                pos  = i + 1
                fat  = float(row.get("faturamento") or 0)
                pct  = fat / max_fat * 100
                nome = row.get("trade_name") or "—"
                cor  = cores.get(pos, "#3A3A4A")

                st.markdown(f"""
<div style='display:flex;align-items:center;gap:10px;
            padding:9px 0;border-bottom:1px solid #1C1C1F'>
  <div style='color:{cor};font-size:.72rem;font-weight:800;width:22px;
              flex-shrink:0'>#{pos}</div>
  <div style='flex:1;min-width:0'>
    <div style='color:#F5F5F7;font-size:.78rem;font-weight:700;
                white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{nome}</div>
    <div style='background:#1C1C1F;border-radius:99px;height:3px;margin-top:5px'>
      <div style='width:{pct:.0f}%;height:3px;border-radius:99px;
                  background:linear-gradient(90deg,#C8102E,#E8304A)'></div>
    </div>
  </div>
  <div style='text-align:right;flex-shrink:0'>
    <div style='color:#F5F5F7;font-size:.78rem;font-weight:700'>
      R$ {fat:,.0f}
    </div>
    <div style='color:#5A5A65;font-size:.62rem'>
      {int(row.get("pedidos") or 0)} pedidos
    </div>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.info("Sem dados de faturamento no período.")

    # ══════════ ABA 3 — PLATAFORMAS ══════════
    with t_plat:
        if is_visao_geral:
            st.markdown("""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:12px;
            padding:20px 24px;margin-top:8px'>
  <div style='font-size:.9rem;font-weight:700;color:#F5F5F7;margin-bottom:6px'>
    📡 Selecione uma loja
  </div>
  <div style='color:#5A5A65;font-size:.85rem;line-height:1.6'>
    Use o seletor <strong style='color:#A0A0A8'>🏪 Loja</strong> no topo da página
    para filtrar uma unidade específica e visualizar os dados de
    <strong style='color:#A0A0A8'>iFood, Anotaai, 99Food e Direto</strong> semana a semana.
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div style='color:#5A5A65;font-size:.62rem;font-weight:600;
            letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px'>
  Visualizando
</div>
<div style='color:#F5F5F7;font-size:1rem;font-weight:800;margin-bottom:16px'>
  📡 Plataformas — {trade_atual}
</div>""", unsafe_allow_html=True)
            render_plataformas(trade_atual)

    # ══════════ ABA 4 — TICKETS & DESCONTOS ══════════
    with t_tick:
        if is_visao_geral:
            st.markdown("""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:12px;
            padding:20px 24px;margin-top:8px'>
  <div style='font-size:.9rem;font-weight:700;color:#F5F5F7;margin-bottom:6px'>
    🎟️ Selecione uma loja
  </div>
  <div style='color:#5A5A65;font-size:.85rem;line-height:1.6'>
    Use o seletor <strong style='color:#A0A0A8'>🏪 Loja</strong> no topo da página
    para visualizar <strong style='color:#A0A0A8'>tickets médios e descontos</strong>
    por plataforma semana a semana.
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div style='color:#5A5A65;font-size:.62rem;font-weight:600;
            letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px'>
  Visualizando
</div>
<div style='color:#F5F5F7;font-size:1rem;font-weight:800;margin-bottom:16px'>
  🎟️ Tickets & Descontos — {trade_atual}
</div>""", unsafe_allow_html=True)
            render_tickets_descontos(trade_atual)

    # ══════════ ABA 5 — RECORRÊNCIA ══════════
    with t_recorr:
        if is_visao_geral:
            st.markdown("""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:12px;
            padding:20px 24px;margin-top:8px'>
  <div style='font-size:.9rem;font-weight:700;color:#F5F5F7;margin-bottom:6px'>
    🔄 Selecione uma loja
  </div>
  <div style='color:#5A5A65;font-size:.85rem;line-height:1.6'>
    Use o seletor <strong style='color:#A0A0A8'>🏪 Loja</strong> no topo da página
    para visualizar <strong style='color:#A0A0A8'>recorrência, almoço vs janta
    e clientes novos vs recorrentes</strong> semana a semana.
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div style='color:#5A5A65;font-size:.62rem;font-weight:600;
            letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px'>
  Visualizando
</div>
<div style='color:#F5F5F7;font-size:1rem;font-weight:800;margin-bottom:16px'>
  🔄 Recorrência — {trade_atual}
</div>""", unsafe_allow_html=True)
            render_recorrencia(trade_atual)

    # ══════════ ABA 6 — Usuarios ══════════
    with t_usuarios:
      render_gerenciar_usuarios()
    
    # ══════════ ABA 7 — IA ══════════
    with t_ia:
        render_ia_tab(st.session_state.user, st.session_state.loja_atual)
        