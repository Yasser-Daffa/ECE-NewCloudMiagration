import sys
# Fix for PyInstaller: ensure python-dotenv is discoverable
if hasattr(sys, '_MEIPASS'):
    import os
    os.environ['PYTHONPATH'] = sys._MEIPASS


import time
import psycopg2
from psycopg2.pool import SimpleConnectionPool


# ================== SUPABASE SESSION POOLER CONFIG ==================

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_HOST = os.getenv("SUPABASE_HOST")
SUPABASE_PORT = os.getenv("SUPABASE_PORT")
SUPABASE_USER = os.getenv("SUPABASE_USER")
SUPABASE_PASS = os.getenv("SUPABASE_PASS")
SUPABASE_DB = os.getenv("SUPABASE_DB")



# =====================================================================
#                       SIMPLE CONNECTION (DIRECT)
# =====================================================================

def get_connection(retries=3, delay=2):
    """
    Attempts to connect to PostgreSQL with automatic retry.
    Used mainly for checking connectivity.
    """

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            con = psycopg2.connect(
                host=SUPABASE_HOST,
                port=SUPABASE_PORT,
                database=SUPABASE_DB,
                user=SUPABASE_USER,
                password=SUPABASE_PASS,
                sslmode="require",
                connect_timeout=5,
            )
            cur = con.cursor()
            return con, cur

        except Exception as e:
            last_error = e
            print(f"[DB] Connection attempt {attempt}/{retries} failed: {e}")
            time.sleep(delay)

    raise last_error


# =====================================================================
#                         LAZY CONNECTION POOL
# =====================================================================

_pool = None   # IMPORTANT: DO NOT create the pool at import time.


def _create_pool():
    """
    Creates the connection pool **only when needed**.
    This prevents crashes upon import when offline.
    """
    return SimpleConnectionPool(
        minconn=3,
        maxconn=15,
        host=SUPABASE_HOST,
        port=SUPABASE_PORT,
        database=SUPABASE_DB,
        user=SUPABASE_USER,
        password=SUPABASE_PASS,
        sslmode="require",
        connect_timeout=5,
    )


def get_pooled_connection():
    """
    Returns a pooled PostgreSQL connection and cursor.
    Creates the pool lazily (on first demand).
    """

    global _pool

    if _pool is None:
        try:
            print("[DB] Creating connection pool...")
            _pool = _create_pool()
        except Exception as e:
            print("[DB] FAILED to create pool:", e)
            raise e

    con = _pool.getconn()
    con.autocommit = True
    return con, con.cursor()


def release_connection(con):
    """Returns a connection back to the pool (if pool exists)."""
    global _pool
    if _pool:
        _pool.putconn(con)


# =====================================================================
#                       CONNECTIVITY CHECK
# =====================================================================

def is_connected_to_db():
    """
    Returns True if database is reachable, False otherwise.
    """
    try:
        con, cur = get_connection()
        cur.execute("SELECT 1;")
        cur.close()
        con.close()
        return True
    except:
        return False


# =====================================================================
#                       CONNECTION RETRY LOGIC
# =====================================================================

def attempt_connection_with_retry(max_attempts=3, delay=2):
    """
    Safe function for UI:
    Returns True if connected, False if all attempts failed.
    """

    for attempt in range(1, max_attempts + 1):
        print(f"[DB] TRY {attempt}/{max_attempts}")
        if is_connected_to_db():
            print("[DB] Connection OK!")
            return True

        time.sleep(delay)

    return False


