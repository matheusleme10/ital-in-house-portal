"""Gerenciamento de usuários — Ital In House · Apenas admin."""

import hashlib

import streamlit as st

from db import fetch_all, fetch_one
from theme import inject_global_css


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _hash(senha: str) -> str:
    return hashlib.sha256(senha.strip().encode()).hexdigest()


def _label(txt: str):
    st.markdown(
        f"<div style='color:#5A5A65;font-size:.65rem;font-weight:600;"
        f"letter-spacing:.09em;text-transform:uppercase;margin-bottom:4px'>{txt}</div>",
        unsafe_allow_html=True,
    )


def _secao(titulo: str, icone: str = ""):
    st.markdown(
        f"<div style='color:#F5F5F7;font-size:.95rem;font-weight:800;"
        f"letter-spacing:-.01em;margin:24px 0 14px'>{icone} {titulo}</div>",
        unsafe_allow_html=True,
    )


def _card_usuario(u: dict, lojas_map: dict):
    """Renderiza um card de usuário na listagem."""
    uid       = u.get("id")
    nome      = u.get("nome_completo") or u.get("username") or "—"
    username  = u.get("username") or "—"
    email     = u.get("email") or "—"
    role      = (u.get("role") or "franqueado").lower()
    ids_uni   = list(u.get("id_unidades") or [])
    nomes_uni = [lojas_map.get(i, f"ID {i}") for i in ids_uni] if ids_uni else []

    cor_role  = "#C8102E" if role == "admin" else "#4f6ef7"
    bg_role   = "rgba(200,16,46,.12)" if role == "admin" else "rgba(79,110,247,.12)"
    iniciais  = "".join(p[0].upper() for p in nome.split()[:2]) or "?"

    lojas_html = ""
    if nomes_uni:
        pills = "".join(
            f"<span style='background:#1C1C1F;border:1px solid #2A2A2F;"
            f"border-radius:99px;padding:2px 10px;font-size:.62rem;color:#A0A0A8;"
            f"margin:2px'>{n}</span>"
            for n in nomes_uni
        )
        lojas_html = f"<div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:4px'>{pills}</div>"
    elif role != "admin":
        lojas_html = (
            "<div style='margin-top:8px;color:#EF4444;font-size:.65rem'>"
            "⚠️ Nenhuma loja vinculada</div>"
        )

    st.markdown(f"""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:14px;
            padding:16px 20px;margin-bottom:10px;
            transition:border-color .2s' id='user_{uid}'>
  <div style='display:flex;align-items:center;gap:14px'>
    <div style='width:40px;height:40px;border-radius:50%;background:#C8102E;
                display:flex;align-items:center;justify-content:center;
                color:white;font-size:.78rem;font-weight:800;flex-shrink:0'>
      {iniciais}
    </div>
    <div style='flex:1;min-width:0'>
      <div style='display:flex;align-items:center;gap:8px;margin-bottom:2px'>
        <span style='color:#F5F5F7;font-size:.88rem;font-weight:700'>{nome}</span>
        <span style='background:{bg_role};color:{cor_role};font-size:.6rem;
                     font-weight:700;padding:2px 8px;border-radius:99px;
                     letter-spacing:.06em;text-transform:uppercase'>{role}</span>
      </div>
      <div style='color:#5A5A65;font-size:.72rem'>
        @{username} · {email}
      </div>
      {lojas_html}
    </div>
    <div style='color:#5A5A65;font-size:.68rem;flex-shrink:0'>ID #{uid}</div>
  </div>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  QUERIES
# ─────────────────────────────────────────────

def _listar_usuarios() -> list:
    try:
        rows = fetch_all("""
            SELECT id, username, email, role, nome_completo, id_unidades
            FROM cardapio_cmv.usuarios_portal
            ORDER BY role DESC, nome_completo ASC
        """)
        return [dict(r) for r in rows] if rows else []
    except Exception as e:
        st.error(f"Erro ao listar usuários: {e}")
        return []


def _listar_lojas() -> list:
    try:
        rows = fetch_all("""
            SELECT id, trade_name, short_desc_state
            FROM cardapio_cmv.unidade_uf
            ORDER BY trade_name
        """)
        return [dict(r) for r in rows] if rows else []
    except Exception as e:
        return []


def _criar_usuario(username: str, nome: str, email: str,
                   senha: str, role: str, ids_lojas: list) -> tuple[bool, str]:
    """Cria usuário e retorna (sucesso, mensagem)."""
    try:
        # Verifica duplicidade
        exist = fetch_one(
            """
            SELECT id FROM cardapio_cmv.usuarios_portal
            WHERE LOWER(TRIM(email)) = LOWER(TRIM(%s))
               OR LOWER(TRIM(username)) = LOWER(TRIM(%s))
            """,
            (email, username),
        )
        if exist:
            return False, "Já existe um usuário com esse e-mail ou username."

        pw_hash  = _hash(senha)
        ids_arr  = ids_lojas if ids_lojas else []

        from db import execute
        execute(
            """
            INSERT INTO cardapio_cmv.usuarios_portal
                (username, nome_completo, email, password_hash, role, id_unidades)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (username.strip(), nome.strip(), email.strip().lower(),
             pw_hash, role, ids_arr),
        )
        return True, f"Usuário **{nome}** criado com sucesso!"
    except Exception as e:
        return False, f"Erro ao criar usuário: {e}"


def _alterar_senha(user_id: int, nova_senha: str) -> tuple[bool, str]:
    try:
        from db import execute
        execute(
            """
            UPDATE cardapio_cmv.usuarios_portal
            SET password_hash = %s WHERE id = %s
            """,
            (_hash(nova_senha), user_id),
        )
        return True, "Senha alterada com sucesso!"
    except Exception as e:
        return False, f"Erro ao alterar senha: {e}"


def _atualizar_lojas(user_id: int, ids_lojas: list) -> tuple[bool, str]:
    try:
        from db import execute
        execute(
            """
            UPDATE cardapio_cmv.usuarios_portal
            SET id_unidades = %s WHERE id = %s
            """,
            (ids_lojas, user_id),
        )
        return True, "Lojas atualizadas com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar lojas: {e}"


def _deletar_usuario(user_id: int) -> tuple[bool, str]:
    try:
        from db import execute
        execute(
            "DELETE FROM cardapio_cmv.usuarios_portal WHERE id = %s",
            (user_id,),
        )
        return True, "Usuário removido."
    except Exception as e:
        return False, f"Erro ao remover: {e}"


# ─────────────────────────────────────────────
#  PÁGINA PRINCIPAL
# ─────────────────────────────────────────────

def render_gerenciar_usuarios():
    """
    Página completa de gerenciamento de usuários.
    Chamar dentro de uma aba do painel admin.
    """
    inject_global_css()

    lojas     = _listar_lojas()
    lojas_map = {l["id"]: l["trade_name"] for l in lojas}
    nomes_loja = [l["trade_name"] for l in lojas]

    # ── CSS extra para esta página ──
    st.markdown("""
<style>
div[data-testid="stForm"] {
    background: #141416 !important;
    border: 1px solid #2A2A2F !important;
    border-radius: 16px !important;
    padding: 24px !important;
}
div[data-testid="stForm"] label {
    color: #5A5A65 !important;
    font-size: .65rem !important;
    font-weight: 600 !important;
    letter-spacing: .09em !important;
    text-transform: uppercase !important;
}
</style>
""", unsafe_allow_html=True)

    # ── Header ──
    st.markdown("""
<div style='display:flex;align-items:center;gap:12px;margin-bottom:20px'>
  <div style='width:44px;height:44px;border-radius:12px;
              background:linear-gradient(135deg,#C8102E,#E8304A);
              display:flex;align-items:center;justify-content:center;
              font-size:1.2rem;flex-shrink:0'>👥</div>
  <div>
    <div style='color:#5A5A65;font-size:.62rem;font-weight:600;
                letter-spacing:.1em;text-transform:uppercase'>Administração</div>
    <div style='color:#F5F5F7;font-size:1.2rem;font-weight:800;
                letter-spacing:-.02em'>Gerenciar Usuários</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Tabs internas ──
    tab_criar, tab_listar, tab_editar = st.tabs([
        "➕  Novo Usuário",
        "📋  Listar Usuários",
        "✏️  Editar / Excluir",
    ])

    # ══════════════════════════════════════
    #  TAB 1 — CRIAR USUÁRIO
    # ══════════════════════════════════════
    with tab_criar:
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("form_criar_usuario", clear_on_submit=True):
            st.markdown("""
<div style='color:#F5F5F7;font-size:.88rem;font-weight:700;margin-bottom:16px'>
  Dados do novo usuário
</div>""", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                novo_nome     = st.text_input("Nome completo",
                                              placeholder="Ex: João da Silva")
                novo_email    = st.text_input("E-mail",
                                              placeholder="joao@italinhouse.com")
                novo_role     = st.selectbox("Perfil", ["franqueado", "admin"])
            with c2:
                novo_username = st.text_input("Username",
                                              placeholder="joaosilva")
                nova_senha    = st.text_input("Senha", type="password",
                                              placeholder="Mínimo 6 caracteres")
                confirma_senha = st.text_input("Confirmar senha", type="password",
                                               placeholder="Repita a senha")

            # Seleção de lojas (só para franqueado)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
<div style='color:#5A5A65;font-size:.65rem;font-weight:600;
            letter-spacing:.09em;text-transform:uppercase;margin-bottom:4px'>
  Lojas vinculadas (apenas para franqueado)
</div>""", unsafe_allow_html=True)

            lojas_selecionadas = st.multiselect(
                "",
                options=nomes_loja,
                placeholder="Selecione as lojas do franqueado...",
                label_visibility="collapsed",
            )

            st.markdown("<br>", unsafe_allow_html=True)
            criar = st.form_submit_button("✅ Criar Usuário",
                                          use_container_width=True)

        if criar:
            # Validações
            erros = []
            if not novo_nome.strip():
                erros.append("Nome completo é obrigatório.")
            if not novo_username.strip():
                erros.append("Username é obrigatório.")
            if not novo_email.strip() or "@" not in novo_email:
                erros.append("E-mail inválido.")
            if len(nova_senha) < 6:
                erros.append("Senha deve ter pelo menos 6 caracteres.")
            if nova_senha != confirma_senha:
                erros.append("As senhas não coincidem.")

            if erros:
                for e in erros:
                    st.error(e)
            else:
                ids_lojas = [
                    l["id"] for l in lojas
                    if l["trade_name"] in lojas_selecionadas
                ]
                ok, msg = _criar_usuario(
                    novo_username, novo_nome, novo_email,
                    nova_senha, novo_role, ids_lojas,
                )
                if ok:
                    st.success(msg)
                    st.balloons()
                else:
                    st.error(msg)

    # ══════════════════════════════════════
    #  TAB 2 — LISTAR USUÁRIOS
    # ══════════════════════════════════════
    with tab_listar:
        st.markdown("<br>", unsafe_allow_html=True)

        usuarios = _listar_usuarios()

        if not usuarios:
            st.info("Nenhum usuário cadastrado.")
        else:
            # Filtros
            fc1, fc2, _ = st.columns([1, 1, 2])
            with fc1:
                filtro_role = st.selectbox("Filtrar por perfil",
                                           ["Todos", "admin", "franqueado"],
                                           key="filtro_role")
            with fc2:
                filtro_busca = st.text_input("Buscar por nome ou e-mail",
                                             placeholder="Digite para buscar...",
                                             key="filtro_busca")

            st.markdown("<br>", unsafe_allow_html=True)

            # Aplica filtros
            lista = usuarios
            if filtro_role != "Todos":
                lista = [u for u in lista
                         if (u.get("role") or "").lower() == filtro_role]
            if filtro_busca:
                t = filtro_busca.lower()
                lista = [u for u in lista if
                         t in (u.get("nome_completo") or "").lower() or
                         t in (u.get("email") or "").lower() or
                         t in (u.get("username") or "").lower()]

            # Contadores
            n_admin = sum(1 for u in usuarios
                          if (u.get("role") or "").lower() == "admin")
            n_franc = sum(1 for u in usuarios
                          if (u.get("role") or "").lower() == "franqueado")

            m1, m2, m3 = st.columns(3)
            m1.metric("Total", len(usuarios))
            m2.metric("Admins", n_admin)
            m3.metric("Franqueados", n_franc)

            st.markdown("<br>", unsafe_allow_html=True)

            if lista:
                for u in lista:
                    _card_usuario(u, lojas_map)
            else:
                st.info("Nenhum usuário encontrado com esses filtros.")

    # ══════════════════════════════════════
    #  TAB 3 — EDITAR / EXCLUIR
    # ══════════════════════════════════════
    with tab_editar:
        st.markdown("<br>", unsafe_allow_html=True)

        usuarios = _listar_usuarios()
        if not usuarios:
            st.info("Nenhum usuário cadastrado.")
            return

        opcoes = {
            f"#{u['id']} — {u.get('nome_completo') or u.get('username')} ({u.get('role')})": u
            for u in usuarios
        }
        escolhido_label = st.selectbox("Selecione o usuário",
                                       list(opcoes.keys()),
                                       key="edit_user_sel")
        u_edit = opcoes[escolhido_label]

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Alterar senha ──
        st.markdown("""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:14px;
            padding:20px 24px;margin-bottom:16px'>
  <div style='color:#F5F5F7;font-size:.85rem;font-weight:700;margin-bottom:14px'>
    🔑 Alterar senha
  </div>
""", unsafe_allow_html=True)

        with st.form("form_senha", clear_on_submit=True):
            s1, s2 = st.columns(2)
            with s1:
                nova_s = st.text_input("Nova senha", type="password",
                                       placeholder="Mínimo 6 caracteres")
            with s2:
                conf_s = st.text_input("Confirmar nova senha", type="password",
                                       placeholder="Repita a senha")
            salvar_senha = st.form_submit_button("💾 Salvar senha",
                                                  use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        if salvar_senha:
            if len(nova_s) < 6:
                st.error("Senha deve ter pelo menos 6 caracteres.")
            elif nova_s != conf_s:
                st.error("As senhas não coincidem.")
            else:
                ok, msg = _alterar_senha(u_edit["id"], nova_s)
                st.success(msg) if ok else st.error(msg)

        # ── Gerenciar lojas ──
        st.markdown("""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:14px;
            padding:20px 24px;margin-bottom:16px'>
  <div style='color:#F5F5F7;font-size:.85rem;font-weight:700;margin-bottom:14px'>
    🏪 Lojas vinculadas
  </div>
""", unsafe_allow_html=True)

        ids_atuais    = list(u_edit.get("id_unidades") or [])
        nomes_atuais  = [lojas_map.get(i, f"ID {i}") for i in ids_atuais]

        with st.form("form_lojas", clear_on_submit=False):
            novas_lojas = st.multiselect(
                "Selecione as lojas",
                options=nomes_loja,
                default=nomes_atuais,
                label_visibility="collapsed",
            )
            salvar_lojas = st.form_submit_button("💾 Salvar lojas",
                                                  use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        if salvar_lojas:
            ids_novos = [l["id"] for l in lojas
                         if l["trade_name"] in novas_lojas]
            ok, msg = _atualizar_lojas(u_edit["id"], ids_novos)
            st.success(msg) if ok else st.error(msg)

        # ── Excluir ──
        st.markdown("""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:14px;
            padding:20px 24px;border-color:#3A1A1A'>
  <div style='color:#EF4444;font-size:.85rem;font-weight:700;margin-bottom:8px'>
    🗑️ Zona de perigo
  </div>
  <div style='color:#5A5A65;font-size:.78rem;margin-bottom:14px'>
    Esta ação é irreversível. O usuário será removido permanentemente.
  </div>
""", unsafe_allow_html=True)

        confirma_del = st.checkbox(
            f"Confirmo que quero excluir o usuário **{u_edit.get('nome_completo') or u_edit.get('username')}**",
            key="confirma_del",
        )
        if st.button("🗑️ Excluir usuário", disabled=not confirma_del,
                     key="btn_deletar", use_container_width=True):
            # Não permite excluir a si mesmo
            if u_edit["id"] == st.session_state.user.get("id"):
                st.error("Você não pode excluir sua própria conta.")
            else:
                ok, msg = _deletar_usuario(u_edit["id"])
                st.success(msg) if ok else st.error(msg)
                if ok:
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
