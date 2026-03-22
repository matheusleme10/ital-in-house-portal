"""Queries específicas para painel administrativo consolidado"""

from db import fetch_all, fetch_one


def kpi_admin(dias: int) -> dict:
    """KPIs consolidados de toda a rede (sem filtro de loja)."""
    try:
        row = fetch_one(
            """
            SELECT
                COALESCE(SUM(total_amount), 0)::float AS faturamento_total,
                COALESCE(COUNT(*), 0)::int AS total_pedidos,
                COALESCE(AVG(total_amount), 0)::float AS ticket_medio
            FROM backup.vendas
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            """,
            (str(dias),),
        )
        lojas = fetch_one("SELECT COUNT(*) AS total FROM cardapio_cmv.unidade_uf")
        
        if row:
            resultado = dict(row)
        else:
            resultado = {
                "faturamento_total": 0.0,
                "total_pedidos": 0,
                "ticket_medio": 0.0,
            }
        
        resultado['total_lojas'] = int(lojas.get('total', 0)) if lojas else 0
        return resultado
    except Exception as e:
        print(f"kpi_admin error: {e}")
        return {
            "faturamento_total": 0.0,
            "total_pedidos": 0,
            "ticket_medio": 0.0,
            "total_lojas": 0,
        }


def ranking_lojas(dias: int) -> list:
    """Ranking de lojas por faturamento no período (sem filtro)."""
    try:
        result = fetch_all(
            """
            SELECT 
                trade_name,
                SUM(total_amount)::float AS faturamento,
                COUNT(*)::int AS pedidos,
                AVG(total_amount)::float AS ticket_medio
            FROM backup.vendas
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY trade_name
            ORDER BY faturamento DESC
            LIMIT 20
            """,
            (str(dias),),
        )
        return result if result else []
    except Exception as e:
        print(f"ranking_lojas error: {e}")
        return []


def serie_admin(dias: int) -> list:
    """Série temporal de faturamento consolidado da rede (sem filtro)."""
    try:
        result = fetch_all(
            """
            SELECT 
                created_at::date AS data,
                SUM(total_amount)::float AS faturamento,
                COUNT(*)::int AS pedidos
            FROM backup.vendas
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY created_at::date
            ORDER BY 1
            """,
            (str(dias),),
        )
        return result if result else []
    except Exception as e:
        print(f"serie_admin error: {e}")
        return []
