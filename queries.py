import hashlib

from db import fetch_all, fetch_one


def hash_password(plain: str) -> str:
    clean = (plain or "").strip()
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()


def authenticate_user(login: str, password: str):
    pw_hash = hash_password(password)
    campo   = (login or "").strip().lower()

    row = fetch_one(
        """
        SELECT id, username, email, role, nome_completo, telefone
        FROM cardapio_cmv.usuarios_portal
        WHERE (LOWER(TRIM(email)) = %s OR LOWER(TRIM(username)) = %s)
          AND password_hash = %s
        LIMIT 1
        """,
        (campo, campo, pw_hash),
    )

    # ── Fallback: senha em texto puro no banco ──
    if row is None:
        plain = (password or "").strip()
        row = fetch_one(
            """
            SELECT id, username, email, role, nome_completo, telefone
            FROM cardapio_cmv.usuarios_portal
            WHERE (LOWER(TRIM(email)) = %s OR LOWER(TRIM(username)) = %s)
              AND password_hash = %s
            LIMIT 1
            """,
            (campo, campo, plain),
        )

    if row is None:
        return None

    user = dict(row)

    # ── Busca id_unidades (coluna pode ainda não existir) ──
    try:
        extra = fetch_one(
            "SELECT id_unidades FROM cardapio_cmv.usuarios_portal WHERE id = %s",
            (user["id"],),
        )
        user["id_unidades"] = list(extra.get("id_unidades") or []) if extra else []
    except Exception:
        user["id_unidades"] = []

    return user


def list_units_for_user(user_id: int, role: str, id_unidades=None):
    """
    Admin      → todas as unidades de unidade_uf.
    Franqueado → cruza id_unidades (array em usuarios_portal) com unidade_uf.
    Não usa a tabela usuarios_unidades — ela não existe neste projeto.
    """
    if (role or "").lower() == "admin":
        return fetch_all(
            """
            SELECT id, trade_name, estado, short_desc_state
            FROM cardapio_cmv.unidade_uf
            ORDER BY trade_name
            """
        )

    # ── Franqueado: id_unidades é um INT[] em usuarios_portal ──
    ids = list(id_unidades) if id_unidades else []
    if not ids:
        return []

    try:
        rows = fetch_all(
            """
            SELECT id, trade_name, estado, short_desc_state
            FROM cardapio_cmv.unidade_uf
            WHERE id = ANY(%s)
            ORDER BY trade_name
            """,
            (ids,),
        )
        return rows if rows else []
    except Exception as e:
        print(f"[list_units] error: {e}")

    return []


def kpi_vendas(trade_name: str):
    try:
        return fetch_one(
            """
            SELECT
                COALESCE(SUM(CASE WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW())
                             THEN total_amount END), 0) AS mes_atual,
                COALESCE(SUM(CASE WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW() - INTERVAL '1 month')
                             THEN total_amount END), 0) AS mes_anterior,
                COALESCE(SUM(CASE WHEN created_at::date = CURRENT_DATE THEN total_amount END), 0) AS hoje,
                COALESCE(COUNT(CASE WHEN created_at::date = CURRENT_DATE THEN 1 END), 0) AS pedidos_hoje,
                COALESCE(AVG(total_amount), 0) AS ticket_medio_geral
            FROM backup.vendas WHERE trade_name = %s
            """,
            (trade_name,),
        )
    except Exception:
        return {"mes_atual": 0, "mes_anterior": 0, "hoje": 0,
                "pedidos_hoje": 0, "ticket_medio_geral": 0}


def kpi_vendas_extras(trade_name: str):
    try:
        return fetch_one(
            """
            SELECT
                COALESCE(COUNT(CASE WHEN created_at::date = CURRENT_DATE - 1 THEN 1 END), 0) AS pedidos_ontem,
                COALESCE(SUM(CASE WHEN created_at::date = CURRENT_DATE - 1 THEN total_amount END), 0) AS fat_ontem,
                COALESCE(AVG(CASE WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW() - INTERVAL '1 month')
                             THEN total_amount END), 0) AS ticket_mes_anterior
            FROM backup.vendas WHERE trade_name = %s
            """,
            (trade_name,),
        )
    except Exception:
        return {"pedidos_ontem": 0, "fat_ontem": 0, "ticket_mes_anterior": 0}


def serie_temporal(trade_name: str, days: int):
    try:
        return fetch_all(
            """
            SELECT created_at::date AS data,
                   SUM(total_amount) AS faturamento,
                   COUNT(*) AS num_vendas,
                   AVG(total_amount) AS ticket_medio
            FROM backup.vendas
            WHERE trade_name = %s AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1 ORDER BY 1
            """,
            (trade_name, str(days)),
        )
    except Exception:
        return []


def pedidos_por_dia(trade_name: str, days: int):
    try:
        return fetch_all(
            """
            SELECT created_at::date AS data, COUNT(*) AS pedidos
            FROM backup.vendas
            WHERE trade_name = %s AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1 ORDER BY 1
            """,
            (trade_name, str(days)),
        )
    except Exception:
        return []


def status_vendas(trade_name: str, days: int):
    try:
        return fetch_all(
            """
            SELECT desc_store_sale_status AS status, COUNT(*) AS quantidade
            FROM backup.vendas
            WHERE trade_name = %s AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1 ORDER BY 2 DESC
            """,
            (trade_name, str(days)),
        )
    except Exception:
        return []


def top_itens(trade_name: str, days: int, limit: int = 15):
    try:
        return fetch_all(
            """
            SELECT vi.desc_sale_item AS produto,
                   vi.desc_store_category_item AS categoria,
                   SUM(vi.quantity) AS qtd_vendida,
                   SUM(vi.quantity * vi.unit_price) AS receita_total,
                   AVG(vi.unit_price) AS preco_medio
            FROM backup.venda_item vi
            WHERE vi.trade_name = %s
              AND vi.created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY vi.desc_sale_item, vi.desc_store_category_item
            ORDER BY receita_total DESC NULLS LAST
            LIMIT %s
            """,
            (trade_name, str(days), limit),
        )
    except Exception:
        return []


def kpi_clientes(trade_name: str):
    try:
        return fetch_one(
            """
            SELECT COUNT(DISTINCT numero_documento) AS total_clientes,
                   ROUND(AVG(ticket_medio)::numeric, 2) AS ticket_medio,
                   ROUND(AVG(frequencia)::numeric, 1) AS freq_media,
                   ROUND(AVG(recencia)::numeric, 0) AS recencia_media
            FROM clientes.clientes_historico_vendas_tratadas WHERE trade_name = %s
            """,
            (trade_name,),
        )
    except Exception:
        return {"total_clientes": 0, "ticket_medio": 0.0,
                "freq_media": 0.0, "recencia_media": 0.0}


def clientes_faixa_frequencia(trade_name: str):
    try:
        return fetch_all(
            """
            SELECT
                CASE
                    WHEN frequencia >= 15 THEN '15+'
                    WHEN frequencia >= 10 THEN '10–14'
                    WHEN frequencia >= 5  THEN '5–9'
                    WHEN frequencia >= 2  THEN '2–4'
                    ELSE '1'
                END AS faixa,
                COUNT(DISTINCT numero_documento) AS qtd
            FROM clientes.clientes_historico_vendas_tratadas
            WHERE trade_name = %s
            GROUP BY 1
            """,
            (trade_name,),
        )
    except Exception:
        return []


def clientes_rfm_points(trade_name: str, limit: int = 400):
    try:
        return fetch_all(
            """
            SELECT numero_documento, MAX(full_name) AS full_name,
                   MIN(recencia) AS recencia,
                   MAX(frequencia) AS frequencia,
                   AVG(ticket_medio)::float AS ticket_medio
            FROM clientes.clientes_historico_vendas_tratadas
            WHERE trade_name = %s
            GROUP BY numero_documento
            ORDER BY MAX(frequencia) DESC
            LIMIT %s
            """,
            (trade_name, limit),
        )
    except Exception:
        return []


def clientes_top50(trade_name: str):
    try:
        return fetch_all(
            """
            SELECT numero_documento, MAX(full_name) AS full_name,
                   MAX(frequencia) AS frequencia,
                   MIN(recencia) AS recencia,
                   ROUND(AVG(ticket_medio)::numeric, 2) AS ticket_medio
            FROM clientes.clientes_historico_vendas_tratadas
            WHERE trade_name = %s
            GROUP BY numero_documento
            ORDER BY MAX(frequencia) DESC NULLS LAST, AVG(ticket_medio) DESC NULLS LAST
            LIMIT 50
            """,
            (trade_name,),
        )
    except Exception:
        return []


def metas_historico(trade_name: str):
    return []


def meta_mes_atual(unidade_id: int):
    return None


def itens_cardapio_list():
    try:
        return fetch_all(
            """
            SELECT id_item, nome, ativo, data_criacao, data_atualizacao
            FROM cardapio_cmv.itens_cardapio
            ORDER BY nome
            """
        )
    except Exception:
        return []


def receita_por_categoria(trade_name: str, days: int):
    try:
        return fetch_all(
            """
            SELECT COALESCE(desc_store_category_item, '—') AS categoria,
                   SUM(quantity * unit_price) AS receita
            FROM backup.venda_item
            WHERE trade_name = %s
              AND created_at >= CURRENT_DATE - (%s || ' days')::INTERVAL
            GROUP BY 1
            ORDER BY receita DESC NULLS LAST
            """,
            (trade_name, str(days)),
        )
    except Exception:
        return []
