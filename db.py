from __future__ import annotations

import os

import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def fetch_all(sql: str, params: tuple | None = None):
    """Fetch all rows, with automatic rollback and reconnection on error."""
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    except psycopg2.errors.InFailedSqlTransaction:
        # Reset the cached connection
        st.cache_resource.clear()
        try:
            conn = get_connection()
            conn.rollback()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params or ())
                return cur.fetchall()
        except Exception as e:
            print(f"fetch_all error after reset: {e}")
            return []
    except Exception as e:
        print(f"fetch_all error: {e}")
        try:
            conn = get_connection()
            conn.rollback()
        except:
            pass
        return []


def fetch_one(sql: str, params: tuple | None = None):
    """Fetch one row, with automatic rollback and reconnection on error."""
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()
    except psycopg2.errors.InFailedSqlTransaction:
        # Reset the cached connection
        st.cache_resource.clear()
        try:
            conn = get_connection()
            conn.rollback()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params or ())
                return cur.fetchone()
        except Exception as e:
            print(f"fetch_one error after reset: {e}")
            return None
    except Exception as e:
        print(f"fetch_one error: {e}")
        try:
            conn = get_connection()
            conn.rollback()
        except:
            pass
        return None


def execute(sql: str, params: tuple | None = None) -> None:
    """Execute a query, with automatic rollback on error."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()
    except psycopg2.errors.InFailedSqlTransaction:
        # Reset the cached connection
        st.cache_resource.clear()
        try:
            conn = get_connection()
            conn.rollback()
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
            conn.commit()
        except Exception as e:
            print(f"execute error after reset: {e}")
    except Exception as e:
        print(f"execute error: {e}")
        try:
            conn = get_connection()
            conn.rollback()
        except:
            pass
