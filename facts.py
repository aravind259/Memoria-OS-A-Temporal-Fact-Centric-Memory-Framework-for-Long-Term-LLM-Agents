import sqlite3
import os
import uuid
from typing import List, Dict, Any, Optional
from app.core import clock

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.environ.get("FACTS_DB_PATH", os.path.join(ROOT_DIR, "memory_os_v2.db"))


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None):
    with get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                attribute TEXT NOT NULL,
                value TEXT NOT NULL,
                kind TEXT NOT NULL,
                cardinality TEXT NOT NULL DEFAULT 'many',
                valid_from TEXT,
                valid_to TEXT,
                status TEXT NOT NULL,
                source_text TEXT,
                created_at TEXT NOT NULL,
                last_accessed_at TEXT NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 1
            )
        """)
        # Auto-migration: check if cardinality column exists
        cur = conn.cursor()
        cols = [col[1] for col in cur.execute("PRAGMA table_info(facts)").fetchall()]
        if "cardinality" not in cols:
            conn.execute("ALTER TABLE facts ADD COLUMN cardinality TEXT NOT NULL DEFAULT 'many'")

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_facts_user_status 
            ON facts(user_id, status)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_facts_lookup 
            ON facts(user_id, subject, attribute, status)
        """)
        conn.commit()


# Ensure table exists on import
init_db()


def get_existing_attributes(user_id: str, db_path: Optional[str] = None) -> List[str]:
    """
    Returns unique attribute names associated with user_id in the facts table.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT attribute FROM facts WHERE user_id = ? ORDER BY attribute",
            (user_id,)
        )
        rows = cur.fetchall()
        return [row["attribute"] for row in rows]


def get_active_facts(user_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns all active facts for a user.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM facts WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC",
            (user_id,)
        )
        return [dict(row) for row in cur.fetchall()]


def get_all_facts(user_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns all facts (active and superseded) for a user.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM facts WHERE user_id = ? ORDER BY created_at ASC",
            (user_id,)
        )
        return [dict(row) for row in cur.fetchall()]
