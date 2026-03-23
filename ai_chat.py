"""IA - IH · Motor de IA — Gemini 1.5 Flash (estável) com fallback."""

import os
import time

import streamlit as st
from google import genai
from google.genai import types

from db import fetch_all, fetch_one
from queries import kpi_clientes, kpi_vendas

# ── Modelos em ordem de preferência (todos estáveis) ──
_MODELOS = [
    "gemini-1.5-flash",      # principal — rápido e barato
    "gemini-1.5-flash-8b",   # fallback leve
    "gemini-1.5-pro",        # fallback premium se os outros falharem
]


def _key(name: str) -> str:
    """Lê chave do .env ou Streamlit Secrets."""
    val = os.getenv(name, "").strip()
    if val:
        return val
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────
#  GEMINI — fallback automático por modelos
# ─────────────────────────────────────────────────────────

def _build_history(messages: list) -> list:
    """Converte histórico para formato Gemini (user/model, nunca assistant)."""
    history = []
    for msg in messages[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
    history.append(types.Content(
        role="user",
        parts=[types.Part(text=messages[-1]["content"])]
    ))
    return history


def _responder_gemini(messages: list, context: str) -> str:
    gemini_key = _key("GOOGLE_API_KEY")
    if not gemini_key:
        return "⚠️ GOOGLE_API_KEY não configurada no .env ou Secrets."

    client  = genai.Client(api_key=gemini_key)
    history = _build_history(messages)

    system_prompt = (
        "Você é a IA - IH, assistente inteligente da Ital In House.\n"
        "Responda SEMPRE em português do Brasil, de forma direta.\n"
        "Não invente dados. Use apenas as informações do contexto.\n\n"
        + context
    )

    ultimo_erro = ""
    for modelo in _MODELOS:
        try:
            resp = client.models.generate_content(
                model=modelo,
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=800,
                    temperature=0.6,
                ),
            )
            print(f"[IA-IH] ✓ respondeu via {modelo}")
            return resp.text

        except Exception as e:
            err = str(e)
            ultimo_erro = err
            print(f"[IA-IH] {modelo} falhou: {err[:120]}")

            is_quota = "quota" in err.lower() or "429" in err or "resource exhausted" in err.lower()
            is_key   = "api key" in err.lower() or "401" in err or "invalid" in err.lower() and "key" in err.lower()

            if is_key:
                return "⚠️ Chave Google inválida. Verifique GOOGLE_API_KEY no .env"
            if is_quota:
                time.sleep(1)  # aguarda antes do próximo modelo

            # qualquer erro → tenta próximo modelo
            continue

    # todos falharam — retorna o erro real para diagnóstico
    return f"⚠️ Não foi possível conectar à IA agora. Detalhe: {ultimo_erro[:200]}"


def ia_responder(messages: list, context: str) -> str:
    """Ponto de entrada principal. Gemini com fallback automático entre modelos."""
    gemini_key = _key("GOOGLE_API_KEY")

    print(f"[IA-IH] Gemini={'✓' if gemini_key else '✗'} | msgs={len(messages)}")
    if messages:
        print(f"[IA-IH] pergunta: '{messages[-1]['content'][:80]}'")

    if gemini_key:
        return _responder_gemini(messages, context)

    return "⚠️ GOOGLE_API_KEY não configurada. Adicione no .env ou Streamlit Secrets."


# ─────────────────────────────────────────────────────────
#  QUERIES DE CONTEXTO
# ─────────────────────────────────────────────────────────

def _top_prods(trade_name: str = None, mes: int = None, ano: int = None,
               dias: int = 30, limit: int = 10) -> list:
    """Top produtos — por loja, por mês/ano, ou consolidado."""
    try:
        if mes and ano:
            params = (mes, ano, limit) if not trade_name else (trade_name, mes, ano, limit)
            where  = "EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s"
            where  = (f"trade_name=%s AND " + where) if trade_name else where
        else:
            where  = f"created_at >= CURRENT_DATE - ('{dias} days')::INTERVAL"
            params = (limit,) if not trade_name else (trade_name, limit)
            where  = (f"trade_name=%s AND " + where) if trade_name else where

        return fetch_all(f"""
            SELECT desc_sale_item      AS produto,
                   desc_store_category_item AS categoria,
                   SUM(quantity)::int  AS qtd_vendida,
                   SUM(quantity * unit_price)::float AS receita_total
            FROM backup.venda_item
            WHERE {where} AND desc_sale_item IS NOT NULL
            GROUP BY desc_sale_item, desc_store_category_item
            ORDER BY receita_total DESC
            LIMIT %s
        """, params)
    except Exception as e:
        print(f"[top_prods] {e}")
        return []


def _kpi_rede(dias: int = 30) -> dict:
    try:
        r = fetch_one("""
            SELECT COALESCE(SUM(total_amount),0)::float AS fat_total,
                   COALESCE(COUNT(*),0)::int            AS pedidos_total,
                   COALESCE(AVG(total_amount),0)::float AS ticket_medio
            FROM backup.vendas
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
        """, (str(dias),))
        return dict(r) if r else {}
    except Exception as e:
        print(f"[kpi_rede] {e}")
        return {}


def _ranking(dias: int = 30, limit: int = 10, asc: bool = False) -> list:
    try:
        order = "ASC" if asc else "DESC"
        return fetch_all(f"""
            SELECT trade_name,
                   SUM(total_amount)::float AS faturamento,
                   COUNT(*)::int            AS pedidos,
                   AVG(total_amount)::float AS ticket
            FROM backup.vendas
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY trade_name
            ORDER BY faturamento {order}
            LIMIT %s
        """, (str(dias), limit))
    except Exception as e:
        print(f"[ranking] {e}")
        return []


# ─────────────────────────────────────────────────────────
#  FORMATADORES
# ─────────────────────────────────────────────────────────

def _fmt_prods(rows: list) -> str:
    if not rows:
        return "sem dados"
    out = []
    for i, r in enumerate(rows):
        fat  = float(r.get("receita_total") or 0)
        qtd  = int(r.get("qtd_vendida") or 0)
        prod = r.get("produto") or "—"
        cat  = r.get("categoria") or "—"
        out.append(f"{i+1}. {prod} ({cat}): {qtd} un. | R$ {fat:,.2f}")
    return "\n".join(out)


def _fmt_rank(rows: list) -> str:
    if not rows:
        return "sem dados"
    out = []
    for i, r in enumerate(rows):
        fat  = float(r.get("faturamento") or 0)
        peds = int(r.get("pedidos") or 0)
        nome = r.get("trade_name") or "—"
        out.append(f"{i+1}. {nome}: R$ {fat:,.2f} ({peds} pedidos)")
    return "\n".join(out)


# ─────────────────────────────────────────────────────────
#  BUILD CONTEXT
# ─────────────────────────────────────────────────────────

def build_context_ia(user: dict, loja_atual: dict) -> str:
    is_admin = (user.get("role") or "").lower() == "admin"

    # ── nome: session guarda como "nome", não "nome_completo" ──
    nome = (user.get("nome_completo")
            or user.get("nome")
            or user.get("username")
            or "Usuário")

    trade = None
    if loja_atual and loja_atual.get("trade_name") not in (None, "__admin__", ""):
        trade = loja_atual["trade_name"]

    # ── Lojas que o franqueado pode ver ──
    lojas_permitidas: list[str] = []
    if not is_admin:
        lojas_permitidas = [l["trade_name"] for l in (user.get("lojas") or [])]

    bloco_rede = ""
    bloco_loja = ""

    # ── Admin: dados consolidados da rede ──
    if is_admin:
        try:
            kv   = _kpi_rede(30)
            rank = _ranking(30, 10)
            pior = _ranking(30, 5, asc=True)
            top  = _top_prods(dias=30, limit=10)

            fat  = float(kv.get("fat_total") or 0)
            peds = int(kv.get("pedidos_total") or 0)
            tick = float(kv.get("ticket_medio") or 0)

            bloco_rede = f"""
=== REDE — últimos 30 dias ===
Faturamento total: R$ {fat:,.2f}
Total de pedidos:  {peds:,}
Ticket médio:      R$ {tick:,.2f}

=== TOP 10 LOJAS por faturamento ===
{_fmt_rank(rank)}

=== 5 LOJAS COM MENOR FATURAMENTO ===
{_fmt_rank(pior)}

=== TOP PRODUTOS DA REDE (30d) ===
{_fmt_prods(top)}
"""
        except Exception as e:
            print(f"[ctx admin] {e}")

    # ── Dados da loja selecionada ──
    if trade:
        try:
            kv  = kpi_vendas(trade) or {}
            kc  = kpi_clientes(trade) or {}
            top = _top_prods(trade_name=trade, dias=30, limit=10)

            ma  = float(kv.get("mes_atual") or 0)
            mp  = float(kv.get("mes_anterior") or 0)
            tk  = float(kv.get("ticket_medio_geral") or 0)
            tc  = int(kc.get("total_clientes") or 0)
            fm  = float(kc.get("freq_media") or 0)
            rm  = float(kc.get("recencia_media") or 0)

            var = ((ma - mp) / mp * 100) if mp else 0
            sinal = "↑" if var >= 0 else "↓"

            bloco_loja = f"""
=== LOJA: {trade} ===
Faturamento mês atual:    R$ {ma:,.2f} ({sinal}{abs(var):.1f}% vs mês anterior)
Faturamento mês anterior: R$ {mp:,.2f}
Ticket médio:             R$ {tk:,.2f}

=== CLIENTES — {trade} ===
Total clientes únicos: {tc:,}
Frequência média:      {fm:.1f} compras
Recência média:        {rm:.0f} dias

=== TOP 10 PRODUTOS — {trade} (30d) ===
{_fmt_prods(top)}
"""
        except Exception as e:
            print(f"[ctx loja] {e}")

    dados = (bloco_rede + bloco_loja).strip() or "Não há dados disponíveis no momento."

    # ── Regra de permissão para franqueado ──
    regra_permissao = ""
    if not is_admin and lojas_permitidas:
        lojas_str = ", ".join(lojas_permitidas)
        regra_permissao = f"""
REGRA DE PERMISSÃO (OBRIGATÓRIA):
- Este usuário é FRANQUEADO e só tem acesso aos dados das suas lojas: {lojas_str}
- Se perguntarem sobre QUALQUER outra loja ou dados da rede, responda:
  "Só tenho acesso aos dados da(s) sua(s) unidade(s): {lojas_str}."
- NUNCA compartilhe dados de outras lojas, mesmo que estejam no contexto.
"""

    perfil    = "ADMINISTRADOR (acesso total à rede)" if is_admin else f"FRANQUEADO (acesso restrito a: {', '.join(lojas_permitidas) or trade or '—'})"
    loja_info = f"Loja ativa: {trade}" if trade else "Visão consolidada da rede"

    return f"""
Você é a IA - IH, assistente inteligente da Ital In House Macarrão Gourmet.
Usuário: {nome} ({perfil}) | {loja_info}
{regra_permissao}
REGRAS GERAIS:
1. Responda SEMPRE em português do Brasil, de forma direta e amigável
2. Use no máximo 2 emojis por resposta
3. NUNCA invente dados — use apenas o contexto abaixo
4. Se a informação não estiver disponível, diga claramente
5. Valores monetários: R$ X.XXX,XX | Crescimento: ↑ | Queda: ↓
6. Máximo 3 parágrafos — seja conciso e objetivo
7. Mensagens de teste: confirme que está funcionando normalmente
8. Finalize com 1 insight ou sugestão prática quando relevante

DADOS DISPONÍVEIS:
{dados}
""".strip()


# ── Compatibilidade legada ──
def build_context(trade_name: str) -> str:
    kv  = kpi_vendas(trade_name) or {}
    kc  = kpi_clientes(trade_name) or {}
    top = _top_prods(trade_name=trade_name, dias=30, limit=10)

    def money(k):
        from decimal import Decimal
        v = kv.get(k)
        if v is None: return "R$ 0,00"
        x = float(v) if isinstance(v, Decimal) else float(v)
        return f"R$ {x:,.2f}".replace(",","X").replace(".",",").replace("X",".")

    return (
        f"Unidade: {trade_name}. "
        f"Mês atual: {money('mes_atual')}. Hoje: {money('hoje')}. "
        f"Pedidos hoje: {int(kv.get('pedidos_hoje') or 0)}. "
        f"Ticket médio: {money('ticket_medio_geral')}. "
        f"Clientes: {int(kc.get('total_clientes') or 0)}. "
        f"Top produtos: {_fmt_prods(top)}. "
        "Responda em português. Não invente."
    )