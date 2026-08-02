import os

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool

# Hosted Postgres (Railway/Render/etc.) injects a single DATABASE_URL; local
# dev uses the discrete VAPOSPY_PG_* vars matching database/docker-compose.yml.
DATABASE_URL = os.environ.get("DATABASE_URL")

DSN = dict(
    host=os.environ.get("VAPOSPY_PG_HOST", "localhost"),
    port=os.environ.get("VAPOSPY_PG_PORT", "5433"),
    dbname=os.environ.get("VAPOSPY_PG_DB", "vapospy_clone"),
    user=os.environ.get("VAPOSPY_PG_USER", "vapospy"),
    password=os.environ.get("VAPOSPY_PG_PASSWORD", "vapospy"),
)

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        if DATABASE_URL:
            _pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL)
        else:
            _pool = SimpleConnectionPool(1, 10, **DSN)
    return _pool


def query(sql, params=None):
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        pool.putconn(conn)


def query_one(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None
