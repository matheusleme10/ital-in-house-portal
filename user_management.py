"""Gerenciamento de usuários — Ital In House · Apenas admin."""

import hashlib

import streamlit as st

from db import fetch_all, fetch_one


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _hash(senha: str) -> str:
    return hashlib.sha256(senha.strip().encode()).hexdigest()


def _card_usuario(u: dict, lojas_map: dict):
    uid      = u.get("id")
    nome     = u.get("nome_completo") or u.get("username") or "—"
    username = u.get("username") or "—"
    email    = u.get("email") or "—"
    role     = (u.get("role") or "franqueado").lower()
    ids_uni  = list(u.get("id_unidades") or [])
    nomes_uni = [lojas_map.get(i, f"ID {i}") for i in ids_uni] if ids_uni else []

    cor_role = "#C8102E" if role == "admin" else "#4f6ef7"
    bg_role  = "rgba(200,16,46,.12)" if role == "admin" else "rgba(79,110,247,.12)"
    iniciais = "".join(p[0].upper() for p in nome.split()[:2]) or "?"

    if nomes_uni:
        pills = "".join(
            f"<span style='background:#1C1C1F;border:1px solid #2A2A2F;"
            f"border-radius:99px;padding:2px 10px;font-size:.62rem;"
            f"color:#A0A0A8;margin:2px;display:inline-block'>{n}</span>"
            for n in nomes_uni
        )
        lojas_html = f"<div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:4px'>{pills}</div>"
    elif role != "admin":
        lojas_html = "<div style='margin-top:8px;color:#EF4444;font-size:.65rem'>⚠️ Nenhuma loja vinculada</div>"
    else:
        lojas_html = ""

    st.markdown(f"""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:14px;
            padding:14px 18px;margin-bottom:8px'>
  <div style='display:flex;align-items:center;gap:14px'>
    <div style='width:38px;height:38px;border-radius:50%;background:#C8102E;
                display:flex;align-items:center;justify-content:center;
                color:white;font-size:.72rem;font-weight:800;flex-shrink:0'>{iniciais}</div>
    <div style='flex:1;min-width:0'>
      <div style='display:flex;align-items:center;gap:8px;margin-bottom:3px'>
        <span style='color:#F5F5F7;font-size:.88rem;font-weight:700'>{nome}</span>
        <span style='background:{bg_role};color:{cor_role};font-size:.6rem;
                     font-weight:700;padding:2px 8px;border-radius:99px;
                     letter-spacing:.06em;text-transform:uppercase'>{role}</span>
      </div>
      <div style='color:#5A5A65;font-size:.72rem'>@{username} · {email}</div>
      {lojas_html}
    </div>
    <div style='color:#3A3A45;font-size:.65rem;flex-shrink:0'>ID #{uid}</div>
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
    except Exception:
        return []


def _criar_usuario(username, nome, email, senha, role, ids_lojas) -> tuple[bool, str]:
    try:
        exist = fetch_one("""
            SELECT id FROM cardapio_cmv.usuarios_portal
            WHERE LOWER(TRIM(email)) = LOWER(TRIM(%s))
               OR LOWER(TRIM(username)) = LOWER(TRIM(%s))
        """, (email, username))
        if exist:
            return False, "Já existe usuário com esse e-mail ou username."

        from db import execute
        execute("""
            INSERT INTO cardapio_cmv.usuarios_portal
                (username, nome_completo, email, password_hash, role, id_unidades)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (username.strip(), nome.strip(), email.strip().lower(),
              _hash(senha), role, ids_lojas or []))
        return True, f"Usuário **{nome}** criado com sucesso!"
    except Exception as e:
        return False, f"Erro ao criar: {e}"


def _alterar_senha(user_id: int, nova: str) -> tuple[bool, str]:
    try:
        from db import execute
        execute("UPDATE cardapio_cmv.usuarios_portal SET password_hash = %s WHERE id = %s",
                (_hash(nova), user_id))
        return True, "Senha alterada com sucesso!"
    except Exception as e:
        return False, f"Erro: {e}"


def _atualizar_lojas(user_id: int, ids: list) -> tuple[bool, str]:
    try:
        from db import execute
        execute("UPDATE cardapio_cmv.usuarios_portal SET id_unidades = %s WHERE id = %s",
                (ids, user_id))
        return True, "Lojas atualizadas com sucesso!"
    except Exception as e:
        return False, f"Erro: {e}"


def _deletar_usuario(user_id: int) -> tuple[bool, str]:
    try:
        from db import execute
        execute("DELETE FROM cardapio_cmv.usuarios_portal WHERE id = %s", (user_id,))
        return True, "Usuário removido."
    except Exception as e:
        return False, f"Erro: {e}"


# ─────────────────────────────────────────────
#  PÁGINA PRINCIPAL
# ─────────────────────────────────────────────

def render_gerenciar_usuarios():
    lojas     = _listar_lojas()
    lojas_map = {l["id"]: l["trade_name"] for l in lojas}
    nomes_loja = [l["trade_name"] for l in lojas]

    st.markdown("""
<style>
div[data-testid="stForm"] {
    background: #141416 !important;
    border: 1px solid #2A2A2F !important;
    border-radius: 16px !important;
    padding: 24px !important;
}
</style>
<div style='display:flex;align-items:center;gap:12px;margin-bottom:20px'>
  <div style='width:42px;height:42px;border-radius:12px;
              background:linear-gradient(135deg,#C8102E,#E8304A);
              display:flex;align-items:center;justify-content:center;
              font-size:1.1rem;flex-shrink:0'>👥</div>
  <div>
    <div style='color:#5A5A65;font-size:.6rem;font-weight:600;
                letter-spacing:.1em;text-transform:uppercase'>Administração</div>
    <div style='color:#F5F5F7;font-size:1.15rem;font-weight:800;
                letter-spacing:-.02em'>Gerenciar Usuários</div>
  </div>
</div>
""", unsafe_allow_html=True)

    tab_criar, tab_listar, tab_editar = st.tabs([
        "➕  Novo Usuário",
        "📋  Listar",
        "✏️  Editar / Excluir",
    ])

    # ══════════════════════════════════════
    #  TAB 1 — CRIAR
    # ══════════════════════════════════════
    with tab_criar:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("form_criar", clear_on_submit=True):
            st.markdown("<div style='color:#F5F5F7;font-size:.88rem;font-weight:700;margin-bottom:14px'>Dados do novo usuário</div>",
                        unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                novo_nome     = st.text_input("Nome completo", placeholder="Ex: João da Silva")
                novo_email    = st.text_input("E-mail",        placeholder="joao@italinhouse.com")
                novo_role     = st.selectbox("Perfil", ["franqueado", "admin"])
            with c2:
                novo_username  = st.text_input("Username",         placeholder="joaosilva")
                nova_senha     = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres")
                confirma_senha = st.text_input("Confirmar senha", type="password", placeholder="Repita a senha")

            st.markdown("<div style='color:#5A5A65;font-size:.62rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin:12px 0 4px'>Lojas vinculadas (apenas franqueado)</div>",
                        unsafe_allow_html=True)
            lojas_sel = st.multiselect("", options=nomes_loja,
                                       placeholder="Selecione as lojas...",
                                       label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            criar = st.form_submit_button("✅ Criar Usuário", use_container_width=True)

        if criar:
            erros = []
            if not novo_nome.strip():    erros.append("Nome completo é obrigatório.")
            if not novo_username.strip():erros.append("Username é obrigatório.")
            if not novo_email.strip() or "@" not in novo_email: erros.append("E-mail inválido.")
            if len(nova_senha) < 6:     erros.append("Senha mínima de 6 caracteres.")
            if nova_senha != confirma_senha: erros.append("As senhas não coincidem.")

            if erros:
                for e in erros:
                    st.error(e)
            else:
                ids = [l["id"] for l in lojas if l["trade_name"] in lojas_sel]
                ok, msg = _criar_usuario(novo_username, novo_nome, novo_email,
                                         nova_senha, novo_role, ids)
                if ok:
                    st.success(msg)
                    st.balloons()
                else:
                    st.error(msg)

    # ══════════════════════════════════════
    #  TAB 2 — LISTAR
    # ══════════════════════════════════════
    with tab_listar:
        st.markdown("<br>", unsafe_allow_html=True)
        usuarios = _listar_usuarios()

        if not usuarios:
            st.info("Nenhum usuário cadastrado.")
        else:
            fc1, fc2 = st.columns([1, 2])
            with fc1:
                filtro_role = st.selectbox("Perfil", ["Todos", "admin", "franqueado"],
                                           key="filtro_role_lst")
            with fc2:
                filtro_busca = st.text_input("Buscar por nome, e-mail ou username",
                                             placeholder="🔍  Digite para filtrar...",
                                             key="filtro_busca_lst")

            st.markdown("<br>", unsafe_allow_html=True)

            # Métricas
            n_adm  = sum(1 for u in usuarios if (u.get("role") or "").lower() == "admin")
            n_franc = sum(1 for u in usuarios if (u.get("role") or "").lower() == "franqueado")
            m1, m2, m3 = st.columns(3)
            m1.metric("Total",       len(usuarios))
            m2.metric("Admins",      n_adm)
            m3.metric("Franqueados", n_franc)
            st.markdown("<br>", unsafe_allow_html=True)

            # Filtra
            lista = usuarios
            if filtro_role != "Todos":
                lista = [u for u in lista if (u.get("role") or "").lower() == filtro_role]
            if filtro_busca:
                t = filtro_busca.lower()
                lista = [u for u in lista if
                         t in (u.get("nome_completo") or "").lower() or
                         t in (u.get("email") or "").lower() or
                         t in (u.get("username") or "").lower()]

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

        # ── BUSCA em vez de selectbox ──────────────────────
        st.markdown("""
<div style='color:#5A5A65;font-size:.62rem;font-weight:600;
            letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px'>
  Buscar usuário para editar
</div>""", unsafe_allow_html=True)

        busca_edit = st.text_input("",
                                   placeholder="🔍  Nome, username ou e-mail...",
                                   key="busca_edit_usr",
                                   label_visibility="collapsed")

        lista_edit = usuarios
        if busca_edit:
            t = busca_edit.lower()
            lista_edit = [u for u in usuarios if
                          t in (u.get("nome_completo") or "").lower() or
                          t in (u.get("username") or "").lower() or
                          t in (u.get("email") or "").lower()]

        if not lista_edit:
            st.info("Nenhum usuário encontrado para esse termo.")
            return

        # Selectbox apenas com os resultados filtrados
        opcoes = {
            f"#{u['id']} — {u.get('nome_completo') or u.get('username')} ({u.get('role')})": u
            for u in lista_edit[:50]  # limita 50 para não travar
        }
        escolhido = st.selectbox("Selecione", list(opcoes.keys()),
                                 key="edit_user_sel_v2",
                                 label_visibility="collapsed")
        u_edit = opcoes[escolhido]

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Info do usuário selecionado ──
        nome_edit = u_edit.get("nome_completo") or u_edit.get("username") or "—"
        st.markdown(f"""
<div style='background:#1C1C1F;border:1px solid #2A2A2F;border-radius:12px;
            padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;gap:12px'>
  <div style='width:36px;height:36px;border-radius:50%;background:#C8102E;
              display:flex;align-items:center;justify-content:center;
              color:white;font-size:.7rem;font-weight:800;flex-shrink:0'>
    {"".join(p[0].upper() for p in nome_edit.split()[:2]) or "?"}
  </div>
  <div>
    <div style='color:#F5F5F7;font-size:.85rem;font-weight:700'>{nome_edit}</div>
    <div style='color:#5A5A65;font-size:.7rem'>{u_edit.get("email","—")} · ID #{u_edit.get("id")}</div>
  </div>
</div>""", unsafe_allow_html=True)

        # ── Alterar senha ──
        st.markdown("""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:14px;padding:18px 22px;margin-bottom:14px'>
  <div style='color:#F5F5F7;font-size:.85rem;font-weight:700;margin-bottom:12px'>🔑 Alterar senha</div>
""", unsafe_allow_html=True)

        with st.form("form_senha_v2", clear_on_submit=True):
            s1, s2 = st.columns(2)
            with s1: nova_s  = st.text_input("Nova senha", type="password", placeholder="Mínimo 6 caracteres")
            with s2: conf_s  = st.text_input("Confirmar",  type="password", placeholder="Repita a senha")
            salvar_s = st.form_submit_button("💾 Salvar senha", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)  # fecha div alterar senha

        if salvar_s:
            if len(nova_s) < 6:        st.error("Senha mínima de 6 caracteres.")
            elif nova_s != conf_s:     st.error("As senhas não coincidem.")
            else:
                ok, msg = _alterar_senha(u_edit["id"], nova_s)
                st.success(msg) if ok else st.error(msg)

        # ── Lojas vinculadas ──
        st.markdown("""
<div style='background:#141416;border:1px solid #2A2A2F;border-radius:14px;padding:18px 22px;margin-bottom:14px'>
  <div style='color:#F5F5F7;font-size:.85rem;font-weight:700;margin-bottom:12px'>🏪 Lojas vinculadas</div>
""", unsafe_allow_html=True)

        ids_atuais   = list(u_edit.get("id_unidades") or [])
        nomes_atuais = [lojas_map.get(i, f"ID {i}") for i in ids_atuais]

        with st.form("form_lojas_v2", clear_on_submit=False):
            novas = st.multiselect("Lojas", options=nomes_loja, default=nomes_atuais,
                                   label_visibility="collapsed")
            salvar_l = st.form_submit_button("💾 Salvar lojas", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)  # fecha div lojas

        if salvar_l:
            ids_novos = [l["id"] for l in lojas if l["trade_name"] in novas]
            ok, msg = _atualizar_lojas(u_edit["id"], ids_novos)
            st.success(msg) if ok else st.error(msg)

        # ── Zona de perigo ──
        st.markdown("""
<div style='background:#141416;border:1px solid #3A1A1A;border-radius:14px;padding:18px 22px'>
  <div style='color:#EF4444;font-size:.85rem;font-weight:700;margin-bottom:6px'>🗑️ Zona de perigo</div>
  <div style='color:#5A5A65;font-size:.78rem;margin-bottom:12px'>
    Esta ação é irreversível. O usuário será removido permanentemente.
  </div>
""", unsafe_allow_html=True)

        confirma = st.checkbox(f"Confirmo que quero excluir **{nome_edit}**",
                               key="confirma_del_v2")
        if st.button("🗑️ Excluir usuário", disabled=not confirma,
                     key="btn_del_v2", use_container_width=True):
            if u_edit["id"] == st.session_state.user.get("id"):
                st.error("Você não pode excluir sua própria conta.")
            else:
                ok, msg = _deletar_usuario(u_edit["id"])
                st.success(msg) if ok else st.error(msg)
                if ok:
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)  # fecha zona de perigo
