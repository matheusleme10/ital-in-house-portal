"""IA - IH · Chat estilo Gemini — Ital In House"""

import streamlit as st


def render_ia_css():
    st.markdown("""
<style>
/* ── Área do chat ── */
.ia-area {
    max-width: 720px;
    margin: 0 auto;
    padding-bottom: 140px;
}

/* ── Mensagem usuário ── */
.ia-user {
    display: flex;
    justify-content: flex-end;
    margin: 10px 0;
}
.ia-user-bubble {
    background: #1C1C1F;
    color: #F5F5F7;
    border-radius: 18px 18px 4px 18px;
    padding: 11px 16px;
    max-width: 74%;
    font-size: .9rem;
    line-height: 1.55;
    word-wrap: break-word;
}

/* ── Mensagem IA ── */
.ia-ai {
    display: flex;
    gap: 12px;
    margin: 16px 0;
    align-items: flex-start;
}
.ia-ai-ico {
    font-size: .95rem;
    flex-shrink: 0;
    margin-top: 2px;
    background: linear-gradient(135deg, #4f8ef7, #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
}
.ia-ai-text {
    flex: 1;
    color: #E0E0E8;
    font-size: .9rem;
    line-height: 1.72;
}
.ia-ai-text p    { margin: 5px 0; }
.ia-ai-text ul,
.ia-ai-text ol   { margin: 5px 0 5px 16px; }
.ia-ai-text li   { margin: 3px 0; }
.ia-ai-text strong { color: #F5F5F7; font-weight: 700; }
.ia-ai-text code {
    background: #1C1C1F;
    border: 1px solid #2A2A2F;
    padding: 1px 5px;
    border-radius: 4px;
    font-size: .82rem;
    color: #7dd3a8;
}
.ia-sep { height: 1px; background: #1C1C1F; margin: 4px 0 4px 34px; }

/* ── Boas-vindas ── */
.ia-welcome {
    text-align: center;
    padding: 40px 16px 28px;
    max-width: 720px;
    margin: 0 auto;
}
.ia-ico-big {
    font-size: 2rem;
    background: linear-gradient(135deg, #4f8ef7, #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: block;
    margin-bottom: 12px;
}
.ia-title {
    color: #F5F5F7;
    font-size: 1.55rem;
    font-weight: 800;
    letter-spacing: -.02em;
    margin-bottom: 4px;
}
.ia-subtitle {
    color: #5A5A65;
    font-size: .88rem;
    margin-bottom: 28px;
}

/* ── Chips de sugestão ── */
.ia-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin-bottom: 8px;
}
.ia-chip {
    background: #141416;
    border: 1px solid #2A2A2F;
    border-radius: 99px;
    padding: 7px 16px;
    font-size: .78rem;
    color: #A0A0A8;
    cursor: pointer;
    transition: border-color .15s, color .15s;
}
.ia-chip:hover { border-color: #C8102E; color: #F5F5F7; }

/* ── Footer do chat ── */
.ia-footer {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: linear-gradient(to top, #0C0C0E 75%, transparent);
    padding: 20px 16px 14px;
    z-index: 999;
}
.ia-input-box {
    max-width: 720px;
    margin: 0 auto;
    background: #141416;
    border: 1px solid #2A2A2F;
    border-radius: 16px;
    padding: 10px 14px;
    transition: border-color .2s;
}
.ia-input-box:focus-within {
    border-color: #C8102E;
    box-shadow: 0 0 0 2px rgba(200,16,46,.1);
}
.ia-counter {
    font-size: .65rem;
    text-align: right;
    margin-top: 2px;
    color: #3A3A45;
}
.ia-counter.warn  { color: #F59E0B; }
.ia-counter.over  { color: #EF4444; }

/* ── Loading ── */
@keyframes ia-blink { 0%,100%{opacity:1} 50%{opacity:.15} }
.ia-loading { display:flex; gap:5px; align-items:center; padding: 6px 0 6px 34px; }
.ia-dot {
    width:7px; height:7px; border-radius:50%;
    background:#C8102E;
    animation: ia-blink 1.1s infinite;
}
.ia-dot:nth-child(2){animation-delay:.18s}
.ia-dot:nth-child(3){animation-delay:.36s}
</style>
""", unsafe_allow_html=True)


def _user_msg(content: str):
    st.markdown(f"""
<div class="ia-user">
  <div class="ia-user-bubble">{content}</div>
</div>""", unsafe_allow_html=True)


def _ai_msg(content: str):
    st.markdown('<div class="ia-ai"><div class="ia-ai-ico">✦</div><div class="ia-ai-text">',
                unsafe_allow_html=True)
    st.markdown(content)
    st.markdown("</div></div><div class='ia-sep'></div>", unsafe_allow_html=True)


def _welcome(nome: str):
    primeiro = nome.split()[0] if nome else "você"
    st.markdown(f"""
<div class="ia-welcome">
  <span class="ia-ico-big">✦</span>
  <div class="ia-title">Olá, {primeiro}!</div>
  <div class="ia-subtitle">Pergunte sobre vendas, produtos, clientes ou qualquer loja da rede.</div>
  <div class="ia-chips" id="chips">
    <span class="ia-chip" id="c1">💰 Vendas deste mês</span>
    <span class="ia-chip" id="c2">🏆 Produto mais vendido</span>
    <span class="ia-chip" id="c3">📊 Resumo da rede</span>
    <span class="ia-chip" id="c4">🎯 Estou batendo a meta?</span>
    <span class="ia-chip" id="c5">👥 Clientes novos</span>
  </div>
</div>""", unsafe_allow_html=True)

    # Botões invisíveis mapeados para as chips via JS
    chip_perguntas = {
        "c1": "Como foram as vendas deste mês?",
        "c2": "Qual foi o produto mais vendido?",
        "c3": "Me dê um resumo geral da rede.",
        "c4": "Estou batendo a meta este mês?",
        "c5": "Quantos clientes novos tive recentemente?",
    }

    cols = st.columns(len(chip_perguntas))
    for col, (_, pergunta) in zip(cols, chip_perguntas.items()):
        with col:
            if st.button(pergunta, key=f"chip_{pergunta}", use_container_width=True,
                        help=pergunta):
                st.session_state["_ia_sugestao"] = pergunta
                st.rerun()

    # CSS para esconder os botões nativos e deixar só as chips visuais
    st.markdown("""
<style>
div[data-testid="column"] > div > div > div > button {
    position: absolute !important;
    opacity: 0 !important;
    pointer-events: none !important;
    height: 0 !important;
    overflow: hidden !important;
}
</style>
<script>
var chips = document.querySelectorAll('.ia-chip');
var btns  = document.querySelectorAll('div[data-testid="column"] > div > div > div > button');
chips.forEach(function(chip, i) {
    chip.addEventListener('click', function() {
        if (btns[i]) btns[i].click();
    });
});
</script>
""", unsafe_allow_html=True)


def render_ia_tab(user_dict: dict, loja_atual: dict):
    """Renderiza a aba IA - IH."""
    from ai_chat import build_context_ia, ia_responder

    render_ia_css()

    nome = user_dict.get("nome_completo") or user_dict.get("username") or "Usuário"

    # ── Processa sugestão clicada ──
    if "_ia_sugestao" in st.session_state:
        pergunta = st.session_state.pop("_ia_sugestao")
        _processar_pergunta(pergunta, user_dict, loja_atual, ia_responder, build_context_ia)
        return  # rerun já foi chamado dentro

    # ── Histórico ──
    st.markdown('<div class="ia-area">', unsafe_allow_html=True)

    if not st.session_state.get("chat"):
        _welcome(nome)
    else:
        for msg in st.session_state.chat:
            if msg["role"] == "user":
                _user_msg(msg["content"])
            else:
                _ai_msg(msg["content"])

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Input fixo ──
    st.markdown('<div class="ia-footer"><div class="ia-input-box">',
                unsafe_allow_html=True)

    with st.form("ia_chat_form", clear_on_submit=True):
        col_txt, col_btn = st.columns([0.91, 0.09])
        with col_txt:
            pergunta = st.text_area(
                "",
                height=52,
                max_chars=1500,
                placeholder="Pergunte sobre vendas, produtos, clientes ou qualquer loja...",
                label_visibility="collapsed",
                key="ia_input_txt",
            )
            chars = len(pergunta) if pergunta else 0
            cls   = "over" if chars > 1400 else "warn" if chars > 1100 else ""
            st.markdown(
                f'<div class="ia-counter {cls}">{chars} / 1500</div>',
                unsafe_allow_html=True,
            )
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            enviar = st.form_submit_button("↗️", use_container_width=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    if enviar and pergunta and pergunta.strip():
        _processar_pergunta(
            pergunta.strip(), user_dict, loja_atual, ia_responder, build_context_ia
        )

    # ── Limpar ──
    if st.session_state.get("chat"):
        st.markdown("<br>" * 5, unsafe_allow_html=True)
        c, _ = st.columns([0.16, 0.84])
        with c:
            if st.button("🗑️ Limpar", use_container_width=True, key="ia_clear_btn"):
                st.session_state.chat = []
                st.rerun()


def _processar_pergunta(pergunta, user_dict, loja_atual, ia_responder, build_context_ia):
    """Processa uma pergunta e salva a resposta no histórico."""
    ctx = build_context_ia(user_dict, loja_atual)
    st.session_state.chat.append({"role": "user", "content": pergunta})
    msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat]

    with st.spinner("IA - IH pensando..."):
        try:
            reply = ia_responder(msgs, ctx)
        except Exception as e:
            reply = f"⚠️ Erro ao conectar com a IA: {e}"

    st.session_state.chat.append({"role": "assistant", "content": reply})
    st.rerun()