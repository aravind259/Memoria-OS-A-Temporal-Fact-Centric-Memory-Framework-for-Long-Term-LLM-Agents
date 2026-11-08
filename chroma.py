import uuid
from datetime import datetime
from app.core import clock
from typing import List, Dict, Any, Optional
import chromadb

client = chromadb.PersistentClient(path="memory_db")

collection = client.get_or_create_collection(
    name="conversation_memory"
)


def save_memory(
    memory: str,
    embedding,
    category: str,
    importance: float,
    status: str = "active",
    superseded_by: str = None,
    user_id: str = "default_user",
    tenant_id: str = "default_tenant",
    tier: str = "L2",
    modality: str = "text",
    image_url: str = "",
    visual_summary: str = "",
    memory_id: str = None,
    created_at: str = None
) -> str:
    memory_id = memory_id or str(uuid.uuid4())
    collection.add(
        ids=[memory_id],
        documents=[memory],
        embeddings=[embedding],
        metadatas=[{
            "id": memory_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "tier": tier,
            "category": category,
            "importance": importance,
            "created_at": created_at or clock.get_now().isoformat(),
            "access_count": 0,
            "status": status,
            "superseded_by": superseded_by or "",
            "modality": modality,
            "image_url": image_url or "",
            "visual_summary": visual_summary or ""
        }]
    )
    return memory_id


def mark_memory_superseded(old_memory_id: str, new_memory_id: str):
    """
    Marks an existing memory as superseded by a newer memory.
    """
    existing = collection.get(
        ids=[old_memory_id],
        include=["documents", "embeddings", "metadatas"]
    )
    if existing and existing.get("metadatas"):
        metadata = existing["metadatas"][0]
        metadata["status"] = "superseded"
        metadata["superseded_by"] = new_memory_id
        metadata["superseded_at"] = clock.get_now().isoformat()

        collection.update(
            ids=[old_memory_id],
            documents=existing["documents"],
            embeddings=existing["embeddings"],
            metadatas=[metadata]
        )
        print(f"[ChromaDB] Marked memory {old_memory_id} as SUPERSEDED by {new_memory_id}")


def update_memory(
    memory_id: str,
    memory: str,
    embedding,
    metadata: dict
):
    collection.update(
        ids=[memory_id],
        documents=[memory],
        embeddings=[embedding],
        metadatas=[metadata]
    )


def delete_memory(memory_id: str) -> bool:
    """Deletes a single memory by ID."""
    try:
        collection.delete(ids=[memory_id])
        return True
    except Exception as e:
        print(f"[ChromaDB] Error deleting memory {memory_id}: {e}")
        return False


def delete_user_memories(user_id: str) -> int:
    """
    GDPR Right-to-Forget API: Deletes all memory records belonging to a user.
    """
    try:
        results = collection.get(where={"user_id": user_id})
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            print(f"[ChromaDB] GDPR Right-To-Forget: Deleted {len(ids_to_delete)} memories for user '{user_id}'")
            return len(ids_to_delete)
        return 0
    except Exception as e:
        print(f"[ChromaDB] Error performing right-to-forget for user {user_id}: {e}")
        return 0


def export_user_memories(user_id: str = "default_user") -> List[Dict[str, Any]]:
    """Exports all stored memory entries for a user."""
    results = collection.get(
        where={"user_id": user_id},
        include=["documents", "metadatas"]
    )
    memories = []
    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    for memory_id, doc, meta in zip(ids, documents, metadatas):
        memories.append({
            "id": memory_id,
            "document": doc,
            "metadata": meta
        })
    return memories


def search_memory(
    embedding,
    n_results=15,
    category=None,
    include_superseded=False,
    user_id: str = "default_user"
):
    where_clause = {}
    if category and category != "Conversation":
        where_clause["category"] = category

    if not include_superseded:
        where_clause["status"] = "active"

    # Multi-tenant user isolation filter if specified
    if user_id:
        where_clause["user_id"] = user_id

    try:
        if where_clause:
            results = collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
        else:
            results = collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
    except Exception:
        # Fallback query if metadata filters fail on initial legacy entries
        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

    memories = []
    if not results or not results.get("ids") or len(results["ids"]) == 0:
        return memories

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for memory_id, doc, metadata, distance in zip(ids, documents, metadatas, distances):
        metadata = metadata or {}
        # Filter out superseded if status field exists
        if not include_superseded and metadata.get("status") == "superseded":
            continue

        memories.append({
            "id": memory_id,
            "document": doc,
            "metadata": metadata,
            "distance": distance
        })

    return memories


def update_access_count(memory_id: str) -> int:
    existing = collection.get(
        ids=[memory_id],
        include=["documents", "embeddings", "metadatas"]
    )
    if not existing or not existing.get("metadatas"):
        return 1

    metadata = existing["metadatas"][0] or {}
    new_count = int(metadata.get("access_count", 0)) + 1
    metadata["access_count"] = new_count
    metadata["last_accessed_at"] = clock.get_now().isoformat()

    collection.update(
        ids=[memory_id],
        documents=existing["documents"],
        embeddings=existing["embeddings"],
        metadatas=[metadata]
    )
    return new_count


def get_all_memories(include_superseded=False, user_id: Optional[str] = None):
    where_clause = {}
    if user_id:
        where_clause["user_id"] = user_id

    if where_clause:
        results = collection.get(where=where_clause, include=["documents", "metadatas"])
    else:
        results = collection.get(include=["documents", "metadatas"])

    memories = []
    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    for memory_id, doc, meta in zip(ids, documents, metadatas):
        meta = meta or {}
        if not include_superseded and meta.get("status") == "superseded":
            continue
        memories.append({
            "id": memory_id,
            "document": doc,
            "metadata": meta
        })

    return memories


def get_memory_stats(user_id: Optional[str] = None) -> Dict[str, Any]:
    all_mem = get_all_memories(include_superseded=True, user_id=user_id)
    active_count = sum(1 for m in all_mem if m.get("metadata", {}).get("status") != "superseded")
    superseded_count = sum(1 for m in all_mem if m.get("metadata", {}).get("status") == "superseded")
    
    categories = {}
    for m in all_mem:
        cat = m.get("metadata", {}).get("category", "Uncategorized")
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "total_memories": len(all_mem),
        "active_memories": active_count,
        "superseded_memories": superseded_count,
        "categories": categories
    }


def clear_all_memories():
    """Wipes collection clean (for testing and verification)."""
    all_m = collection.get()
    ids = all_m.get("ids", [])
    if ids:
        collection.delete(ids=ids)