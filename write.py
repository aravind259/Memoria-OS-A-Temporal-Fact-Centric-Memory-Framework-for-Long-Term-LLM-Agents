import uuid
from typing import Dict, Any, Optional
import chromadb

from app.core import clock
from app.embeddings.encoder import get_embedding
from app.memory_v2.facts import get_connection, init_db

# Initialize ChromaDB collection for facts_v2 and turns_v2
chroma_client = chromadb.PersistentClient(path="memory_db")
facts_collection = chroma_client.get_or_create_collection(name="facts_v2")
turns_collection = chroma_client.get_or_create_collection(name="turns_v2")

SINGLE_VALUED_ATTRS = {
    "home_city", "last_name", "first_name", "full_name", "job_title",
    "employer", "relationship_status", "birth_date", "current_residence",
    "marital_status", "company", "age"
}


def index_raw_turn(
    user_id: str,
    content: str,
    timestamp: str,
    turn_id: Optional[str] = None,
    source_role: str = "user"
):
    """
    Indexes every user turn as a raw chunk in Chroma collection turns_v2 with session date.
    """
    if not content or not str(content).strip():
        return

    tid = turn_id or str(uuid.uuid4())
    doc = str(content).strip()
    embedding = get_embedding(doc)

    turns_collection.upsert(
        ids=[tid],
        documents=[doc],
        embeddings=[embedding],
        metadatas=[{
            "id": tid,
            "user_id": user_id,
            "timestamp": str(timestamp),
            "role": source_role
        }]
    )


def write_fact(
    user_id: str,
    fact: Dict[str, Any],
    source_text: str = "",
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Rule-based persistence for facts with Cardinality and Deduplication:
      - cardinality == 'one':
          single-valued attributes (home_city, last_name, employer, etc.).
          Supersede previous active facts when value changes:
          set old.valid_to = new.valid_from and old.status = 'superseded'.
      - cardinality == 'many':
          multi-valued attributes (interests, activities, visited_place, skills, etc.).
          Deduplicate on exact (user_id, subject, attribute, value):
          if exact match exists, increment access_count and update last_accessed_at.
          If no exact match, append as active fact without superseding other values.
      - kind == 'event':
          events are multi-valued occurrences: appended and deduplicated on exact match.
      - embeds 'subject attribute value' and indexes into Chroma collection facts_v2.
    """
    init_db(db_path)

    subject = str(fact.get("subject", "user")).strip()
    attribute = str(fact.get("attribute", "")).strip().lower()
    value = str(fact.get("value", "")).strip()
    kind = str(fact.get("kind", "state")).strip().lower()
    if kind not in ("trait", "state", "event"):
        kind = "state"

    cardinality = str(fact.get("cardinality", "")).strip().lower()
    if cardinality not in ("one", "many"):
        cardinality = "one" if attribute in SINGLE_VALUED_ATTRS else "many"

    # Events are fundamentally multi-instance
    if kind == "event":
        cardinality = "many"

    valid_from = fact.get("valid_from")
    if not valid_from:
        valid_from = clock.get_now().isoformat()

    now_iso = clock.get_now().isoformat()

    with get_connection(db_path) as conn:
        cur = conn.cursor()

        # Check existing active facts with same user_id, subject, attribute
        cur.execute("""
            SELECT * FROM facts
            WHERE user_id = ? AND subject = ? AND attribute = ? AND status = 'active'
        """, (user_id, subject, attribute))
        existing_facts = cur.fetchall()

        # Check for exact duplicate (same value)
        matched_same_value = None
        for row in existing_facts:
            if row["value"].strip().lower() == value.lower():
                matched_same_value = row
                break

        if matched_same_value is not None:
            # Rule: exact duplicate -> increment access_count, update last_accessed_at
            cur.execute("""
                UPDATE facts
                SET access_count = access_count + 1, last_accessed_at = ?
                WHERE id = ?
            """, (now_iso, matched_same_value["id"]))
            conn.commit()
            return {
                "action": "DEDUPE_INCREMENT",
                "id": matched_same_value["id"],
                "status": "active",
                "access_count": matched_same_value["access_count"] + 1
            }

        # Value differs:
        if cardinality == "one":
            # Rule: single-valued attribute -> supersede previous active facts
            for row in existing_facts:
                cur.execute("""
                    UPDATE facts
                    SET valid_to = ?, status = 'superseded'
                    WHERE id = ?
                """, (valid_from, row["id"]))

        # Insert new active fact
        new_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO facts (
                id, user_id, subject, attribute, value, kind, cardinality, valid_from, valid_to,
                status, source_text, created_at, last_accessed_at, access_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 'active', ?, ?, ?, 1)
        """, (new_id, user_id, subject, attribute, value, kind, cardinality, valid_from, source_text, now_iso, now_iso))
        conn.commit()

        _embed_and_index(new_id, user_id, subject, attribute, value)
        return {
            "action": "SUPERSEDE_AND_INSERT" if (cardinality == "one" and existing_facts) else "INSERTED_NEW",
            "id": new_id,
            "status": "active",
            "cardinality": cardinality,
            "superseded_count": len(existing_facts) if cardinality == "one" else 0
        }


def _embed_and_index(fact_id: str, user_id: str, subject: str, attribute: str, value: str):
    """
    Embeds 'subject attribute value' with existing encoder and stores in Chroma collection facts_v2.
    """
    doc_text = f"{subject} {attribute} {value}"
    embedding = get_embedding(doc_text)

    facts_collection.upsert(
        ids=[fact_id],
        documents=[doc_text],
        embeddings=[embedding],
        metadatas=[{
            "id": fact_id,
            "user_id": user_id
        }]
    )
