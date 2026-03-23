"""
Queries administrativas — Ital In House.
Lógica retroativa: usa ontem (ou último dia com dados) como referência.
Cache TTL=600s (10 min) em todas as queries pesadas.
"""

import streamlit as st
from db import fetch_all, fetch_one


# ─────────────────────────────────────────────
#  LÓGICA RETROATIVA — último dia com dados
# ─────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def ultimo_dia_com_dados(trade_name: str | None = None) -> tuple[str, str]:
    """
    Retorna (data_iso 'YYYY-MM-DD', label 'DD/MM') do último dia
    com registros anterior a hoje. Exclui hoje pois dados são parciais.
    """
    try:
        filtro = "AND trade_name = %s" if trade_name else ""
        params = (trade_name,) if trade_name else ()
        row = fetch_one(f"""
            SELECT MAX(created_at::date)::text AS dt
            FROM backup.vendas
            WHERE created_at::date < CURRENT_DATE {filtro}
        """, params)
        if row and row.get("dt"):
            dt = row["dt"]
            p  = dt.split("-")
            return dt, f"{p[2]}/{p[1]}"
    except Exception as e:
        print(f"[ultimo_dia] {e}")
    return "", ""


# ─────────────────────────────────────────────
#  KPIs RETROATIVOS — usa ontem como base
# ─────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def kpi_admin(dias: int) -> dict:
    """
    KPIs consolidados da rede.
    'fat_ref' = faturamento do último dia com dados (retroativo).
    """
    try:
        row = fetch_one("""
            SELECT
                COALESCE(SUM(total_amount), 0)::float        AS faturamento_total,
                COALESCE(COUNT(*), 0)::int                   AS total_pedidos,
                COALESCE(AVG(total_amount), 0)::float        AS ticket_medio
            FROM backup.vendas
            WHERE created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
        """, (str(dias),))

        # Busca último dia com dados (retroativo — exclui hoje)
        ref_row = fetch_one("""
            SELECT
                MAX(created_at::date)::text                                AS ref_data,
                COALESCE(SUM(CASE WHEN created_at::date =
                    (SELECT MAX(created_at::date) FROM backup.vendas
                     WHERE created_at::date < CURRENT_DATE)
                    THEN total_amount END), 0)::float                      AS fat_ref,
                COALESCE(COUNT(CASE WHEN created_at::date =
                    (SELECT MAX(created_at::date) FROM backup.vendas
                     WHERE created_at::date < CURRENT_DATE)
                    THEN 1 END), 0)::int                                   AS ped_ref
            FROM backup.vendas
            WHERE created_at::date < CURRENT_DATE
        """)

        # Dia anterior ao ref para comparação
        ant_row = fetch_one("""
            WITH ref AS (
                SELECT MAX(created_at::date) AS ref_date
                FROM backup.vendas WHERE created_at::date < CURRENT_DATE
            ),
            ant AS (
                SELECT MAX(created_at::date) AS ant_date
                FROM backup.vendas
                WHERE created_at::date < (SELECT ref_date FROM ref)
            )
            SELECT
                COALESCE(SUM(CASE WHEN v.created_at::date = a.ant_date
                             THEN v.total_amount END), 0)::float AS fat_ant,
                COALESCE(COUNT(CASE WHEN v.created_at::date = a.ant_date
                             THEN 1 END), 0)::int                AS ped_ant
            FROM backup.vendas v, ant a
        """)

        lojas = fetch_one("""
            SELECT COUNT(DISTINCT trade_name)::int AS total
            FROM backup.vendas WHERE created_at::date < CURRENT_DATE
              AND created_at >= CURRENT_DATE - '30 days'::INTERVAL
        """)

        resultado = dict(row) if row else {}
        if ref_row:
            resultado["fat_ref"]  = float(ref_row.get("fat_ref") or 0)
            resultado["ped_ref"]  = int(ref_row.get("ped_ref") or 0)
            resultado["ref_data"] = ref_row.get("ref_data") or ""
            if resultado["ref_data"]:
                p = resultado["ref_data"].split("-")
                resultado["ref_label"] = f"{p[2]}/{p[1]}"
            else:
                resultado["ref_label"] = "—"
        if ant_row:
            resultado["fat_ant"] = float(ant_row.get("fat_ant") or 0)
            resultado["ped_ant"] = int(ant_row.get("ped_ant") or 0)
        resultado["total_lojas"] = int((lojas or {}).get("total", 0))
        return resultado
    except Exception as e:
        print(f"kpi_admin: {e}")
        return {"faturamento_total": 0.0, "total_pedidos": 0,
                "ticket_medio": 0.0, "fat_ref": 0.0, "ped_ref": 0,
                "fat_ant": 0.0, "ped_ant": 0,
                "ref_label": "—", "ref_data": "", "total_lojas": 0}


@st.cache_data(ttl=600, show_spinner=False)
def serie_admin(dias: int) -> list:
    """Série diária da rede — exclui hoje (dados parciais)."""
    try:
        return fetch_all("""
            SELECT created_at::date AS data,
                   SUM(total_amount)::float AS faturamento,
                   COUNT(*)::int            AS pedidos
            FROM backup.vendas
            WHERE created_at::date < CURRENT_DATE
              AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1 ORDER BY 1
        """, (str(dias),)) or []
    except Exception as e:
        print(f"serie_admin: {e}")
        return []


# ─────────────────────────────────────────────
#  RANKINGS TOP 10
# ─────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def ranking_lojas(dias: int) -> list:
    """Top 10 lojas por faturamento com variação % vs período anterior."""
    try:
        return fetch_all("""
            WITH atual AS (
                SELECT trade_name,
                       SUM(total_amount)::float AS faturamento,
                       COUNT(*)::int            AS pedidos,
                       AVG(total_amount)::float AS ticket_medio
                FROM backup.vendas
                WHERE created_at::date < CURRENT_DATE
                  AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
                GROUP BY trade_name
            ),
            anterior AS (
                SELECT trade_name,
                       SUM(total_amount)::float AS faturamento_ant
                FROM backup.vendas
                WHERE created_at::date < CURRENT_DATE
                  AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL * 2
                  AND created_at <  CURRENT_DATE - (%s || ' days')::INTERVAL
                GROUP BY trade_name
            )
            SELECT a.trade_name, a.faturamento, a.pedidos, a.ticket_medio,
                   COALESCE(ant.faturamento_ant, 0)::float AS faturamento_ant,
                   CASE WHEN COALESCE(ant.faturamento_ant,0) > 0
                        THEN ROUND(((a.faturamento - ant.faturamento_ant)
                                    / ant.faturamento_ant * 100)::numeric, 1)::float
                        ELSE NULL END AS variacao_pct
            FROM atual a LEFT JOIN anterior ant USING (trade_name)
            ORDER BY a.faturamento DESC LIMIT 10
        """, (str(dias), str(dias), str(dias))) or []
    except Exception as e:
        print(f"ranking_lojas: {e}")
        return []


@st.cache_data(ttl=600, show_spinner=False)
def ranking_volume_pedidos(dias: int) -> list:
    """
    Top 10 lojas por VOLUME DE PEDIDOS (não ticket médio).
    Mais estratégico: mostra quem está operando mais.
    """
    try:
        return fetch_all("""
            WITH atual AS (
                SELECT trade_name,
                       COUNT(*)::int            AS pedidos,
                       SUM(total_amount)::float AS faturamento,
                       AVG(total_amount)::float AS ticket_medio
                FROM backup.vendas
                WHERE created_at::date < CURRENT_DATE
                  AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
                GROUP BY trade_name
            ),
            anterior AS (
                SELECT trade_name, COUNT(*)::int AS pedidos_ant
                FROM backup.vendas
                WHERE created_at::date < CURRENT_DATE
                  AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL * 2
                  AND created_at <  CURRENT_DATE - (%s || ' days')::INTERVAL
                GROUP BY trade_name
            )
            SELECT a.trade_name, a.pedidos, a.faturamento, a.ticket_medio,
                   COALESCE(ant.pedidos_ant, 0)::int AS pedidos_ant,
                   CASE WHEN COALESCE(ant.pedidos_ant,0) > 0
                        THEN ROUND(((a.pedidos - ant.pedidos_ant)::float
                                    / ant.pedidos_ant * 100)::numeric, 1)::float
                        ELSE NULL END AS variacao_pct
            FROM atual a LEFT JOIN anterior ant USING (trade_name)
            ORDER BY a.pedidos DESC LIMIT 10
        """, (str(dias), str(dias), str(dias))) or []
    except Exception as e:
        print(f"ranking_volume_pedidos: {e}")
        return []


@st.cache_data(ttl=600, show_spinner=False)
def ranking_plataformas(dias: int) -> list:
    """Performance por plataforma — usa backup.vendas como fallback."""
    try:
        return fetch_all("""
            SELECT COALESCE(desc_partner_sale, 'Direto') AS plataforma,
                   COUNT(*)::int                         AS pedidos,
                   SUM(total_amount)::float              AS faturamento,
                   AVG(total_amount)::float              AS ticket_medio,
                   ROUND((COUNT(*) * 100.0
                          / NULLIF(SUM(COUNT(*)) OVER (), 0))::numeric, 1)::float AS pct_pedidos,
                   ROUND((SUM(total_amount) * 100.0
                          / NULLIF(SUM(SUM(total_amount)) OVER (), 0))::numeric, 1)::float AS pct_faturamento
            FROM backup.vendas
            WHERE created_at::date < CURRENT_DATE
              AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY COALESCE(desc_partner_sale, 'Direto')
            ORDER BY faturamento DESC
        """, (str(dias),)) or []
    except Exception as e:
        print(f"ranking_plataformas: {e}")
        return []


@st.cache_data(ttl=600, show_spinner=False)
def ranking_ticket_por_loja(dias: int, limit: int = 10) -> list:
    """Top lojas por ticket médio (mínimo 30 pedidos)."""
    try:
        return fetch_all("""
            SELECT v.trade_name,
                   u.estado, u.regiao_simples,
                   COUNT(*)::int             AS pedidos,
                   AVG(total_amount)::float  AS ticket_medio,
                   SUM(total_amount)::float  AS faturamento
            FROM backup.vendas v
            LEFT JOIN cardapio_cmv.unidade_uf u ON u.trade_name = v.trade_name
            WHERE v.created_at::date < CURRENT_DATE
              AND v.created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY v.trade_name, u.estado, u.regiao_simples
            HAVING COUNT(*) >= 30
            ORDER BY ticket_medio DESC LIMIT %s
        """, (str(dias), limit)) or []
    except Exception as e:
        print(f"ranking_ticket: {e}")
        return []


# ─────────────────────────────────────────────
#  CONSOLIDADOS DA REDE
# ─────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def kpi_vendas_rede(dias: int) -> dict:
    """KPIs de vendas retroativos — usa último dia com dados, não hoje."""
    try:
        r = fetch_one("""
            SELECT
                COALESCE(SUM(CASE WHEN DATE_TRUNC('month', created_at)
                               = DATE_TRUNC('month', NOW())
                             THEN total_amount END), 0)::float  AS mes_atual,
                COALESCE(SUM(CASE WHEN DATE_TRUNC('month', created_at)
                               = DATE_TRUNC('month', NOW() - INTERVAL '1 month')
                             THEN total_amount END), 0)::float  AS mes_anterior,
                COALESCE(AVG(total_amount), 0)::float           AS ticket_medio_geral
            FROM backup.vendas
            WHERE created_at::date < CURRENT_DATE
              AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
        """, (str(dias),))
        return dict(r) if r else {}
    except Exception as e:
        print(f"kpi_vendas_rede: {e}")
        return {}


@st.cache_data(ttl=600, show_spinner=False)
def kpi_vendas_rede_extras(dias: int) -> dict:
    """Fat e pedidos do último dia com dados + dia anterior para comparação."""
    try:
        r = fetch_one("""
            WITH ref AS (
                SELECT MAX(created_at::date) AS ref_date
                FROM backup.vendas WHERE created_at::date < CURRENT_DATE
            ),
            ant AS (
                SELECT MAX(created_at::date) AS ant_date
                FROM backup.vendas
                WHERE created_at::date < (SELECT ref_date FROM ref)
            )
            SELECT
                r.ref_date::text AS ref_data,
                COALESCE(SUM(CASE WHEN v.created_at::date = r.ref_date
                             THEN v.total_amount END), 0)::float AS fat_ontem,
                COALESCE(COUNT(CASE WHEN v.created_at::date = r.ref_date
                             THEN 1 END), 0)::int                AS pedidos_ontem,
                COALESCE(SUM(CASE WHEN v.created_at::date = a.ant_date
                             THEN v.total_amount END), 0)::float AS fat_ant,
                COALESCE(COUNT(CASE WHEN v.created_at::date = a.ant_date
                             THEN 1 END), 0)::int                AS ped_ant,
                COALESCE(AVG(CASE WHEN DATE_TRUNC('month', v.created_at)
                               = DATE_TRUNC('month', NOW() - INTERVAL '1 month')
                             THEN v.total_amount END), 0)::float AS ticket_mes_anterior
            FROM backup.vendas v, ref r, ant a
        """)
        resultado = dict(r) if r else {}
        if resultado.get("ref_data"):
            p = resultado["ref_data"].split("-")
            resultado["ref_label"] = f"{p[2]}/{p[1]}"
        else:
            resultado["ref_label"] = "—"
        return resultado
    except Exception as e:
        print(f"kpi_vendas_rede_extras: {e}")
        return {}


@st.cache_data(ttl=600, show_spinner=False)
def serie_rede(dias: int) -> list:
    """Série diária da rede — exclui hoje."""
    try:
        return fetch_all("""
            SELECT created_at::date AS data,
                   SUM(total_amount)::float AS faturamento,
                   COUNT(*)::int            AS num_vendas,
                   AVG(total_amount)::float AS ticket_medio
            FROM backup.vendas
            WHERE created_at::date < CURRENT_DATE
              AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1 ORDER BY 1
        """, (str(dias),)) or []
    except Exception as e:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def pedidos_rede(dias: int) -> list:
    try:
        return fetch_all("""
            SELECT created_at::date AS data, COUNT(*)::int AS pedidos
            FROM backup.vendas
            WHERE created_at::date < CURRENT_DATE
              AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1 ORDER BY 1
        """, (str(dias),)) or []
    except Exception as e:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def status_rede(dias: int) -> list:
    try:
        return fetch_all("""
            SELECT desc_store_sale_status AS status, COUNT(*)::int AS quantidade
            FROM backup.vendas
            WHERE created_at::date < CURRENT_DATE
              AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1 ORDER BY 2 DESC
        """, (str(dias),)) or []
    except Exception as e:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def top_itens_rede(dias: int, limit: int = 15) -> list:
    try:
        return fetch_all("""
            SELECT desc_sale_item                    AS produto,
                   desc_store_category_item          AS categoria,
                   SUM(quantity)::int                AS qtd_vendida,
                   SUM(quantity * unit_price)::float AS receita_total,
                   AVG(unit_price)::float            AS preco_medio
            FROM backup.venda_item
            WHERE created_at::date < CURRENT_DATE
              AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
              AND desc_sale_item IS NOT NULL
            GROUP BY 1, 2 ORDER BY receita_total DESC NULLS LAST LIMIT %s
        """, (str(dias), limit)) or []
    except Exception as e:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def receita_categoria_rede(dias: int) -> list:
    try:
        return fetch_all("""
            SELECT COALESCE(desc_store_category_item, '—') AS categoria,
                   SUM(quantity * unit_price)::float        AS receita
            FROM backup.venda_item
            WHERE created_at::date < CURRENT_DATE
              AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1 ORDER BY receita DESC NULLS LAST
        """, (str(dias),)) or []
    except Exception as e:
        return []


@st.cache_data(ttl=600, show_spinner=False)
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
        return {}


@st.cache_data(ttl=600, show_spinner=False)
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
        return []


@st.cache_data(ttl=600, show_spinner=False)
def clientes_rfm_rede(limit: int = 400) -> list:
    try:
        return fetch_all("""
            SELECT numero_documento, MAX(full_name) AS full_name,
                   MIN(recencia)::float   AS recencia,
                   MAX(frequencia)::float AS frequencia,
                   AVG(ticket_medio)::float AS ticket_medio
            FROM clientes.clientes_historico_vendas_tratadas
            GROUP BY numero_documento
            ORDER BY MAX(frequencia) DESC LIMIT %s
        """, (limit,)) or []
    except Exception as e:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def clientes_top50_rede() -> list:
    try:
        return fetch_all("""
            SELECT numero_documento, MAX(full_name) AS full_name,
                   MAX(frequencia)::float                      AS frequencia,
                   MIN(recencia)::float                        AS recencia,
                   ROUND(AVG(ticket_medio)::numeric, 2)::float AS ticket_medio
            FROM clientes.clientes_historico_vendas_tratadas
            GROUP BY numero_documento
            ORDER BY MAX(frequencia) DESC NULLS LAST LIMIT 50
        """) or []
    except Exception as e:
        return []
