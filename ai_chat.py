"""IA - IH · Motor de IA — google.genai (biblioteca atual)"""

import os
import streamlit as st
from google import genai
from google.genai import types

from db import fetch_all, fetch_one
from queries import kpi_clientes, kpi_vendas

# Modelos disponíveis na conta (em ordem de preferência)
_MODELOS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
]

_client_cache = None


def _key(name: str) -> str:
    val = os.getenv(name, "").strip()
    if val:
        return val
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def _client():
    global _client_cache
    if _client_cache is None:
        key = _key("GOOGLE_API_KEY")
        if not key:
            return None
        _client_cache = genai.Client(api_key=key)
    return _client_cache


# ─────────────────────────────────────────────────────────
#  STREAMING
# ─────────────────────────────────────────────────────────

def ia_stream(messages: list, context: str):
    """Generator de tokens para st.write_stream()."""
    client = _client()
    if not client:
        yield "⚠️ GOOGLE_API_KEY não configurada no .env ou Secrets."
        return

    system_prompt = (
        "Você é a IA - IH, assistente da Ital In House Macarrão Gourmet.\n"
        "Responda SEMPRE em português do Brasil, de forma direta e amigável.\n"
        "Use apenas os dados do contexto. Se não souber, diga claramente.\n"
        "Máximo 3 parágrafos por resposta.\n\n"
        + context
    )

    # Converte histórico: streamlit usa "assistant", genai usa "model"
    history = []
    for msg in messages[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history.append(types.Content(
            role=role,
            parts=[types.Part(text=msg["content"])]
        ))
    history.append(types.Content(
        role="user",
        parts=[types.Part(text=messages[-1]["content"])]
    ))

    for modelo in _MODELOS:
        try:
            print(f"[IA-IH] Tentando {modelo}...")
            stream = client.models.generate_content_stream(
                model=modelo,
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=800,
                    temperature=0.6,
                ),
            )
            for chunk in stream:
                if chunk.text:
                    yield chunk.text
            print(f"[IA-IH] ✓ respondeu via {modelo}")
            return

        except Exception as e:
            err = str(e)
            print(f"[IA-IH] {modelo} falhou: {err[:120]}")

            if "api key" in err.lower() or "401" in err:
                yield "⚠️ Chave Google inválida. Verifique GOOGLE_API_KEY."
                return
            if "429" in err or "quota" in err.lower() or "resource exhausted" in err.lower():
                yield "⚠️ Limite de requisições atingido. Aguarde alguns segundos."
                return
            # 404 ou outro erro → tenta próximo modelo
            continue

    yield "⚠️ Nenhum modelo disponível respondeu. Verifique sua conta no Google AI Studio."


def ia_responder(messages: list, context: str) -> str:
    return "".join(ia_stream(messages, context))


# ─────────────────────────────────────────────────────────
#  QUERIES DE CONTEXTO
# ─────────────────────────────────────────────────────────

def _top_prods(trade_name=None, dias=30, limit=10) -> list:
    try:
        where = f"created_at >= CURRENT_DATE - ('{dias} days')::INTERVAL AND desc_sale_item IS NOT NULL"
        if trade_name:
            where = f"trade_name=%s AND {where}"
            params = (trade_name, limit)
        else:
            params = (limit,)
        return fetch_all(f"""
            SELECT desc_sale_item AS produto, desc_store_category_item AS categoria,
                   SUM(quantity)::int AS qtd_vendida,
                   SUM(quantity * unit_price)::float AS receita_total
            FROM backup.venda_item WHERE {where}
            GROUP BY 1,2 ORDER BY receita_total DESC LIMIT %s
        """, params) or []
    except Exception as e:
        print(f"[top_prods] {e}")
        return []


def _kpi_rede(dias=30) -> dict:
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


def _ranking(dias=30, limit=10, asc=False) -> list:
    try:
        order = "ASC" if asc else "DESC"
        return fetch_all(f"""
            SELECT trade_name,
                   SUM(total_amount)::float AS faturamento,
                   COUNT(*)::int            AS pedidos,
                   AVG(total_amount)::float AS ticket
            FROM backup.vendas
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY trade_name ORDER BY faturamento {order} LIMIT %s
        """, (str(dias), limit)) or []
    except Exception as e:
        print(f"[ranking] {e}")
        return []


def _fmt_prods(rows):
    if not rows: return "sem dados"
    return "\n".join(
        f"{i+1}. {r.get('produto','—')} ({r.get('categoria','—')}): "
        f"{int(r.get('qtd_vendida') or 0):,} un. | R$ {float(r.get('receita_total') or 0):,.2f}"
        for i, r in enumerate(rows)
    )


def _fmt_rank(rows):
    if not rows: return "sem dados"
    return "\n".join(
        f"{i+1}. {r.get('trade_name','—')}: "
        f"R$ {float(r.get('faturamento') or 0):,.2f} ({int(r.get('pedidos') or 0):,} pedidos)"
        for i, r in enumerate(rows)
    )


# ─────────────────────────────────────────────────────────
#  BUILD CONTEXT
# ─────────────────────────────────────────────────────────

def build_context_ia(user: dict, loja_atual: dict) -> str:
    is_admin = (user.get("role") or "").lower() == "admin"
    nome = (user.get("nome_completo") or user.get("nome")
            or user.get("username") or "Usuário")

    trade = None
    if loja_atual and loja_atual.get("trade_name") not in (None, "__admin__", ""):
        trade = loja_atual["trade_name"]

    lojas_permitidas = []
    if not is_admin:
        lojas_permitidas = [l["trade_name"] for l in (user.get("lojas") or [])]

    bloco = ""

    if is_admin:
        try:
            kv   = _kpi_rede(30)
            rank = _ranking(30, 10)
            pior = _ranking(30, 5, asc=True)
            top  = _top_prods(dias=30, limit=10)
            bloco += f"""
=== REDE — últimos 30 dias ===
Faturamento: R$ {float(kv.get('fat_total') or 0):,.2f}
Pedidos: {int(kv.get('pedidos_total') or 0):,}
Ticket médio: R$ {float(kv.get('ticket_medio') or 0):,.2f}

=== TOP 10 LOJAS por faturamento ===
{_fmt_rank(rank)}

=== 5 MENORES FATURAMENTOS ===
{_fmt_rank(pior)}

=== TOP 10 PRODUTOS DA REDE (30d) ===
{_fmt_prods(top)}
"""
        except Exception as e:
            print(f"[ctx admin] {e}")

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
            var = ((ma - mp) / mp * 100) if mp else 0
            bloco += f"""
=== LOJA: {trade} ===
Mês atual: R$ {ma:,.2f} ({'↑' if var>=0 else '↓'}{abs(var):.1f}% vs anterior)
Mês anterior: R$ {mp:,.2f}
Ticket médio: R$ {tk:,.2f}
Clientes únicos: {tc:,} | Frequência média: {fm:.1f}x

=== TOP 10 PRODUTOS — {trade} (30d) ===
{_fmt_prods(top)}
"""
        except Exception as e:
            print(f"[ctx loja] {e}")

    dados = bloco.strip() or "Dados não disponíveis no momento."

    regra = ""
    if not is_admin and lojas_permitidas:
        ls = ", ".join(lojas_permitidas)
        regra = (f"\nPERMISSÃO OBRIGATÓRIA: Este usuário é FRANQUEADO e só pode ver "
                 f"dados de: {ls}. Recuse qualquer pergunta sobre outras lojas.\n")

    perfil = "ADMINISTRADOR" if is_admin else f"FRANQUEADO ({', '.join(lojas_permitidas) or '—'})"
    ctx    = "Rede toda" if not trade else f"Loja: {trade}"

    return f"""Usuário: {nome} ({perfil}) | {ctx}
{regra}
DADOS DISPONÍVEIS:
{dados}"""


def build_context(trade_name: str) -> str:
    kv  = kpi_vendas(trade_name) or {}
    top = _top_prods(trade_name=trade_name, dias=30, limit=5)
    return (f"Unidade: {trade_name}. "
            f"Mês: R$ {float(kv.get('mes_atual') or 0):,.2f}. "
            f"Produtos: {_fmt_prods(top)}")
