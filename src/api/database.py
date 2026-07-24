import logging

import duckdb

logger = logging.getLogger(__name__)

try:
    con = duckdb.connect(database=":memory:", read_only=False)
    logger.info("DuckDB in-memory connection initialized")
except Exception:
    logger.exception("Unable to initialize DuckDB")
    con = None


def get_db_connection():
    """Return the process-wide read-only analytics connection."""
    return con
