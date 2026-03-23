"""IA - IH · Chat estilo Gemini — Ital In House"""

import streamlit as st


def render_ia_css():
    st.markdown("""
<style>
.ia-area {
    max-width: 780px;
    margin: 0 auto;
    padding-bottom: 160px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

/* Usuário — direita */
.ia-user { display:flex; justify-content:flex-end; margin:8px 0 4px; }
.ia-user-bubble {
    background: #1E1E28;
    color: #F0F0F5;
    border-radius: 20px 20px 4px 20px;
    padding: 12px 18px;
    max-width: 72%;
    font-size: .9rem;
    line-height: 1.6;
    word-wrap: break-word;
    border: 1px solid #2A2A38;
}

/* IA — esquerda */
.ia-ai-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin: 4px 0 8px;
    max-width: 88%;
}
.ia-avatar {
    width: 32px; height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg,#4f8ef7,#a855f7);
    display: flex; align-items:center; justify-content:center;
    font-size: .8rem; font-weight: 800;
    flex-shrink: 0; margin-top: 2px; color: white;
    box-shadow: 0 2px 8px rgba(79,142,247,.25);
}
.ia-ai-bubble {
    background: #141418;
    border: 1px solid #2A2A35;
    border-radius: 4px 20px 20px 20px;
    padding: 14px 18px;
    color: #E0E0EC;
    font-size: .9rem;
    line-height: 1.75;
    flex: 1;
}
.ia-ai-bubble p      { margin:5px 0; }
.ia-ai-bubble ul,
.ia-ai-bubble ol     { margin:5px 0 5px 18px; }
.ia-ai-bubble li     { margin:3px 0; }
.ia-ai-bubble strong { color:#F5F5F7; font-weight:700; }
.ia-ai-bubble code {
    background:#1C1C22; border:1px solid #2A2A35;
    padding:2px 6px; border-radius:4px;
    font-size:.82rem; color:#7dd3a8; font-family:monospace;
}

/* Boas-vindas */
.ia-welcome {
    text-align:center; padding:48px 20px 28px;
    max-width:560px; margin:0 auto;
}
.ia-logo-glow {
    width:56px; height:56px; border-radius:50%;
    background:linear-gradient(135deg,#4f8ef7,#a855f7);
    display:flex; align-items:center; justify-content:center;
    font-size:1.4rem; margin:0 auto 16px; color:white;
    box-shadow:0 0 28px rgba(79,142,247,.3);
}
.ia-title {
    color:#F5F5F7; font-size:1.55rem; font-weight:800;
    letter-spacing:-.025em; margin-bottom:8px;
}
.ia-subtitle { color:#5A5A6A; font-size:.88rem; line-height:1.6; }

/* Footer fixo */
.ia-footer-wrap {
    position:fixed; bottom:0; left:0; right:0;
    background:linear-gradient(to top,#0C0C0E 72%,transparent);
    padding:24px 16px 16px; z-index:999;
}
.ia-input-card {
    max-width:780px; margin:0 auto;
    background:#141418; border:1px solid #2A2A35;
    border-radius:22px; padding:4px 8px 4px 16px;
    display:flex; align-items:flex-end; gap:8px;
    transition:border-color .2s, box-shadow .2s;
}
.ia-input-card:focus-within {
    border-color:rgba(79,142,247,.55);
    box-shadow:0 0 0 3px rgba(79,142,247,.07);
}

/* Botão enviar — gradiente circular */
div[data-testid="stFormSubmitButton"] > button {
    background:linear-gradient(135deg,#4f8ef7,#a855f7) !important;
    border:none !important;
    border-radius:50% !important;
    width:40px !important; height:40px !important;
    min-width:40px !important;
    padding:0 !important;
    font-size:1.1rem !important;
    line-height:1 !important;
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    transition:opacity .2s, transform .15s !important;
    box-shadow:0 3px 12px rgba(79,142,247,.4) !important;
    color:white !important;
    flex-shrink:0 !important;
    margin-bottom:4px !important;
}
div[data-testid="stFormSubmitButton"] > button:hover  { opacity:.88 !important; transform:scale(1.07) !important; }
div[data-testid="stFormSubmitButton"] > button:active { transform:scale(.94) !important; }

/* Textarea transparente */
div[data-testid="stForm"] div[data-baseweb="textarea"] {
    background:transparent !important;
    border:none !important;
    box-shadow:none !important;
}
div[data-testid="stForm"] div[data-baseweb="textarea"] textarea {
    background:transparent !important;
    color:#F0F0F5 !important;
    font-size:.9rem !important;
    resize:none !important;
    padding:10px 0 !important;
    line-height:1.5 !important;
}
div[data-testid="stForm"] div[data-baseweb="textarea"] textarea::placeholder { color:#383850 !important; }

/* Contador */
.ia-counter { font-size:.62rem; color:#28283A; text-align:right; padding:0 4px 4px 0; }
.ia-counter.warn { color:#F59E0B; }
.ia-counter.over { color:#EF4444; }

/* Loading dots */
@keyframes ia-pulse { 0%,80%,100%{opacity:.12;transform:scale(.75)} 40%{opacity:1;transform:scale(1)} }
.ia-loading { display:flex; align-items:center; gap:5px; padding:10px 0; }
.ia-dot { width:7px;height:7px;border-radius:50%;animation:ia-pulse 1.2s infinite ease-in-out; }
.ia-dot:nth-child(1){background:#4f8ef7;}
.ia-dot:nth-child(2){background:#8b5cf6;animation-delay:.2s;}
.ia-dot:nth-child(3){background:#a855f7;animation-delay:.4s;}
</style>
""", unsafe_allow_html=True)


def _user_msg(content: str):
    safe = content.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    st.markdown(f'<div class="ia-user"><div class="ia-user-bubble">{safe}</div></div>',
                unsafe_allow_html=True)


def _ai_msg(content: str):
    st.markdown('<div class="ia-ai-row"><div class="ia-avatar">✦</div><div class="ia-ai-bubble">',
                unsafe_allow_html=True)
    st.markdown(content)
    st.markdown("</div></div>", unsafe_allow_html=True)


def _welcome(nome: str, is_admin: bool):
    primeiro = nome.split()[0] if nome else "você"
    sub = ("Pergunte sobre vendas, produtos, lojas ou qualquer métrica da rede Ital In House."
           if is_admin else
           "Pergunte sobre suas vendas, produtos mais vendidos, clientes ou metas da sua unidade.")
    st.markdown(f"""
<div class="ia-welcome">
  <div class="ia-logo-glow">✦</div>
  <div class="ia-title">Olá, {primeiro}!</div>
  <div class="ia-subtitle">{sub}</div>
</div>""", unsafe_allow_html=True)


def render_ia_tab(user_dict: dict, loja_atual: dict):
    from ai_chat import build_context_ia, ia_stream

    render_ia_css()

    nome     = (user_dict.get("nome_completo")
                or user_dict.get("nome")
                or user_dict.get("username")
                or "Usuário")
    is_admin = (user_dict.get("role") or "").lower() == "admin"
    chat     = st.session_state.get("chat", [])

    # ── Histórico ──
    st.markdown('<div class="ia-area">', unsafe_allow_html=True)
    if not chat:
        _welcome(nome, is_admin)
    else:
        for msg in chat:
            if msg["role"] == "user":
                _user_msg(msg["content"])
            else:
                _ai_msg(msg["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Placeholder contextual (sem botões) ──
    loja_trade = (loja_atual or {}).get("trade_name", "")
    if is_admin and loja_trade in (None, "", "__admin__"):
        placeholder = "Ex: Qual loja faturou mais? · Top produtos da rede · Compare Loja A e B"
    else:
        placeholder = "Ex: Produtos mais vendidos · Estou batendo a meta? · Resumo de vendas do mês"

    # ── Input fixo ──
    st.markdown('<div class="ia-footer-wrap"><div class="ia-input-card">',
                unsafe_allow_html=True)

    with st.form("ia_form", clear_on_submit=True):
        col_txt, col_btn = st.columns([0.93, 0.07])
        with col_txt:
            pergunta = st.text_area(
                "", height=56, max_chars=1500,
                placeholder=placeholder,
                label_visibility="collapsed",
                key="ia_txt",
            )
            chars = len(pergunta) if pergunta else 0
            cls   = "over" if chars > 1400 else "warn" if chars > 1100 else ""
            if chars > 0:
                st.markdown(f'<div class="ia-counter {cls}">{chars}/1500</div>',
                            unsafe_allow_html=True)
        with col_btn:
            enviar = st.form_submit_button("➤", use_container_width=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── Envio com streaming ──
    if enviar and pergunta and pergunta.strip():
        q = pergunta.strip()
        st.session_state.chat = chat + [{"role": "user", "content": q}]

        ctx  = build_context_ia(user_dict, loja_atual)
        msgs = [{"role": m["role"], "content": m["content"]}
                for m in st.session_state.chat]

        # Renderiza conversa atualizada
        st.markdown('<div class="ia-area">', unsafe_allow_html=True)
        for msg in st.session_state.chat:
            if msg["role"] == "user":
                _user_msg(msg["content"])

        # Streaming ao vivo
        st.markdown('<div class="ia-ai-row"><div class="ia-avatar">✦</div>'
                    '<div class="ia-ai-bubble">', unsafe_allow_html=True)
        try:
            reply = st.write_stream(ia_stream(msgs, ctx))
        except Exception as e:
            reply = f"⚠️ Erro: {e}"
            st.error(reply)
        st.markdown("</div></div></div>", unsafe_allow_html=True)

        st.session_state.chat.append({"role": "assistant", "content": reply or ""})
        st.rerun()

    # ── Limpar ──
    if st.session_state.get("chat"):
        st.markdown("<br>" * 7, unsafe_allow_html=True)
        _, cc, _ = st.columns([0.41, 0.18, 0.41])
        with cc:
            if st.button("🗑️ Limpar conversa", key="ia_clear", use_container_width=True):
                st.session_state.chat = []
                st.rerun()
