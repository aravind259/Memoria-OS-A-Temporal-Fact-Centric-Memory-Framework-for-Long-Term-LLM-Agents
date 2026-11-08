import sqlite3
import json
import os
from datetime import datetime
from app.core import clock
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "memory_os_archive.db")

class ColdArchiveStorage:
    """
    OS Cold Storage Archive Engine (L3 SQLite Disk Storage):
    Provides persistent SQLite database for cold, archived, or paged-out memory blocks.
    Prevents memory clutter in ChromaDB active RAM vector database while ensuring zero data loss.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cold_memories (
                    id TEXT PRIMARY KEY,
                    document TEXT NOT NULL,
                    category TEXT,
                    importance REAL,
                    status TEXT,
                    user_id TEXT,
                    tenant_id TEXT,
                    created_at TEXT,
                    last_accessed_at TEXT,
                    modality TEXT,
                    image_url TEXT,
                    metadata_json TEXT,
                    archived_at TEXT
                )
            """)
            try:
                cursor.execute("ALTER TABLE cold_memories ADD COLUMN last_accessed_at TEXT")
            except Exception:
                pass
            conn.commit()

    def archive_memory(self, memory_data: Dict[str, Any]) -> bool:
        """
        Pages out a memory dict from Active Vector DB into Cold SQLite Storage.
        """
        mem_id = memory_data.get("id")
        if not mem_id:
            return False

        doc = memory_data.get("document", "")
        meta = dict(memory_data.get("metadata") or {})
        category = meta.get("category", "Fact")
        importance = float(meta.get("importance", 0.5))
        status = meta.get("status", "archived")
        user_id = meta.get("user_id", "default_user")
        tenant_id = meta.get("tenant_id", "default_tenant")
        created_at = meta.get("created_at", clock.get_now().isoformat())
        last_accessed_at = meta.get("last_accessed_at", clock.get_now().isoformat())
        modality = meta.get("modality", "text")
        image_url = meta.get("image_url", "")
        archived_at = clock.get_now().isoformat()

        meta.update({
            "id": mem_id,
            "tier": "L3",
            "status": status,
            "archived_at": archived_at
        })

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO cold_memories (
                        id, document, category, importance, status, user_id, tenant_id, created_at, last_accessed_at, modality, image_url, metadata_json, archived_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    mem_id, doc, category, importance, status, user_id, tenant_id,
                    created_at, last_accessed_at, modality, image_url, json.dumps(meta), archived_at
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"[ColdArchiveStorage] Error archiving memory {mem_id}: {e}")
            return False

    def search_l3(self, query: str, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """
        Searches L3 SQLite Cold Archive lexically using LIKE pattern matching.
        """
        q_tokens = [t.strip().lower() for t in query.split() if len(t.strip()) > 2]
        if not q_tokens:
            pattern = f"%{query.strip().lower()}%"
            where_sql = "LOWER(document) LIKE ?"
            params = [pattern]
        else:
            where_sql = " OR ".join(["LOWER(document) LIKE ?" for _ in q_tokens])
            params = [f"%{t}%" for t in q_tokens]

        if user_id:
            where_sql = f"user_id = ? AND ({where_sql})"
            params.insert(0, user_id)

        sql = f"SELECT * FROM cold_memories WHERE {where_sql} ORDER BY importance DESC, archived_at DESC LIMIT 10"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
            except Exception as e:
                print(f"[ColdArchiveStorage] Search error: {e}")
                return []

            results = []
            for row in rows:
                meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
                meta.update({
                    "id": row["id"],
                    "category": row["category"],
                    "importance": row["importance"],
                    "tier": "L3",
                    "status": row["status"],
                    "user_id": row["user_id"],
                    "tenant_id": row["tenant_id"],
                    "created_at": row["created_at"],
                    "last_accessed_at": clock.get_now().isoformat(),
                    "modality": row["modality"],
                    "image_url": row["image_url"],
                    "archived_at": row["archived_at"]
                })
                results.append({
                    "id": row["id"],
                    "document": row["document"],
                    "metadata": meta,
                    "score": 0.5
                })
            return results

    def get_archived_memories(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT * FROM cold_memories WHERE user_id = ? ORDER BY archived_at DESC", (user_id,))
            else:
                cursor.execute("SELECT * FROM cold_memories ORDER BY archived_at DESC")
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
                meta.update({
                    "id": row["id"],
                    "category": row["category"],
                    "importance": row["importance"],
                    "tier": "L3",
                    "status": row["status"],
                    "user_id": row["user_id"],
                    "tenant_id": row["tenant_id"],
                    "modality": row["modality"],
                    "image_url": row["image_url"],
                    "archived_at": row["archived_at"]
                })
                results.append({
                    "id": row["id"],
                    "document": row["document"],
                    "metadata": meta
                })
            return results

    def restore_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a memory record from Cold SQLite Archive for paging back into active L2 memory.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cold_memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
            meta["status"] = "active"
            meta["tier"] = "L2"
            doc = row["document"]
            
            cursor.execute("DELETE FROM cold_memories WHERE id = ?", (memory_id,))
            conn.commit()
            
            return {
                "id": row["id"],
                "document": doc,
                "metadata": meta
            }

    def delete_memory(self, memory_id: str) -> bool:
        """Deletes a single memory record from L3 archive."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cold_memories WHERE id = ?", (memory_id,))
            cnt = cursor.rowcount
            conn.commit()
            return cnt > 0

    def delete_user_archive(self, user_id: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cold_memories WHERE user_id = ?", (user_id,))
            cnt = cursor.rowcount
            conn.commit()
            return cnt

    def clear_all(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cold_memories")
            conn.commit()

    def update_memory_category(self, memory_id: str, new_category: str) -> bool:
        """Updates category metadata of a cold memory record without modifying other fields."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT metadata_json FROM cold_memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            if not row:
                return False
            meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
            meta["category"] = new_category
            cursor.execute("""
                UPDATE cold_memories
                SET category = ?, metadata_json = ?
                WHERE id = ?
            """, (new_category, json.dumps(meta), memory_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT COUNT(*) as count FROM cold_memories WHERE user_id = ?", (user_id,))
            else:
                cursor.execute("SELECT COUNT(*) as count FROM cold_memories")
            row = cursor.fetchone()
            return {"cold_archived_count": row["count"] if row else 0}
