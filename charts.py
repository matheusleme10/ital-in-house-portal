from decimal import Decimal

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from theme import COLOR_MAIN, COLOR_MUTED, COLOR_RAMP, PLOTLY_THEME


def _to_float(x):
    if x is None:
        return 0.0
    if isinstance(x, Decimal):
        return float(x)
    return float(x)


def apply_layout(fig):
    fig.update_layout(**PLOTLY_THEME)
    return fig


def fig_faturamento_diario(df: pd.DataFrame):
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados no período", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return apply_layout(fig)
    df = df.copy()
    df["data"] = pd.to_datetime(df["data"])
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["data"],
            y=df["faturamento"].map(_to_float),
            fill="tozeroy",
            mode="lines",
            line=dict(color=COLOR_MAIN, width=2),
            fillcolor="rgba(200,16,46,0.25)",
            name="Faturamento",
        )
    )
    fig.update_layout(hovermode="x unified", yaxis_title="R$")
    return apply_layout(fig)


def fig_pizza_status(df: pd.DataFrame):
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return apply_layout(fig)
    fig = px.pie(
        df,
        names="status",
        values="quantidade",
        color_discrete_sequence=COLOR_RAMP,
        hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return apply_layout(fig)


def fig_barras_pedidos(df: pd.DataFrame):
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return apply_layout(fig)
    df = df.copy()
    df["data"] = pd.to_datetime(df["data"])
    fig = px.bar(
        df,
        x="data",
        y="pedidos",
        color_discrete_sequence=[COLOR_MAIN],
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Pedidos")
    return apply_layout(fig)


def fig_top_itens_horizontal(df: pd.DataFrame, n: int = 10):
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return apply_layout(fig)
    sub = df.head(n).iloc[::-1]
    fig = px.bar(
        sub,
        x="receita_total",
        y="produto",
        orientation="h",
        color_discrete_sequence=[COLOR_MAIN],
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(showlegend=False, xaxis_title="Receita (R$)", yaxis_title="")
    return apply_layout(fig)


def fig_pizza_categoria(df: pd.DataFrame):
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return apply_layout(fig)
    fig = px.pie(
        df,
        names="categoria",
        values="receita",
        color_discrete_sequence=COLOR_RAMP,
        hole=0.4,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return apply_layout(fig)


def fig_faixa_freq(df: pd.DataFrame):
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return apply_layout(fig)
    order = ["1", "2–4", "5–9", "10–14", "15+"]
    df = df.copy()
    df["faixa"] = pd.Categorical(df["faixa"].astype(str), categories=order, ordered=True)
    df = df.sort_values("faixa")
    fig = px.bar(
        df,
        x="faixa",
        y="qtd",
        color_discrete_sequence=[COLOR_MAIN],
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(showlegend=False, xaxis_title="Faixa de frequência", yaxis_title="Clientes")
    return apply_layout(fig)


def fig_scatter_rfm(df: pd.DataFrame):
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return apply_layout(fig)
    d = df.copy()
    d["_tm"] = d["ticket_medio"].map(_to_float)
    d = d.dropna(subset=["recencia", "frequencia", "_tm"])
    if d.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return apply_layout(fig)
    fig = px.scatter(
        d,
        x="recencia",
        y="frequencia",
        size="_tm",
        hover_name="full_name",
        color_discrete_sequence=[COLOR_MAIN],
    )
    fig.update_traces(marker=dict(line=dict(width=0)), selector=dict(mode="markers"))
    fig.update_layout(showlegend=False, xaxis_title="Recência", yaxis_title="Frequência")
    return apply_layout(fig)


def fig_metas_agrupadas(df: pd.DataFrame):
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return apply_layout(fig)
    df = df.iloc[::-1].copy()
    df["label"] = df.apply(lambda r: f"{int(r['mes']):02d}/{int(r['ano'])}", axis=1)
    fig = go.Figure(
        data=[
            go.Bar(name="Meta", x=df["label"], y=df["meta_vendas"].map(_to_float), marker_color=COLOR_MUTED),
            go.Bar(
                name="Realizado",
                x=df["label"],
                y=df["realizado_vendas"].map(_to_float),
                marker_color=COLOR_MAIN,
            ),
        ]
    )
    fig.update_layout(barmode="group", xaxis_title="", yaxis_title="R$", legend=dict(orientation="h", yanchor="bottom", y=1.02))
    return apply_layout(fig)


def fig_gauge_metas(pct: float):
    pct = max(0.0, min(float(pct or 0), 200.0))
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=pct,
            number=dict(suffix="%", font=dict(color="#F5F5F7")),
            gauge=dict(
                axis=dict(range=[0, 120], tickcolor="#5A5A65"),
                bar=dict(color=COLOR_MAIN),
                bgcolor="#141416",
                borderwidth=1,
                bordercolor="#2A2A2F",
                steps=[
                    dict(range=[0, 60], color="rgba(42,42,47,0.5)"),
                    dict(range=[60, 100], color="rgba(200,16,46,0.15)"),
                    dict(range=[100, 120], color="rgba(34,197,94,0.12)"),
                ],
                threshold=dict(line=dict(color="#F5F5F7", width=2), thickness=0.85, value=100),
            ),
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#A0A0A8", family="Plus Jakarta Sans"),
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )
    return fig
