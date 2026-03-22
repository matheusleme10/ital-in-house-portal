"""Visual identity — CSS global + Plotly theme (Ital In House)."""

import streamlit as st

# ── Plotly ──────────────────────────────────────────────
PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#A0A0A8", family="Plus Jakarta Sans", size=12),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(
        gridcolor="#1C1C1F",
        showline=False,
        tickfont=dict(color="#8A8A95", size=11),
        title_font=dict(color="#5A5A65"),
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="#1C1C1F",
        showline=False,
        tickfont=dict(color="#8A8A95", size=11),
        title_font=dict(color="#5A5A65"),
        zeroline=False,
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color="#A0A0A8", size=11),
    ),
    title=dict(
        font=dict(color="#C8C8D0", size=13, family="Plus Jakarta Sans"),
        x=0,
        pad=dict(b=8),
    ),
    hoverlabel=dict(
        bgcolor="#1C1C1F",
        bordercolor="#2A2A2F",
        font=dict(color="#F5F5F7", size=12),
    ),
)

COLOR_RAMP  = ["#C8102E", "#E8304A", "#FF6B6B", "#FF9999", "#FFCCCC"]
COLOR_MAIN  = "#C8102E"
COLOR_MUTED = "#2A2A2F"


def inject_global_css() -> None:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

/* ── Base ── */
html, body, [class*="css"], .stMarkdown, label, p, span, div {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.stApp { background: #0C0C0E !important; }
section[data-testid="stAppViewContainer"] > .main {
    background: #0C0C0E;
    color: #F5F5F7;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #141416 !important;
    border-right: 1px solid #2A2A2F !important;
}
[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }

/* ── Headings ── */
h1, h2, h3 {
    color: #F5F5F7 !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}

/* ── KPI cards ── */
[data-testid="stMetric"] {
    background: #141416 !important;
    border: 1px solid #2A2A2F !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    transition: border-color .2s, box-shadow .2s;
}
[data-testid="stMetric"]:hover {
    border-color: #C8102E !important;
    box-shadow: 0 0 20px rgba(200,16,46,.08) !important;
}
[data-testid="stMetricValue"] {
    color: #F5F5F7 !important;
    font-size: 1.7rem !important;
    font-weight: 800 !important;
    letter-spacing: -.02em !important;
}
[data-testid="stMetricLabel"] {
    color: #5A5A65 !important;
    font-size: .68rem !important;
    font-weight: 600 !important;
    letter-spacing: .09em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricDelta"] {
    font-size: .72rem !important;
    font-weight: 600 !important;
}

/* ── Tabs ── */
div[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #141416 !important;
    border: 1px solid #2A2A2F !important;
    border-radius: 10px !important;
    padding: 3px !important;
    gap: 3px !important;
}
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    border-radius: 7px !important;
    padding: 7px 18px !important;
    font-weight: 600 !important;
    font-size: .78rem !important;
    color: #5A5A65 !important;
    background: transparent !important;
    transition: color .15s !important;
}
div[data-testid="stTabs"] [aria-selected="true"] {
    background: #C8102E !important;
    color: #fff !important;
    box-shadow: 0 2px 10px rgba(200,16,46,.25) !important;
}

/* ── Inputs ── */
div[data-baseweb="input"] > div {
    background: #0C0C0E !important;
    border: 1px solid #2A2A2F !important;
    border-radius: 10px !important;
    color: #F5F5F7 !important;
}
div[data-baseweb="input"]:focus-within > div {
    border-color: #C8102E !important;
    box-shadow: 0 0 0 2px rgba(200,16,46,.12) !important;
}
div[data-baseweb="textarea"] > div {
    background: #0C0C0E !important;
    border: 1px solid #2A2A2F !important;
    border-radius: 10px !important;
    color: #F5F5F7 !important;
}
div[data-baseweb="textarea"]:focus-within > div {
    border-color: #C8102E !important;
}
.stTextInput label, .stSelectbox label, .stTextArea label {
    color: #5A5A65 !important;
    font-size: .68rem !important;
    font-weight: 600 !important;
    letter-spacing: .08em !important;
    text-transform: uppercase !important;
}

/* ── Selectbox ── */
div[data-baseweb="select"] > div {
    background: #0C0C0E !important;
    border: 1px solid #2A2A2F !important;
    border-radius: 10px !important;
    color: #F5F5F7 !important;
}
div[data-baseweb="select"]:focus-within > div {
    border-color: #C8102E !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #C8102E, #E8304A) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: .82rem !important;
    transition: opacity .2s, transform .15s !important;
}
.stButton > button:hover {
    opacity: .88 !important;
    transform: translateY(-1px) !important;
}
/* Ghost button (sair) */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: #C8102E !important;
    border: 1px solid #2A2A2F !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(200,16,46,.08) !important;
    border-color: #C8102E !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #2A2A2F !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] th {
    background: #141416 !important;
    color: #5A5A65 !important;
    font-size: .68rem !important;
    font-weight: 600 !important;
    letter-spacing: .08em !important;
    text-transform: uppercase !important;
}
[data-testid="stDataFrame"] td {
    color: #C8C8D0 !important;
    font-size: .82rem !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #C8102E !important; }

/* ── Info / warning boxes ── */
[data-testid="stInfo"] {
    background: #141416 !important;
    border: 1px solid #2A2A2F !important;
    border-radius: 10px !important;
    color: #A0A0A8 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: #2A2A2F; border-radius: 3px; }
* { scrollbar-width: thin; scrollbar-color: #2A2A2F transparent; }

/* ── HR ── */
hr { border-color: #2A2A2F !important; opacity: 1 !important; }

/* ── Form submit button (chat) ── */
.stForm [data-testid="stFormSubmitButton"] > button {
    background: #C8102E !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)