import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from config import mcp_settings

logger = logging.getLogger(__name__)

def run_query(sql: str, params: tuple = ()) -> list:
    conn = psycopg2.connect(**mcp_settings.db_dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
            logger.info("[db_query] 조회 완료: " + str(len(rows)) + "건")
            return rows
    finally:
        conn.close()
