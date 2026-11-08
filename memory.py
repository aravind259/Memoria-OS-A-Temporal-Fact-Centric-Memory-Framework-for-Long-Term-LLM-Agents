from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.memory.chroma import (
    get_all_memories,
    get_memory_stats,
    delete_memory,
    delete_user_memories,
    export_user_memories,
    clear_all_memories
)
from app.core.container import working_memory
from app.memory.persona import UserPersonaEngine
from app.memory.archive_storage import ColdArchiveStorage
from app.memory.compactor import OSMemoryCompactor

router = APIRouter()

persona_engine = UserPersonaEngine()
archive_storage = ColdArchiveStorage()
compactor = OSMemoryCompactor(archive_storage=archive_storage)


@router.get("/memories")
def memories(
    include_superseded: bool = Query(False, description="Include old superseded memory facts"),
    user_id: Optional[str] = Query(None, description="Filter by User ID")
):
    return get_all_memories(include_superseded=include_superseded, user_id=user_id)


@router.get("/memories/stats")
def stats(user_id: Optional[str] = Query(None, description="Filter stats by User ID")):
    long_term_stats = get_memory_stats(user_id=user_id)
    tier_summary = working_memory.get_all_tiers_summary()
    archive_stats = archive_storage.get_stats(user_id=user_id)
    return {
        "long_term": long_term_stats,
        "cold_archive": archive_stats,
        "working_memory_tiers": tier_summary
    }


@router.get("/memories/tiers")
def get_tiers():
    """Returns short-term working memory and mid-term episodic memory contents."""
    return {
        "short_term": working_memory.get_short_term_context(),
        "mid_term": working_memory.get_mid_term_summaries()
    }


@router.get("/memories/persona")
def get_persona(user_id: str = Query("default_user", description="User ID for persona synthesis")):
    """Returns synthesized User Persona Profile."""
    return persona_engine.synthesize_persona(user_id=user_id)


@router.get("/memories/suggestions")
def get_suggestions(user_id: str = Query("default_user", description="User ID for suggestions")):
    """Returns dynamic quick-action suggestions tailored to user's active persona and memories."""
    return persona_engine.generate_quick_action_suggestions(user_id=user_id)


@router.get("/memories/archive")
def get_archive(user_id: Optional[str] = Query(None, description="Filter archive by User ID")):
    """Returns all cold-archived memories stored in SQLite disk archive."""
    return archive_storage.get_archived_memories(user_id=user_id)


@router.post("/memories/compact")
def run_compaction(user_id: Optional[str] = Query(None, description="Filter compaction by User ID")):
    """Triggers OS Garbage Collection & Memory Compaction: pages out low retention/superseded memories to cold archive."""
    return compactor.run_garbage_collection(user_id=user_id)


@router.post("/memories/reclassify")
def run_reclassification(dry_run: bool = Query(False, description="Preview reclassification without writing")):
    """Safely audits and reclassifies existing memories across vector store and cold archive without data loss."""
    from app.memory.reclassify import reclassify_existing_memories
    return reclassify_existing_memories(dry_run=dry_run)


@router.delete("/memories/{memory_id}")
def remove_single_memory(memory_id: str):
    """Deletes a specific memory entry by ID."""
    success = delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory ID not found or could not be deleted")
    return {"status": "success", "deleted_id": memory_id}


@router.delete("/memories/user/{user_id}")
def right_to_forget(user_id: str):
    """GDPR Compliance: Purges all stored memory vectors, cold archives, and logs for the given user ID."""
    deleted_count = delete_user_memories(user_id=user_id)
    archived_deleted = archive_storage.delete_user_archive(user_id=user_id)
    working_memory.clear()
    return {
        "status": "success",
        "action": "RIGHT_TO_FORGET_EXECUTED",
        "user_id": user_id,
        "deleted_vector_count": deleted_count,
        "deleted_archive_count": archived_deleted
    }


@router.get("/memories/export/{user_id}")
def export_user_data(user_id: str):
    """Exports all stored memories for data portability."""
    user_memories = export_user_memories(user_id=user_id)
    cold_memories = archive_storage.get_archived_memories(user_id=user_id)
    return {
        "user_id": user_id,
        "exported_at": user_memories,
        "cold_archived": cold_memories,
        "total_records": len(user_memories) + len(cold_memories),
        "data": user_memories
    }


@router.post("/memories/clear")
def clear_all():
    """Clears all vector, working, and archive memory (for reset/testing)."""
    clear_all_memories()
    archive_storage.clear_all()
    working_memory.clear()
    return {"status": "success", "message": "All memories cleared across all OS tiers."}