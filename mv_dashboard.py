"""3 novas abas do dashboard usando as materialized views do schema views_n8n."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from mv_queries import (
    _f, _semana_label,
    mv_descontos, mv_faturamento, mv_pedidos,
    mv_percentuais, mv_tickets, mv_vendas,
)
from theme import COLOR_MAIN, PLOTLY_THEME

# ── Paleta de plataformas ──────────────────────────────
COR = {
    "iFood":   "#C8102E",
    "Anotaai": "#4f6ef7",
    "99Food":  "#F59E0B",
    "Direto":  "#22C55E",
    "Outros":  "#5A5A65",
    "Almoço":  "#C8102E",
    "Janta":   "#4f6ef7",
    "Recor":   "#22C55E",
    "Novos":   "#4f6ef7",
    "NI":      "#5A5A65",
}

SEMANAS_OPTS = [4, 8, 12, 24]


def _base_layout(**extra):
    layout = {**PLOTLY_THEME, "height": 320}
    layout.update(extra)
    return layout


def _kpi(label: str, valor: str, delta: str = "", pos: bool = True):
    cor  = "#22C55E" if pos else "#EF4444"
    bg   = "rgba(34,197,94,.1)" if pos else "rgba(239,68,68,.1)"
    d_html = (
        f"<div style='display:inline-block;background:{bg};color:{cor};"
        f"font-size:.62rem;font-weight:600;padding:2px 8px;"
        f"border-radius:99px;margin-top:4px'>{delta}</div>"
    ) if delta else ""
    st.markdown(f"""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:12px;
            padding:14px 18px'>
  <div style='color:#5A5A65;font-size:.6rem;font-weight:600;
              letter-spacing:.09em;text-transform:uppercase;margin-bottom:5px'>
    {label}
  </div>
  <div style='color:#F5F5F7;font-size:1.45rem;font-weight:800;
              letter-spacing:-.02em'>{valor}</div>
  {d_html}
</div>""", unsafe_allow_html=True)


def _labels(rows: list) -> list:
    return [_semana_label(r.get("semana_ano", "")) for r in rows]


# ══════════════════════════════════════════════════════
#  ABA 1 — PLATAFORMAS
# ══════════════════════════════════════════════════════

def render_plataformas(trade_name: str):
    st.markdown("<br>", unsafe_allow_html=True)
    col_s, _ = st.columns([0.3, 0.7])
    with col_s:
        semanas = st.selectbox("📅 Semanas", SEMANAS_OPTS, index=1,
                               key="plat_semanas")

    fat  = mv_faturamento(trade_name, semanas)
    ped  = mv_pedidos(trade_name, semanas)
    fat4 = mv_faturamento(trade_name, 4)

    if not fat:
        st.info("Sem dados de faturamento no período.")
        return

    # ── KPIs (soma últimas 4 semanas) ──
    kpi_ifood   = sum(_f(r.get("faturamento_ifood"))   for r in fat4)
    kpi_anotaai = sum(_f(r.get("faturamento_anotaai")) for r in fat4)
    kpi_99food  = sum(_f(r.get("faturamento_99food"))  for r in fat4)
    kpi_outros  = sum(_f(r.get("faturamento_outros"))  for r in fat4)

    c1, c2, c3, c4 = st.columns(4)
    with c1: _kpi("iFood (4 sem.)",   f"R$ {kpi_ifood:,.2f}")
    with c2: _kpi("Anotaai (4 sem.)", f"R$ {kpi_anotaai:,.2f}")
    with c3: _kpi("99Food (4 sem.)",  f"R$ {kpi_99food:,.2f}")
    with c4: _kpi("Outros (4 sem.)",  f"R$ {kpi_outros:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)
    labels = _labels(fat)

    # ── Barras: faturamento por plataforma ──
    col_a, col_b = st.columns(2)
    with col_a:
        fig = go.Figure()
        for campo, nome, cor in [
            ("faturamento_ifood",   "iFood",   COR["iFood"]),
            ("faturamento_anotaai", "Anotaai", COR["Anotaai"]),
            ("faturamento_99food",  "99Food",  COR["99Food"]),
            ("faturamento_outros",  "Outros",  COR["Outros"]),
        ]:
            fig.add_trace(go.Bar(
                name=nome,
                x=labels,
                y=[_f(r.get(campo)) for r in fat],
                marker_color=cor,
            ))
        fig.update_layout(**_base_layout(
            barmode="group",
            title=dict(text="Faturamento por plataforma", font=dict(color="#C8C8D0", size=13), x=0),
            yaxis=dict(**PLOTLY_THEME["yaxis"], tickprefix="R$ ", tickformat=",.0f"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        font=dict(color="#A0A0A8", size=10)),
        ))
        st.plotly_chart(fig, use_container_width=True, key="plat_fat_bar")

    with col_b:
        total = kpi_ifood + kpi_anotaai + kpi_99food + kpi_outros
        if total > 0:
            fig2 = go.Figure(go.Pie(
                labels=["iFood", "Anotaai", "99Food", "Outros"],
                values=[kpi_ifood, kpi_anotaai, kpi_99food, kpi_outros],
                marker_colors=[COR["iFood"], COR["Anotaai"], COR["99Food"], COR["Outros"]],
                hole=0.45,
                textinfo="percent+label",
                textfont=dict(color="#F5F5F7", size=11),
            ))
            fig2.update_layout(**_base_layout(
                title=dict(text="Participação % no faturamento", font=dict(color="#C8C8D0", size=13), x=0),
            ))
            st.plotly_chart(fig2, use_container_width=True, key="plat_pizza")

    # ── Pedidos: almoço vs janta ──
    if ped:
        labels_p = _labels(ped)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            name="Almoço", x=labels_p,
            y=[_f(r.get("pedidos_total_almoco")) for r in ped],
            marker_color=COR["Almoço"],
        ))
        fig3.add_trace(go.Bar(
            name="Janta", x=labels_p,
            y=[_f(r.get("pedidos_total_janta")) for r in ped],
            marker_color=COR["Janta"],
        ))
        fig3.update_layout(**_base_layout(
            barmode="group",
            title=dict(text="Pedidos — Almoço vs Janta", font=dict(color="#C8C8D0", size=13), x=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        font=dict(color="#A0A0A8", size=10)),
        ))
        st.plotly_chart(fig3, use_container_width=True, key="plat_ped_bar")

    # ── Tabela ──
    st.markdown("#### 📋 Faturamento por plataforma — semana a semana")
    df = pd.DataFrame([{
        "Semana":      _semana_label(r.get("semana_ano", "")),
        "Total":       f"R$ {_f(r.get('faturamento_total')):,.2f}",
        "iFood":       f"R$ {_f(r.get('faturamento_ifood')):,.2f}",
        "Anotaai":     f"R$ {_f(r.get('faturamento_anotaai')):,.2f}",
        "99Food":      f"R$ {_f(r.get('faturamento_99food')):,.2f}",
        "Outros":      f"R$ {_f(r.get('faturamento_outros')):,.2f}",
        "Recorrentes": f"R$ {_f(r.get('faturamento_recorrentes')):,.2f}",
        "Não Recor.":  f"R$ {_f(r.get('faturamento_nao_recorrente')):,.2f}",
        "Green":       f"R$ {_f(r.get('faturamento_green')):,.2f}",
    } for r in reversed(fat[:8])])
    st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════
#  ABA 2 — TICKETS & DESCONTOS
# ══════════════════════════════════════════════════════

def render_tickets_descontos(trade_name: str):
    st.markdown("<br>", unsafe_allow_html=True)
    col_s, _ = st.columns([0.3, 0.7])
    with col_s:
        semanas = st.selectbox("📅 Semanas", SEMANAS_OPTS, index=1,
                               key="tick_semanas")

    tkt  = mv_tickets(trade_name, semanas)
    desc = mv_descontos(trade_name, semanas)
    tkt4 = mv_tickets(trade_name, 4)
    d4   = mv_descontos(trade_name, 4)

    if not tkt:
        st.info("Sem dados de tickets no período.")
        return

    # ── KPIs ──
    tkt_tot  = (sum(_f(r.get("Tkt med tot")) for r in tkt4) / len(tkt4)) if tkt4 else 0
    tkt_alm  = (sum(_f(r.get("Tkt almoço")) for r in tkt4) / len(tkt4)) if tkt4 else 0
    tkt_jan  = (sum(_f(r.get("Tkt jantar")) for r in tkt4) / len(tkt4)) if tkt4 else 0
    desc_tot = sum(_f(r.get("total_desconto_geral")) for r in d4) if d4 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: _kpi("Ticket médio (4 sem.)", f"R$ {tkt_tot:,.2f}")
    with c2: _kpi("Ticket almoço",         f"R$ {tkt_alm:,.2f}")
    with c3: _kpi("Ticket janta",          f"R$ {tkt_jan:,.2f}")
    with c4: _kpi("Desconto total (4 sem.)", f"R$ {desc_tot:,.2f}", pos=False)

    st.markdown("<br>", unsafe_allow_html=True)
    labels = _labels(tkt)

    col_a, col_b = st.columns(2)

    # ── Linhas: ticket por plataforma ──
    with col_a:
        fig = go.Figure()
        for campo, nome, cor in [
            ("Tkt ifood",  "iFood",  COR["iFood"]),
            ("Tkt 99food", "99Food", COR["99Food"]),
            ("Tkt dir",    "Direto", COR["Direto"]),
        ]:
            fig.add_trace(go.Scatter(
                name=nome, x=labels,
                y=[_f(r.get(campo)) for r in tkt],
                mode="lines+markers",
                line=dict(color=cor, width=2),
                marker=dict(size=5),
            ))
        fig.update_layout(**_base_layout(
            title=dict(text="Ticket médio por plataforma", font=dict(color="#C8C8D0", size=13), x=0),
            yaxis=dict(**PLOTLY_THEME["yaxis"], tickprefix="R$ ", tickformat=",.0f"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        font=dict(color="#A0A0A8", size=10)),
        ))
        st.plotly_chart(fig, use_container_width=True, key="tick_linha")

    # ── Barras: recorrentes vs novos ──
    with col_b:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name="Recorrentes", x=labels,
            y=[_f(r.get("Tkt med rec")) for r in tkt],
            marker_color=COR["Recor"],
        ))
        fig2.add_trace(go.Bar(
            name="Novos", x=labels,
            y=[_f(r.get("Tkt med pri")) for r in tkt],
            marker_color=COR["Novos"],
        ))
        fig2.update_layout(**_base_layout(
            barmode="group",
            title=dict(text="Ticket — Recorrentes vs Novos", font=dict(color="#C8C8D0", size=13), x=0),
            yaxis=dict(**PLOTLY_THEME["yaxis"], tickprefix="R$ ", tickformat=",.0f"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        font=dict(color="#A0A0A8", size=10)),
        ))
        st.plotly_chart(fig2, use_container_width=True, key="tick_rec_bar")

    # ── Barras: descontos por plataforma ──
    if desc:
        labels_d = _labels(desc)
        fig3 = go.Figure()
        for campo, nome, cor in [
            ("total_desconto_ifood",   "iFood",   COR["iFood"]),
            ("total_desconto_anotaai", "Anotaai", COR["Anotaai"]),
            ("total_desconto_99food",  "99Food",  COR["99Food"]),
            ("total_desconto_outros",  "Outros",  COR["Outros"]),
        ]:
            fig3.add_trace(go.Bar(
                name=nome, x=labels_d,
                y=[_f(r.get(campo)) for r in desc],
                marker_color=cor,
            ))
        fig3.update_layout(**_base_layout(
            barmode="group",
            title=dict(text="Desconto por plataforma", font=dict(color="#C8C8D0", size=13), x=0),
            yaxis=dict(**PLOTLY_THEME["yaxis"], tickprefix="R$ ", tickformat=",.0f"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        font=dict(color="#A0A0A8", size=10)),
        ))
        st.plotly_chart(fig3, use_container_width=True, key="desc_bar")

    # ── Tabela ──
    st.markdown("#### 📋 Tickets & Descontos — semana a semana")
    rows_tbl = []
    for i, r in enumerate(reversed(tkt[:8])):
        desc_row = list(reversed(desc[:8]))[i] if desc and i < len(desc) else {}
        rows_tbl.append({
            "Semana":      _semana_label(r.get("semana_ano", "")),
            "Tkt Total":   f"R$ {_f(r.get('Tkt med tot')):,.2f}",
            "Tkt iFood":   f"R$ {_f(r.get('Tkt ifood')):,.2f}",
            "Tkt 99Food":  f"R$ {_f(r.get('Tkt 99food')):,.2f}",
            "Tkt Direto":  f"R$ {_f(r.get('Tkt dir')):,.2f}",
            "Tkt Almoço":  f"R$ {_f(r.get('Tkt almoço')):,.2f}",
            "Tkt Janta":   f"R$ {_f(r.get('Tkt jantar')):,.2f}",
            "Desc. Geral": f"R$ {_f(desc_row.get('total_desconto_geral')):,.2f}",
        })
    st.dataframe(pd.DataFrame(rows_tbl), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════
#  ABA 3 — RECORRÊNCIA
# ══════════════════════════════════════════════════════

def render_recorrencia(trade_name: str):
    st.markdown("<br>", unsafe_allow_html=True)
    col_s, _ = st.columns([0.3, 0.7])
    with col_s:
        semanas = st.selectbox("📅 Semanas", SEMANAS_OPTS, index=1,
                               key="rec_semanas")

    perc = mv_percentuais(trade_name, semanas)
    fat  = mv_faturamento(trade_name, semanas)
    vend = mv_vendas(trade_name, semanas)
    ped  = mv_pedidos(trade_name, semanas)
    p4   = mv_percentuais(trade_name, 4)
    ped4 = mv_pedidos(trade_name, 4)

    if not perc:
        st.info("Sem dados de recorrência no período.")
        return

    # ── KPIs ──
    prc_rec  = (sum(_f(r.get("Perc Recor")) for r in p4) / len(p4)) if p4 else 0
    prc_nov  = (sum(_f(r.get("Perc Novos")) for r in p4) / len(p4)) if p4 else 0
    prc_ni   = (sum(_f(r.get("Perc NI"))    for r in p4) / len(p4)) if p4 else 0
    ped_green = sum(_f(r.get("pedidos_green")) for r in ped4) if ped4 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: _kpi("% Recorrentes (4 sem.)", f"{prc_rec:.1f}%",  pos=True)
    with c2: _kpi("% Novos (4 sem.)",       f"{prc_nov:.1f}%",  pos=True)
    with c3: _kpi("% Não Identificados",    f"{prc_ni:.1f}%",   pos=False)
    with c4: _kpi("Pedidos Green (4 sem.)", f"{ped_green:.0f}", pos=True)

    st.markdown("<br>", unsafe_allow_html=True)
    labels = _labels(perc)

    col_a, col_b = st.columns(2)

    # ── Área empilhada: Recor vs Novos vs NI ──
    with col_a:
        fig = go.Figure()
        for campo, nome, cor in [
            ("Perc Recor", "Recorrentes", COR["Recor"]),
            ("Perc Novos", "Novos",       COR["Novos"]),
            ("Perc NI",    "Não Ident.",  COR["NI"]),
        ]:
            fig.add_trace(go.Scatter(
                name=nome, x=labels,
                y=[_f(r.get(campo)) for r in perc],
                mode="lines",
                fill="tonexty",
                line=dict(color=cor, width=1.5),
                stackgroup="one",
            ))
        fig.update_layout(**_base_layout(
            title=dict(text="% Recorrentes vs Novos vs NI", font=dict(color="#C8C8D0", size=13), x=0),
            yaxis=dict(**PLOTLY_THEME["yaxis"], ticksuffix="%"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        font=dict(color="#A0A0A8", size=10)),
        ))
        st.plotly_chart(fig, use_container_width=True, key="rec_area")

    # ── Pizza: almoço vs janta ──
    with col_b:
        if perc:
            alm = sum(_f(r.get("Perc Faturamento Almoço")) for r in p4)
            jan = sum(_f(r.get("Perc Faturamento Jantar")) for r in p4)
            if alm + jan > 0:
                fig2 = go.Figure(go.Pie(
                    labels=["Almoço", "Janta"],
                    values=[alm, jan],
                    marker_colors=[COR["Almoço"], COR["Janta"]],
                    hole=0.45,
                    textinfo="percent+label",
                    textfont=dict(color="#F5F5F7", size=12),
                ))
                fig2.update_layout(**_base_layout(
                    title=dict(text="Almoço vs Janta (últimas 4 sem.)",
                               font=dict(color="#C8C8D0", size=13), x=0),
                ))
                st.plotly_chart(fig2, use_container_width=True, key="rec_pizza")

    # ── Linhas: faturamento recorrentes vs não recorrentes ──
    if fat:
        labels_f = _labels(fat)
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            name="Recorrentes", x=labels_f,
            y=[_f(r.get("faturamento_recorrentes")) for r in fat],
            mode="lines+markers",
            line=dict(color=COR["Recor"], width=2),
            marker=dict(size=5),
        ))
        fig3.add_trace(go.Scatter(
            name="Não Recorrentes", x=labels_f,
            y=[_f(r.get("faturamento_nao_recorrente")) for r in fat],
            mode="lines+markers",
            line=dict(color=COR["Novos"], width=2),
            marker=dict(size=5),
        ))
        fig3.update_layout(**_base_layout(
            title=dict(text="Faturamento — Recorrentes vs Não Recorrentes",
                       font=dict(color="#C8C8D0", size=13), x=0),
            yaxis=dict(**PLOTLY_THEME["yaxis"], tickprefix="R$ ", tickformat=",.0f"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        font=dict(color="#A0A0A8", size=10)),
        ))
        st.plotly_chart(fig3, use_container_width=True, key="rec_linha_fat")

    # ── Barras: vendas almoço vs janta ──
    if vend:
        labels_v = _labels(vend)
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            name="Almoço", x=labels_v,
            y=[_f(r.get("venda_total_almoco")) for r in vend],
            marker_color=COR["Almoço"],
        ))
        fig4.add_trace(go.Bar(
            name="Janta", x=labels_v,
            y=[_f(r.get("venda_total_janta")) for r in vend],
            marker_color=COR["Janta"],
        ))
        fig4.update_layout(**_base_layout(
            barmode="group",
            title=dict(text="Vendas — Almoço vs Janta",
                       font=dict(color="#C8C8D0", size=13), x=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        font=dict(color="#A0A0A8", size=10)),
        ))
        st.plotly_chart(fig4, use_container_width=True, key="rec_vend_bar")

    # ── Tabela ──
    st.markdown("#### 📋 Recorrência — semana a semana")
    df = pd.DataFrame([{
        "Semana":      _semana_label(r.get("semana_ano", "")),
        "% Recor.":    f"{_f(r.get('Perc Recor')):.1f}%",
        "% Novos":     f"{_f(r.get('Perc Novos')):.1f}%",
        "% NI":        f"{_f(r.get('Perc NI')):.1f}%",
        "% iFood":     f"{_f(r.get('Perc ifood')):.1f}%",
        "% Anotaai":   f"{_f(r.get('Perc anotai')):.1f}%",
        "% 99Food":    f"{_f(r.get('Perc 99food')):.1f}%",
        "% Almoço":    f"{_f(r.get('Perc Faturamento Almoço')):.1f}%",
        "% Janta":     f"{_f(r.get('Perc Faturamento Jantar')):.1f}%",
    } for r in reversed(perc[:8])])
    st.dataframe(df, use_container_width=True, hide_index=True)
