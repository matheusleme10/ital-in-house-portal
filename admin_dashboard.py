"""
Painel Administrativo — Ital In House
Regra: Admin NUNCA vê tela de bloqueio.
- Sem loja selecionada → dados consolidados da rede em TODAS as abas
- Com loja selecionada → dados específicos da loja
- Plataformas/Tickets/Recorrência: sem loja = dados consolidados do backup.vendas
"""

from datetime import datetime
from decimal import Decimal

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from admin_queries import (
    kpi_admin, ranking_lojas, serie_admin,
    kpi_vendas_rede, kpi_vendas_rede_extras,
    serie_rede, pedidos_rede, status_rede,
    top_itens_rede, receita_categoria_rede,
    kpi_clientes_rede, clientes_faixa_rede,
    clientes_rfm_rede, clientes_top50_rede,
)
from charts import (
    fig_barras_pedidos, fig_faturamento_diario, fig_faixa_freq,
    fig_pizza_categoria, fig_pizza_status, fig_scatter_rfm,
    fig_top_itens_horizontal,
)
from ia_ui import render_ia_tab
from mv_dashboard import render_plataformas, render_recorrencia, render_tickets_descontos
from tabs import fmt_brl, fmt_delta_pct, kpi_card, tab_cardapio, tab_clientes, tab_metas, tab_vendas
from theme import PLOTLY_THEME, inject_global_css
from user_management import render_gerenciar_usuarios

LOGO_URL = "https://d7jztl9hjt0p1.cloudfront.net/1.0.0.119/assets/images/home/logo.png"


def _f(x) -> float:
    if x is None: return 0.0
    if isinstance(x, Decimal): return float(x)
    return float(x)


# ─────────────────────────────────────────────
#  KPI CARD ADMIN
# ─────────────────────────────────────────────

def _kpi(label: str, valor: str, delta: str = "", pos: bool = True):
    cor = "#22C55E" if pos else "#EF4444"
    bg  = "rgba(34,197,94,.1)" if pos else "rgba(239,68,68,.1)"
    d   = (f"<span style='background:{bg};color:{cor};font-size:.62rem;"
           f"font-weight:700;padding:2px 8px;border-radius:99px;margin-left:8px'>"
           f"{delta}</span>") if delta else ""
    st.markdown(f"""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:14px;
            padding:16px 20px;position:relative;overflow:hidden'>
  <div style='position:absolute;top:0;left:0;right:0;height:2px;
              background:#C8102E;opacity:.5'></div>
  <div style='color:#5A5A65;font-size:.6rem;font-weight:600;
              letter-spacing:.09em;text-transform:uppercase;margin-bottom:6px'>{label}</div>
  <div style='color:#F5F5F7;font-size:1.5rem;font-weight:800;letter-spacing:-.02em'>
    {valor}{d}
  </div>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  ABAS CONSOLIDADAS (sem loja selecionada)
# ─────────────────────────────────────────────

def _vendas_consolidada(dias: int):
    """Vendas da rede toda quando admin não selecionou loja."""
    kv = kpi_vendas_rede(dias) or {}
    kx = kpi_vendas_rede_extras(dias) or {}

    ma, mp   = _f(kv.get("mes_atual")), _f(kv.get("mes_anterior"))
    hj, on   = _f(kv.get("hoje")), _f(kx.get("fat_ontem"))
    phj, pon = int(kv.get("pedidos_hoje") or 0), int(kx.get("pedidos_ontem") or 0)
    tk, tkm  = _f(kv.get("ticket_medio_geral")), _f(kx.get("ticket_mes_anterior"))

    d1, d1b = fmt_delta_pct(ma, mp)
    d2, d2b = fmt_delta_pct(float(phj), float(pon))
    d3, d3b = fmt_delta_pct(tk, tkm)
    d4, d4b = fmt_delta_pct(hj, on)

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Fat. mês (rede)",    fmt_brl(ma),  d1, d1b=="pos", min(100, ma/max(mp,.01)*100) if mp else 0, "vs mês anterior", "💰")
    with c2: kpi_card("Pedidos hoje (rede)",str(phj),     d2, d2b=="pos", min(100, phj/max(pon,1)*100) if pon or phj else 0, f"vs ontem: {pon}", "🛒")
    with c3: kpi_card("Ticket médio (rede)",fmt_brl(tk),  d3, d3b=="pos", min(100, tk/max(tkm,.01)*100) if tkm else 0, "vs mês anterior", "🎟️")
    with c4: kpi_card("Fat. hoje (rede)",   fmt_brl(hj),  d4, d4b=="pos", min(100, hj/max(on,.01)*100) if on else 0, f"vs ontem: {fmt_brl(on)}", "📅")

    df_s  = pd.DataFrame(serie_rede(dias))
    df_p  = pd.DataFrame(pedidos_rede(dias))
    df_st = pd.DataFrame(status_rede(dias))

    a1, a2 = st.columns((1.4, 1))
    with a1:
        if not df_s.empty: st.plotly_chart(fig_faturamento_diario(df_s), use_container_width=True, key="fig_fat_rede_adm")
        else: st.info("Sem dados de série temporal")
    with a2:
        if not df_st.empty: st.plotly_chart(fig_pizza_status(df_st), use_container_width=True, key="fig_status_rede_adm")
        else: st.info("Sem dados de status")
    if not df_p.empty:
        st.plotly_chart(fig_barras_pedidos(df_p), use_container_width=True, key="fig_ped_rede_adm")


def _cardapio_consolidado(dias: int):
    rows = top_itens_rede(dias, 15)
    df   = pd.DataFrame(rows)
    top1 = rows[0] if rows else None

    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Top item (rede)", (top1 or {}).get("produto") or "—", None, None, 100.0 if top1 else 0.0, "Por receita", "🥇")
    with c2:
        q = int((top1 or {}).get("qtd_vendida") or 0)
        kpi_card("Qtd. vendida (top 1)", f"{q:,}", None, None, 100.0, "Unidades", "📦")
    with c3:
        rec = _f((top1 or {}).get("receita_total"))
        kpi_card("Receita (top 1)", fmt_brl(rec), None, None, 100.0 if rec else 0.0, "No período", "💵")

    b1, b2 = st.columns((1.2, 1))
    with b1:
        if not df.empty: st.plotly_chart(fig_top_itens_horizontal(df, 10), use_container_width=True, key="fig_top_rede_adm")
        else: st.info("Sem dados")
    with b2:
        df_cat = pd.DataFrame(receita_categoria_rede(dias))
        if not df_cat.empty: st.plotly_chart(fig_pizza_categoria(df_cat), use_container_width=True, key="fig_cat_rede_adm")
        else: st.info("Sem dados")

    if not df.empty:
        show = df.copy()
        for col in ["receita_total", "preco_medio"]:
            if col in show.columns: show[col] = show[col].map(fmt_brl)
        st.dataframe(show, use_container_width=True, hide_index=True)


def _clientes_consolidado():
    kc    = kpi_clientes_rede() or {}
    total = int(kc.get("total_clientes") or 0)
    tm    = _f(kc.get("ticket_medio"))
    fq    = _f(kc.get("freq_media"))
    rc    = _f(kc.get("recencia_media"))

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Clientes únicos (rede)", f"{total:,}", None, None, min(100, total/max(total,1)*10), "Distintos", "👥")
    with c2: kpi_card("Ticket médio (rede)",    fmt_brl(tm), None, None, 75.0, "Histórico", "💳")
    with c3: kpi_card("Frequência média",        f"{fq:.1f}×", None, None, min(100, fq*10), "Visitas", "🔄")
    with c4: kpi_card("Recência média",          f"{rc:.0f}d", None, None, min(100, max(0, 100-rc)), "Dias", "📆")

    df_f = pd.DataFrame(clientes_faixa_rede())
    df_r = pd.DataFrame(clientes_rfm_rede(400))
    df_t = pd.DataFrame(clientes_top50_rede())

    u1, u2 = st.columns(2)
    with u1:
        if not df_f.empty: st.plotly_chart(fig_faixa_freq(df_f), use_container_width=True, key="fig_fq_rede_adm")
        else: st.info("Sem dados")
    with u2:
        if not df_r.empty: st.plotly_chart(fig_scatter_rfm(df_r), use_container_width=True, key="fig_rfm_rede_adm")
        else: st.info("Sem dados")

    st.subheader("Top 50 clientes da rede")
    if not df_t.empty: st.dataframe(df_t, use_container_width=True, hide_index=True)
    else: st.info("Sem dados")


def _plataformas_consolidado(dias: int):
    """
    Plataformas consolidadas via backup.vendas quando não há loja selecionada.
    Usa desc_partner_sale como proxy de plataforma.
    """
    from admin_queries import ranking_plataformas
    rows = ranking_plataformas(dias)

    if not rows:
        st.info("Sem dados de plataformas no período.")
        return

    st.markdown("""
<div style='color:#A0A0A8;font-size:.75rem;background:rgba(79,110,247,.08);
            border:1px solid rgba(79,110,247,.2);border-radius:8px;
            padding:8px 12px;margin-bottom:16px'>
  📊 Visão consolidada da rede por plataforma de venda
</div>""", unsafe_allow_html=True)

    COR_PLAT = {"ifood": "#C8102E", "anotaai": "#4f6ef7", "99food": "#F59E0B",
                "direto": "#22C55E", "outros": "#5A5A65"}

    cols = st.columns(min(len(rows), 4))
    for i, row in enumerate(rows[:4]):
        plat = row.get("plataforma") or "Outros"
        fat  = _f(row.get("faturamento"))
        peds = int(row.get("pedidos") or 0)
        tick = _f(row.get("ticket_medio"))
        pct  = _f(row.get("pct_faturamento"))
        key  = plat.lower().replace(" ", "")
        cor  = next((v for k, v in COR_PLAT.items() if k in key), "#5A5A65")
        with cols[i % len(cols)]:
            st.markdown(f"""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:14px;
            padding:16px;border-top:3px solid {cor}'>
  <div style='color:{cor};font-size:.68rem;font-weight:800;
              letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px'>{plat}</div>
  <div style='color:#F5F5F7;font-size:1.2rem;font-weight:800'>{fmt_brl(fat)}</div>
  <div style='color:#5A5A65;font-size:.65rem;margin-top:4px'>
    {pct:.1f}% do faturamento · {peds:,} pedidos
  </div>
  <div style='color:#A0A0A8;font-size:.68rem;margin-top:6px'>TM {fmt_brl(tick)}</div>
</div>""", unsafe_allow_html=True)

    # Gráfico
    st.markdown("<br>", unsafe_allow_html=True)
    nomes = [r.get("plataforma") or "—" for r in rows]
    fats  = [_f(r.get("faturamento")) for r in rows]
    cores = [next((v for k, v in COR_PLAT.items()
                   if k in (n.lower().replace(" ", ""))), "#5A5A65") for n in nomes]

    fig = go.Figure(go.Bar(
        x=nomes, y=fats, marker_color=cores,
        text=[f"R$ {f:,.0f}" for f in fats],
        textposition="outside",
        textfont=dict(color="#A0A0A8", size=11),
    ))
    fig.update_layout(**PLOTLY_THEME, height=300, showlegend=False)
    fig.update_layout(yaxis=dict(**PLOTLY_THEME["yaxis"], tickprefix="R$ ", tickformat=",.0f"))
    fig.update_layout(title=dict(text="Faturamento por plataforma (rede)", font=dict(color="#C8C8D0", size=13), x=0))
    st.plotly_chart(fig, use_container_width=True, key="plat_bar_consolidado")


def _mv_aviso_rede(icone: str, nome: str):
    """Aviso informativo — não bloqueante — para views semanais sem loja."""
    st.markdown(f"""
<div style='color:#A0A0A8;font-size:.75rem;background:rgba(245,158,11,.06);
            border:1px solid rgba(245,158,11,.2);border-radius:8px;
            padding:8px 12px;margin-bottom:16px'>
  ℹ️ Os dados de <strong>{nome}</strong> são semanais e indexados por unidade.
  Para ver o detalhamento completo, selecione uma loja no seletor acima.
  Abaixo estão os dados da <strong>rede consolidada</strong>.
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  RENDER PRINCIPAL
# ─────────────────────────────────────────────

def render_admin_panel():
    inject_global_css()

    st.markdown("""
<style>
section[data-testid='stSidebar']{display:none!important}
.main .block-container{
    padding-left:2rem!important;
    padding-right:2rem!important;
    padding-top:1rem!important;
}
</style>""", unsafe_allow_html=True)

    user     = st.session_state.user
    role     = (user.get("role") or "franqueado").lower()
    nome_adm = user.get("nome") or user.get("username") or "Usuário"
    iniciais = "".join(p[0].upper() for p in nome_adm.split()[:2]) or "?"
    dias_map = {"7 dias": 7, "30 dias": 30, "90 dias": 90}
    role_label = "Admin" if role == "admin" else "Franqueado"
    role_cor   = "#C8102E" if role == "admin" else "#4f6ef7"

    loja_atual  = st.session_state.loja_atual or {}
    trade_atual = loja_atual.get("trade_name") or ""
    is_geral    = (trade_atual in ("__admin__", "") or not trade_atual)

    # ── Header ──
    titulo = "📊 Painel Administrativo" if is_geral else f"🏪 {trade_atual}"
    label  = "Visão geral da rede" if is_geral else f"Loja selecionada"

    st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:12px'>
  <div style='display:flex;align-items:center;gap:14px'>
    <img src='{LOGO_URL}' style='height:34px;object-fit:contain'/>
    <div>
      <div style='color:#5A5A65;font-size:.6rem;font-weight:600;
                  letter-spacing:.1em;text-transform:uppercase'>{label}</div>
      <div style='color:#F5F5F7;font-size:1.3rem;font-weight:800;
                  letter-spacing:-.02em;margin-top:1px'>{titulo}</div>
    </div>
  </div>
  <div style='display:flex;align-items:center;gap:10px'>
    <div style='background:#1C1C1F;border:1px solid #2A2A2F;border-radius:10px;
                padding:6px 12px;display:flex;align-items:center;gap:8px'>
      <div style='width:26px;height:26px;border-radius:50%;background:#C8102E;
                  display:flex;align-items:center;justify-content:center;
                  color:white;font-size:.6rem;font-weight:800'>{iniciais}</div>
      <div>
        <div style='color:#F5F5F7;font-size:.72rem;font-weight:700'>{nome_adm}</div>
        <div style='color:{role_cor};font-size:.55rem;font-weight:700;
                    letter-spacing:.06em;text-transform:uppercase'>{role_label}</div>
      </div>
    </div>
    <div style='color:#5A5A65;font-size:.68rem'>{datetime.now().strftime("%d/%m/%Y %H:%M")}</div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Controles — layout diferente por role ──
    is_admin = (role == "admin")

    if is_admin:
        # Admin: loja livre + período + sair (3 colunas)
        cc1, cc2, cc3 = st.columns([2.8, 1.6, 0.5])
        with cc1:
            opts = ["— Todas as lojas (rede) —"] + [l["trade_name"] for l in user["lojas"]]
            idx  = 0
            if not is_geral and trade_atual in opts:
                idx = opts.index(trade_atual)
            escolha = st.selectbox("Loja", opts, index=idx,
                                   key="adm_loja", label_visibility="collapsed")
            if escolha == "— Todas as lojas (rede) —":
                if not is_geral:
                    st.session_state.loja_atual = {"id": None, "trade_name": "__admin__"}
                    st.session_state.chat = []
                    st.rerun()
            else:
                nova = next((l for l in user["lojas"] if l["trade_name"] == escolha), None)
                if nova and st.session_state.loja_atual != nova:
                    st.session_state.loja_atual = nova
                    st.session_state.chat = []
                    st.rerun()
        with cc2:
            periodo = st.selectbox("Período", list(dias_map.keys()), index=1,
                                   key="adm_periodo", label_visibility="collapsed")
        with cc3:
            if st.button("🚪 Sair", key="adm_sair", use_container_width=True):
                for k in ["user", "loja_atual", "chat"]:
                    st.session_state.pop(k, None)
                st.rerun()

    else:
        # Franqueado: seletor das SUAS lojas + período + sair
        lojas_franc = user.get("lojas") or []
        cc1, cc2, cc3 = st.columns([2.8, 1.6, 0.5])
        with cc1:
            if len(lojas_franc) > 1:
                # 2+ lojas → selectbox funcional (apenas as dele)
                nomes  = [l["trade_name"] for l in lojas_franc]
                cur    = trade_atual if trade_atual in nomes else nomes[0]
                idx    = nomes.index(cur)
                escolha = st.selectbox("Loja", nomes, index=idx,
                                       key="franc_loja", label_visibility="collapsed")
                if escolha != trade_atual:
                    nova = next((l for l in lojas_franc if l["trade_name"] == escolha), None)
                    if nova:
                        st.session_state.loja_atual = nova
                        st.session_state.chat = []
                        st.rerun()
            else:
                # 1 loja → display fixo (sem troca possível)
                st.markdown(f"""
<div style='background:#1C1C1F;border:1px solid #2A2A2F;border-radius:8px;
            padding:8px 12px;height:38px;display:flex;align-items:center;gap:8px'>
  <span>🏪</span>
  <span style='color:#F5F5F7;font-size:.82rem;font-weight:600'>{trade_atual}</span>
</div>""", unsafe_allow_html=True)
        with cc2:
            periodo = st.selectbox("Período", list(dias_map.keys()), index=1,
                                   key="franc_periodo", label_visibility="collapsed")
        with cc3:
            if st.button("🚪 Sair", key="franc_sair", use_container_width=True):
                for k in ["user", "loja_atual", "chat"]:
                    st.session_state.pop(k, None)
                st.rerun()

    # variável unificada de dias
    dias_map_ref = {"7 dias": 7, "30 dias": 30, "90 dias": 90}
    periodo_key  = "adm_periodo" if is_admin else "franc_periodo"

    st.markdown("<hr style='border-color:#2A2A2F;margin:8px 0 14px'>",
                unsafe_allow_html=True)

    dias    = dias_map.get(st.session_state.get(periodo_key, "30 dias"), 30)
    loja_id = loja_atual.get("id")

    # ── Abas — separadas por role ──
    if is_admin:
        (t_geral, t_rank, t_vend, t_card, t_cli,
         t_metas, t_plat, t_tick, t_recorr,
         t_usuarios, t_ia) = st.tabs([
            "📊  Visão Geral", "🏆  Ranking", "📈  Vendas",
            "🍽️  Cardápio", "👥  Clientes", "🎯  Metas",
            "📡  Plataformas", "🎟️  Tickets", "🔄  Recorrência",
            "👤  Usuários", "🤖  IA - IH",
        ])
    else:
        t_geral = t_rank = t_usuarios = None  # franqueado não vê essas
        (t_vend, t_card, t_cli,
         t_metas, t_plat, t_tick, t_recorr, t_ia) = st.tabs([
            "📈  Vendas", "🍽️  Cardápio", "👥  Clientes",
            "🎯  Metas", "📡  Plataformas", "🎟️  Tickets",
            "🔄  Recorrência", "🤖  IA - IH",
        ])

    # ══════════ VISÃO GERAL (admin only) ══════════
    if is_admin and t_geral is not None:
      with t_geral:
        kv     = kpi_admin(dias)
        fat    = float(kv.get("faturamento_total") or 0)
        ped    = int(kv.get("total_pedidos") or 0)
        tick   = float(kv.get("ticket_medio") or 0)
        nlojas = int(kv.get("total_lojas") or 0)
        fat_hj = float(kv.get("fat_hoje") or 0)

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: _kpi("💰 Fat. total rede", f"R$ {fat:,.0f}")
        with c2: _kpi("🛒 Total pedidos",   f"{ped:,}")
        with c3: _kpi("🎟️ Ticket médio",    f"R$ {tick:,.2f}")
        with c4: _kpi("🏪 Lojas ativas",    str(nlojas))
        with c5: _kpi("📅 Fat. hoje",        f"R$ {fat_hj:,.0f}")

        st.markdown("<br>", unsafe_allow_html=True)
        serie = serie_admin(dias)
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
            fig.update_layout(**PLOTLY_THEME, height=340)
            fig.update_layout(yaxis=dict(
                gridcolor="#1C1C1F", showline=False,
                tickfont=dict(color="#8A8A95", size=11),
                tickprefix="R$ ", tickformat=",.0f", zeroline=False,
            ))
            fig.update_layout(title=dict(
                text=f"Faturamento diário da rede — últimos {dias} dias",
                font=dict(color="#C8C8D0", size=13), x=0,
            ))
            st.plotly_chart(fig, use_container_width=True, key="adm_serie_vg")
        else:
            st.info("Sem dados de série temporal.")

    # ══════════ RANKING (admin only) ══════════
    if is_admin and t_rank is not None:
      with t_rank:
        ranking = ranking_lojas(dias)
        st.markdown(f"""
<div style='color:#F5F5F7;font-size:.95rem;font-weight:800;margin-bottom:14px'>
  🏆 Top {min(len(ranking), 10)} Unidades por Faturamento
  <span style='color:#5A5A65;font-size:.72rem;font-weight:400;margin-left:8px'>
    últimos {dias} dias
  </span>
</div>""", unsafe_allow_html=True)

        if ranking:
            max_fat = max(float(r.get("faturamento") or 0) for r in ranking) or 1
            cores   = {1: "#F59E0B", 2: "#A0A0A8", 3: "#C8102E"}
            for i, row in enumerate(ranking[:10]):
                pos  = i + 1
                fat  = float(row.get("faturamento") or 0)
                pct  = fat / max_fat * 100
                nome = row.get("trade_name") or "—"
                cor  = cores.get(pos, "#3A3A4A")
                var  = row.get("variacao_pct")
                var_html = ""
                if var is not None:
                    vc = "#22C55E" if var >= 0 else "#EF4444"
                    vb = "rgba(34,197,94,.1)" if var >= 0 else "rgba(239,68,68,.1)"
                    va = "↑" if var >= 0 else "↓"
                    var_html = (f"<span style='background:{vb};color:{vc};font-size:.6rem;"
                                f"font-weight:700;padding:2px 7px;border-radius:99px'>"
                                f"{va} {abs(var):.1f}%</span>")

                st.markdown(f"""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:12px;
            padding:12px 16px;margin-bottom:8px'>
  <div style='display:flex;align-items:center;gap:12px'>
    <div style='min-width:32px;height:32px;border-radius:8px;
                background:rgba(200,16,46,.08);display:flex;align-items:center;
                justify-content:center;flex-shrink:0'>
      <span style='color:{cor};font-size:.72rem;font-weight:800'>#{pos}</span>
    </div>
    <div style='flex:1;min-width:0'>
      <div style='display:flex;align-items:center;gap:8px;margin-bottom:5px'>
        <span style='color:#F5F5F7;font-size:.85rem;font-weight:700;
                     white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{nome}</span>
        {var_html}
      </div>
      <div style='background:#1C1C1F;border-radius:99px;height:4px'>
        <div style='width:{pct:.0f}%;height:4px;border-radius:99px;
                    background:linear-gradient(90deg,#C8102E,#E8304A)'></div>
      </div>
    </div>
    <div style='text-align:right;flex-shrink:0;min-width:120px'>
      <div style='color:#F5F5F7;font-size:.88rem;font-weight:700'>R$ {fat:,.0f}</div>
      <div style='color:#5A5A65;font-size:.65rem;margin-top:2px'>
        {int(row.get("pedidos") or 0):,} pedidos
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.info("Sem dados de faturamento no período.")

    # ══════════ VENDAS ══════════
    with t_vend:
        if is_geral:
            st.caption("📊 Dados consolidados da rede toda")
            _vendas_consolidada(dias)
        else:
            tab_vendas(trade_atual, loja_id or 0, dias)

    # ══════════ CARDÁPIO ══════════
    with t_card:
        if is_geral:
            st.caption("📊 Dados consolidados da rede toda")
            _cardapio_consolidado(dias)
        else:
            tab_cardapio(trade_atual, dias)

    # ══════════ CLIENTES ══════════
    with t_cli:
        if is_geral:
            st.caption("📊 Dados consolidados da rede toda")
            _clientes_consolidado()
        else:
            tab_clientes(trade_atual)

    # ══════════ METAS ══════════
    with t_metas:
        if is_geral:
            st.info("🎯 Metas são configuradas por unidade. Selecione uma loja acima para visualizar.")
        else:
            tab_metas(trade_atual, loja_id or 0)

    # ══════════ PLATAFORMAS ══════════
    with t_plat:
        if is_geral:
            _mv_aviso_rede("📡", "Plataformas (dados semanais)")
            _plataformas_consolidado(dias)
        else:
            st.caption(f"📡 Plataformas — {trade_atual}")
            render_plataformas(trade_atual)

    # ══════════ TICKETS ══════════
    with t_tick:
        if is_geral:
            _mv_aviso_rede("🎟️", "Tickets & Descontos (dados semanais)")
            # Mostra ticket médio consolidado como fallback
            from admin_queries import ranking_ticket_por_loja
            rows_tk = ranking_ticket_por_loja(dias, 10)
            if rows_tk:
                st.markdown("**Ranking de Ticket Médio por Loja**")
                for i, row in enumerate(rows_tk):
                    st.markdown(f"`#{i+1}` **{row.get('trade_name','—')}** — "
                                f"TM R$ {float(row.get('ticket_medio') or 0):,.2f} "
                                f"({int(row.get('pedidos') or 0):,} pedidos)")
            else:
                st.info("Sem dados de ticket no período.")
        else:
            st.caption(f"🎟️ Tickets & Descontos — {trade_atual}")
            render_tickets_descontos(trade_atual)

    # ══════════ RECORRÊNCIA ══════════
    with t_recorr:
        if is_geral:
            _mv_aviso_rede("🔄", "Recorrência (dados semanais)")
            # Mostra recorrência consolidada como fallback
            kc = kpi_clientes_rede() or {}
            fm = float(kc.get("freq_media") or 0)
            rc = float(kc.get("recencia_media") or 0)
            c1, c2, c3 = st.columns(3)
            with c1: _kpi("Freq. média (rede)", f"{fm:.1f}×")
            with c2: _kpi("Recência média (rede)", f"{rc:.0f} dias")
            with c3: _kpi("Clientes únicos (rede)", f"{int(kc.get('total_clientes') or 0):,}")

            df_f = pd.DataFrame(clientes_faixa_rede())
            if not df_f.empty:
                st.plotly_chart(__import__('charts').fig_faixa_freq(df_f),
                                use_container_width=True, key="fig_fq_recorr_adm")
        else:
            st.caption(f"🔄 Recorrência — {trade_atual}")
            render_recorrencia(trade_atual)

    # ══════════ USUÁRIOS (admin only) ══════════
    if is_admin and t_usuarios is not None:
      with t_usuarios:
        render_gerenciar_usuarios()

    # ══════════ IA ══════════
    with t_ia:
        render_ia_tab(st.session_state.user, st.session_state.loja_atual)
