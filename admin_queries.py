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


# ─────────────────────────────────────────────
#  QUERIES CONSOLIDADAS — usadas nas abas admin
#  quando nenhuma loja está selecionada
# ─────────────────────────────────────────────

def kpi_vendas_rede(dias: int) -> dict:
    """KPIs de vendas da rede inteira para as abas consolidadas."""
    try:
        r = fetch_one("""
            SELECT
                COALESCE(SUM(CASE WHEN DATE_TRUNC('month', created_at)
                               = DATE_TRUNC('month', NOW())
                             THEN total_amount END), 0)::float  AS mes_atual,
                COALESCE(SUM(CASE WHEN DATE_TRUNC('month', created_at)
                               = DATE_TRUNC('month', NOW() - INTERVAL '1 month')
                             THEN total_amount END), 0)::float  AS mes_anterior,
                COALESCE(SUM(CASE WHEN created_at::date = CURRENT_DATE
                             THEN total_amount END), 0)::float  AS hoje,
                COALESCE(COUNT(CASE WHEN created_at::date = CURRENT_DATE
                             THEN 1 END), 0)::int               AS pedidos_hoje,
                COALESCE(AVG(total_amount), 0)::float           AS ticket_medio_geral
            FROM backup.vendas
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
        """, (str(dias),))
        return dict(r) if r else {}
    except Exception as e:
        print(f"kpi_vendas_rede: {e}")
        return {}


def kpi_vendas_rede_extras(dias: int) -> dict:
    try:
        r = fetch_one("""
            SELECT
                COALESCE(COUNT(CASE WHEN created_at::date = CURRENT_DATE - 1
                             THEN 1 END), 0)::int               AS pedidos_ontem,
                COALESCE(SUM(CASE WHEN created_at::date = CURRENT_DATE - 1
                             THEN total_amount END), 0)::float  AS fat_ontem,
                COALESCE(AVG(CASE WHEN DATE_TRUNC('month', created_at)
                               = DATE_TRUNC('month', NOW() - INTERVAL '1 month')
                             THEN total_amount END), 0)::float  AS ticket_mes_anterior
            FROM backup.vendas
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
        """, (str(dias),))
        return dict(r) if r else {}
    except Exception as e:
        print(f"kpi_vendas_rede_extras: {e}")
        return {}


def serie_rede(dias: int) -> list:
    try:
        return fetch_all("""
            SELECT created_at::date AS data,
                   SUM(total_amount)::float AS faturamento,
                   COUNT(*)::int            AS num_vendas,
                   AVG(total_amount)::float AS ticket_medio
            FROM backup.vendas
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1 ORDER BY 1
        """, (str(dias),)) or []
    except Exception as e:
        print(f"serie_rede: {e}")
        return []


def pedidos_rede(dias: int) -> list:
    try:
        return fetch_all("""
            SELECT created_at::date AS data, COUNT(*)::int AS pedidos
            FROM backup.vendas
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1 ORDER BY 1
        """, (str(dias),)) or []
    except Exception as e:
        print(f"pedidos_rede: {e}")
        return []


def status_rede(dias: int) -> list:
    try:
        return fetch_all("""
            SELECT desc_store_sale_status AS status, COUNT(*)::int AS quantidade
            FROM backup.vendas
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1 ORDER BY 2 DESC
        """, (str(dias),)) or []
    except Exception as e:
        print(f"status_rede: {e}")
        return []


def top_itens_rede(dias: int, limit: int = 15) -> list:
    try:
        return fetch_all("""
            SELECT desc_sale_item                           AS produto,
                   desc_store_category_item                AS categoria,
                   SUM(quantity)::int                      AS qtd_vendida,
                   SUM(quantity * unit_price)::float       AS receita_total,
                   AVG(unit_price)::float                  AS preco_medio
            FROM backup.venda_item
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
              AND desc_sale_item IS NOT NULL
            GROUP BY desc_sale_item, desc_store_category_item
            ORDER BY receita_total DESC NULLS LAST
            LIMIT %s
        """, (str(dias), limit)) or []
    except Exception as e:
        print(f"top_itens_rede: {e}")
        return []


def receita_categoria_rede(dias: int) -> list:
    try:
        return fetch_all("""
            SELECT COALESCE(desc_store_category_item, '—') AS categoria,
                   SUM(quantity * unit_price)::float        AS receita
            FROM backup.venda_item
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1 ORDER BY receita DESC NULLS LAST
        """, (str(dias),)) or []
    except Exception as e:
        print(f"receita_categoria_rede: {e}")
        return []


def kpi_clientes_rede() -> dict:
    try:
        r = fetch_one("""
            SELECT COUNT(DISTINCT numero_documento)::int       AS total_clientes,
                   ROUND(AVG(ticket_medio)::numeric, 2)::float AS ticket_medio,
                   ROUND(AVG(frequencia)::numeric, 1)::float   AS freq_media,
                   ROUND(AVG(recencia)::numeric, 0)::float     AS recencia_media
            FROM clientes.clientes_historico_vendas_tratadas
        """)
        return dict(r) if r else {}
    except Exception as e:
        print(f"kpi_clientes_rede: {e}")
        return {}


def clientes_faixa_rede() -> list:
    try:
        return fetch_all("""
            SELECT
                CASE
                    WHEN frequencia >= 15 THEN '15+'
                    WHEN frequencia >= 10 THEN '10–14'
                    WHEN frequencia >= 5  THEN '5–9'
                    WHEN frequencia >= 2  THEN '2–4'
                    ELSE '1'
                END AS faixa,
                COUNT(DISTINCT numero_documento)::int AS qtd
            FROM clientes.clientes_historico_vendas_tratadas
            GROUP BY 1
        """) or []
    except Exception as e:
        print(f"clientes_faixa_rede: {e}")
        return []


def clientes_rfm_rede(limit: int = 400) -> list:
    try:
        return fetch_all("""
            SELECT numero_documento, MAX(full_name) AS full_name,
                   MIN(recencia)::float              AS recencia,
                   MAX(frequencia)::float            AS frequencia,
                   AVG(ticket_medio)::float          AS ticket_medio
            FROM clientes.clientes_historico_vendas_tratadas
            GROUP BY numero_documento
            ORDER BY MAX(frequencia) DESC
            LIMIT %s
        """, (limit,)) or []
    except Exception as e:
        print(f"clientes_rfm_rede: {e}")
        return []


def clientes_top50_rede() -> list:
    try:
        return fetch_all("""
            SELECT numero_documento, MAX(full_name) AS full_name,
                   MAX(frequencia)::float                        AS frequencia,
                   MIN(recencia)::float                          AS recencia,
                   ROUND(AVG(ticket_medio)::numeric, 2)::float   AS ticket_medio
            FROM clientes.clientes_historico_vendas_tratadas
            GROUP BY numero_documento
            ORDER BY MAX(frequencia) DESC NULLS LAST
            LIMIT 50
        """) or []
    except Exception as e:
        print(f"clientes_top50_rede: {e}")
        return []
        return []
