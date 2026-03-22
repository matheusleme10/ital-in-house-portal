"""IA - IH · Motor de IA (Gemini principal, Anthropic fallback)."""

import os
import time

from google import genai
from google.genai import types

from db import fetch_all, fetch_one
from queries import kpi_clientes, kpi_vendas


# ─────────────────────────────────────────────────────────
#  GEMINI
# ─────────────────────────────────────────────────────────

def _responder_gemini(messages: list, context: str) -> str:
    gemini_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not gemini_key:
        return "⚠️ GOOGLE_API_KEY não configurada no .env"

    client = genai.Client(api_key=gemini_key)

    system_prompt = (
        "Você é a IA - IH, assistente inteligente da Ital In House.\n"
        "Responda SEMPRE em português do Brasil, de forma direta.\n"
        "Não invente dados. Use apenas as informações do contexto.\n\n"
        + context
    )

    # Gemini usa "user" e "model" — NUNCA "assistant"
    history = []
    for msg in messages[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
    history.append(types.Content(
        role="user",
        parts=[types.Part(text=messages[-1]["content"])]
    ))

    try:
        # gemini-2.0-flash = melhor custo-benefício velocidade/qualidade
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=800,   # Reduzido para respostas mais rápidas
                temperature=0.6,
            ),
        )
        return resp.text

    except Exception as e:
        err = str(e)
        print(f"[GEMINI] {err}")

        if "quota" in err.lower() or "429" in err or "resource exhausted" in err.lower():
            # Fallback imediato para modelo lite
            try:
                time.sleep(2)
                resp2 = client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=history,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        max_output_tokens=800,
                        temperature=0.6,
                    ),
                )
                return resp2.text
            except Exception as e2:
                print(f"[GEMINI LITE] {e2}")
                return "⚠️ Limite atingido. Aguarde 1 minuto e tente novamente."
        elif "404" in err or "not found" in err.lower():
            return "⚠️ Modelo indisponível. Tente novamente."
        elif "api key" in err.lower() or "401" in err:
            return "⚠️ Chave Google inválida. Verifique GOOGLE_API_KEY no .env"
        else:
            return f"⚠️ Erro Gemini: {err}"


def ia_responder(messages: list, context: str) -> str:
    """Gemini (principal) com fallback para Anthropic."""
    gemini_key    = os.getenv("GOOGLE_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    print(f"[IA-IH] Gemini={'✓' if gemini_key else '✗'} | "
          f"Anthropic={'✓' if anthropic_key else '✗'} | "
          f"msgs={len(messages)}")
    if messages:
        print(f"[IA-IH] '{messages[-1]['content'][:60]}'")

    if gemini_key:
        r = _responder_gemini(messages, context)
        if not r.startswith("⚠️ Chave Google") and not r.startswith("⚠️ Erro Gemini"):
            return r
        if not anthropic_key:
            return r
        print("[IA-IH] Gemini falhou → Anthropic")

    if anthropic_key:
        try:
            from anthropic import Anthropic
            c = Anthropic(api_key=anthropic_key)
            r = c.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5"),
                max_tokens=800,
                system="Você é a IA - IH, assistente da Ital In House.\n" + context,
                messages=messages,
            )
            return r.content[0].text
        except Exception as e:
            err = str(e).lower()
            if "credit" in err or "balance" in err or "billing" in err:
                return "⚠️ Saldo insuficiente no Claude. Recarregue em console.anthropic.com"
            return f"⚠️ Erro Anthropic: {err}"

    return "⚠️ Nenhuma IA configurada. Adicione GOOGLE_API_KEY ou ANTHROPIC_API_KEY no .env"


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
    is_admin  = (user.get("role") or "").lower() == "admin"
    nome      = user.get("nome_completo") or user.get("username", "Usuário")
    trade     = None
    if loja_atual and loja_atual.get("trade_name") not in (None, "__admin__"):
        trade = loja_atual["trade_name"]

    bloco_rede = ""
    bloco_loja = ""

    # ── Admin: dados consolidados da rede ──
    if is_admin:
        try:
            kv   = _kpi_rede(30)
            rank = _ranking(30, 10)
            pior = _ranking(30, 5, asc=True)
            top  = _top_prods(dias=30, limit=10)
            top_feb = _top_prods(mes=2, ano=2026, limit=10)
            top_jan = _top_prods(mes=1, ano=2026, limit=10)
            top_dez = _top_prods(mes=12, ano=2025, limit=10)

            fat  = float(kv.get("fat_total") or 0)
            peds = int(kv.get("pedidos_total") or 0)
            tick = float(kv.get("ticket_medio") or 0)

            bloco_rede = f"""
=== REDE — últimos 30 dias ===
Faturamento total: R$ {fat:,.2f}
Total de pedidos:  {peds:,}
Ticket médio:      R$ {tick:,.2f}

=== TOP 10 LOJAS ===
{_fmt_rank(rank)}

=== 5 PIORES LOJAS ===
{_fmt_rank(pior)}

=== TOP PRODUTOS DA REDE — últimos 30 dias ===
{_fmt_prods(top)}

=== TOP PRODUTOS — fev/2026 ===
{_fmt_prods(top_feb)}

=== TOP PRODUTOS — jan/2026 ===
{_fmt_prods(top_jan)}

=== TOP PRODUTOS — dez/2025 ===
{_fmt_prods(top_dez)}
"""
        except Exception as e:
            print(f"[ctx admin] {e}")

    # ── Dados da loja selecionada ──
    if trade:
        try:
            kv  = kpi_vendas(trade) or {}
            kc  = kpi_clientes(trade) or {}
            top = _top_prods(trade_name=trade, dias=30, limit=10)
            top_feb = _top_prods(trade_name=trade, mes=2, ano=2026, limit=10)
            top_jan = _top_prods(trade_name=trade, mes=1, ano=2026, limit=10)

            ma  = float(kv.get("mes_atual") or 0)
            mp  = float(kv.get("mes_anterior") or 0)
            hj  = float(kv.get("hoje") or 0)
            phj = int(kv.get("pedidos_hoje") or 0)
            tk  = float(kv.get("ticket_medio_geral") or 0)
            tc  = int(kc.get("total_clientes") or 0)
            tm  = float(kc.get("ticket_medio") or 0)
            fm  = float(kc.get("freq_media") or 0)
            rm  = float(kc.get("recencia_media") or 0)

            bloco_loja = f"""
=== LOJA: {trade} ===
Faturamento mês atual:    R$ {ma:,.2f}
Faturamento mês anterior: R$ {mp:,.2f}
Hoje:                     R$ {hj:,.2f}
Pedidos hoje:             {phj}
Ticket médio:             R$ {tk:,.2f}

=== CLIENTES — {trade} ===
Total clientes únicos: {tc:,}
Ticket médio histórico: R$ {tm:,.2f}
Frequência média:       {fm:.1f} compras
Recência média:         {rm:.0f} dias

=== TOP PRODUTOS — {trade} (30d) ===
{_fmt_prods(top)}

=== TOP PRODUTOS — {trade} (fev/2026) ===
{_fmt_prods(top_feb)}

=== TOP PRODUTOS — {trade} (jan/2026) ===
{_fmt_prods(top_jan)}
"""
        except Exception as e:
            print(f"[ctx loja] {e}")

    dados = (bloco_rede + bloco_loja).strip() or \
            "Não há dados disponíveis. Informe o usuário."

    perfil    = "ADMINISTRADOR" if is_admin else "FRANQUEADO"
    loja_info = f"Loja: {trade}" if trade else "Visão consolidada da rede"

    return f"""
Você é a IA - IH, assistente inteligente da Ital In House.
Usuário: {nome} ({perfil}) | {loja_info}

REGRAS:
1. Responda sempre em português do Brasil, de forma direta e amigável
2. Use 1-2 emojis por resposta no máximo
3. NUNCA invente dados — use apenas o contexto abaixo
4. Se a informação não estiver no contexto, diga claramente que não tem
5. Valores monetários: R$ X.XXX,XX
6. Máximo 3 parágrafos por resposta — seja conciso
7. Mensagens de teste: confirme que está funcionando e pergunte como ajudar
8. Para produtos: use as seções TOP PRODUTOS abaixo

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