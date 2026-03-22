"""Queries para as materialized views do schema views_n8n."""

from db import fetch_all


def _semana_label(semana_ano: str) -> str:
    """'2026-08' → 'Sem 08/2026'"""
    try:
        partes = str(semana_ano).split("-")
        if len(partes) == 2:
            return f"Sem {partes[1].zfill(2)}/{partes[0]}"
        return str(semana_ano)
    except Exception:
        return str(semana_ano)


def _f(val) -> float:
    """Converte qualquer valor para float seguro."""
    try:
        return float(val) if val is not None else 0.0
    except Exception:
        return 0.0


def mv_faturamento(trade_name: str, semanas: int = 12) -> list:
    try:
        rows = fetch_all("""
            SELECT semana_ano, data_referencia,
                   faturamento_total,
                   faturamento_total_almoco,
                   faturamento_total_janta,
                   faturamento_ifood,
                   faturamento_anotaai,
                   faturamento_99food,
                   faturamento_outros,
                   faturamento_recorrentes,
                   faturamento_nao_recorrente,
                   faturamento_green
            FROM views_n8n.mv_faturamento
            WHERE unidade = %s
              AND data_referencia >= CURRENT_DATE - (%s || ' weeks')::INTERVAL
            ORDER BY data_referencia ASC
        """, (trade_name, str(semanas)))
        return rows or []
    except Exception as e:
        print(f"[mv_faturamento] {e}")
        return []


def mv_pedidos(trade_name: str, semanas: int = 12) -> list:
    try:
        rows = fetch_all("""
            SELECT semana_ano, data_referencia,
                   pedidos_total,
                   pedidos_total_almoco,
                   pedidos_total_janta,
                   pedidos_combos,
                   pedidos_green,
                   pedidos_recorrentes,
                   pedidos_nao_recorrente,
                   pedidos_nao_identificado
            FROM views_n8n.mv_pedidos
            WHERE unidade = %s
              AND data_referencia >= CURRENT_DATE - (%s || ' weeks')::INTERVAL
            ORDER BY data_referencia ASC
        """, (trade_name, str(semanas)))
        return rows or []
    except Exception as e:
        print(f"[mv_pedidos] {e}")
        return []


def mv_tickets(trade_name: str, semanas: int = 12) -> list:
    try:
        rows = fetch_all("""
            SELECT semana_ano, data_referencia,
                   "Tkt ifood",
                   "Tkt 99food",
                   "Tkt outros",
                   "Tkt dir",
                   "Tkt almoço",
                   "Tkt jantar",
                   "Tkt med pri",
                   "Tkt med rec",
                   "Tkt med tot"
            FROM views_n8n.mv_tickets
            WHERE unidade = %s
              AND data_referencia >= CURRENT_DATE - (%s || ' weeks')::INTERVAL
            ORDER BY data_referencia ASC
        """, (trade_name, str(semanas)))
        return rows or []
    except Exception as e:
        print(f"[mv_tickets] {e}")
        return []


def mv_descontos(trade_name: str, semanas: int = 12) -> list:
    try:
        rows = fetch_all("""
            SELECT semana_ano, data_referencia,
                   total_desconto_ifood,
                   total_desconto_anotaai,
                   total_desconto_99food,
                   total_desconto_outros,
                   total_desconto_geral
            FROM views_n8n.mv_descontos
            WHERE unidade = %s
              AND data_referencia >= CURRENT_DATE - (%s || ' weeks')::INTERVAL
            ORDER BY data_referencia ASC
        """, (trade_name, str(semanas)))
        return rows or []
    except Exception as e:
        print(f"[mv_descontos] {e}")
        return []


def mv_percentuais(trade_name: str, semanas: int = 12) -> list:
    try:
        rows = fetch_all("""
            SELECT semana_ano, data_referencia,
                   "Perc Faturamento Almoço",
                   "Perc Faturamento Jantar",
                   "Perc ifood",
                   "Perc anotai",
                   "Perc 99food",
                   "Perc outros",
                   "Perc Recor",
                   "Perc Novos",
                   "Perc NI"
            FROM views_n8n.mv_percentuais
            WHERE unidade = %s
              AND data_referencia >= CURRENT_DATE - (%s || ' weeks')::INTERVAL
            ORDER BY data_referencia ASC
        """, (trade_name, str(semanas)))
        return rows or []
    except Exception as e:
        print(f"[mv_percentuais] {e}")
        return []


def mv_vendas(trade_name: str, semanas: int = 12) -> list:
    try:
        rows = fetch_all("""
            SELECT semana_ano, data_referencia,
                   venda_total_almoco,
                   venda_total_janta,
                   vendas_ifood,
                   vendas_anotaai,
                   vendas_99food,
                   vendas_outros
            FROM views_n8n.mv_vendas
            WHERE unidade = %s
              AND data_referencia >= CURRENT_DATE - (%s || ' weeks')::INTERVAL
            ORDER BY data_referencia ASC
        """, (trade_name, str(semanas)))
        return rows or []
    except Exception as e:
        print(f"[mv_vendas] {e}")
        return []
