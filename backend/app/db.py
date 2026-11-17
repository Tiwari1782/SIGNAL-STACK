"""Database connection manager with connection pooling for Neon PostgreSQL."""

import atexit
from contextlib import contextmanager
import logging
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from .config import DATABASE_URL

log = logging.getLogger(__name__)

# Connection pool maintains warm connections to Neon, eliminating repeated 2-second SSL/TLS handshakes
_pool: ConnectionPool = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            timeout=15.0,
            max_idle=300.0,
            kwargs={"row_factory": dict_row}
        )
    return _pool


def close_pool():
    global _pool
    if _pool is not None:
        try:
            _pool.close()
        except Exception:
            pass
        _pool = None


atexit.register(close_pool)


@contextmanager
def get_conn():
    """Context manager providing a connection from the pool."""
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def query(sql: str, params: tuple = (), one: bool = False):
    """Execute SQL query using pooled connection."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        if cur.description is None:
            conn.commit()
            return None
        res = cur.fetchone() if one else cur.fetchall()
        conn.commit()
        return res
