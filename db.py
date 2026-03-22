from __future__ import annotations

import os

import psycopg2
import streamlit as st
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv(override=True)


def _get(key: str, default: str = "") -> str:
    """
    Lê variável de ambiente com fallback para st.secrets.
    Funciona em: local (.env), Railway (env vars) e Streamlit Cloud (secrets).
    """
    # 1. Variável de ambiente do sistema (Railway injeta assim)
    val = os.getenv(key, "")
    if val:
        return val
    # 2. Streamlit secrets (Streamlit Cloud)
    try:
        val = st.secrets.get(key, "")
        if val:
            return str(val)
    except Exception:
        pass
    return default


@st.cache_resource
def get_connection():
    conn = psycopg2.connect(
        host=_get("DB_HOST", "localhost"),
        port=_get("DB_PORT", "5432"),
        dbname=_get("DB_NAME", "postgres"),
        user=_get("DB_USER", "postgres"),
        password=_get("DB_PASSWORD", ""),
        sslmode="require",
        connect_timeout=10,
    )
    conn.autocommit = True
    return conn


def _reset_conn():
    """Limpa o cache e reconecta."""
    try:
        st.cache_resource.clear()
    except Exception:
        pass


def fetch_all(sql: str, params: tuple | None = None):
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    except psycopg2.errors.InFailedSqlTransaction:
        _reset_conn()
        try:
            conn = get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params or ())
                return cur.fetchall()
        except Exception as e:
            print(f"fetch_all retry error: {e}")
            return []
    except Exception as e:
        print(f"fetch_all error: {e}")
        _reset_conn()
        return []


def fetch_one(sql: str, params: tuple | None = None):
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()
    except psycopg2.errors.InFailedSqlTransaction:
        _reset_conn()
        try:
            conn = get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params or ())
                return cur.fetchone()
        except Exception as e:
            print(f"fetch_one retry error: {e}")
            return None
    except Exception as e:
        print(f"fetch_one error: {e}")
        _reset_conn()
        return None


def execute(sql: str, params: tuple | None = None) -> None:
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
    except psycopg2.errors.InFailedSqlTransaction:
        _reset_conn()
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
        except Exception as e:
            print(f"execute retry error: {e}")
    except Exception as e:
        print(f"execute error: {e}")
        _reset_conn()
