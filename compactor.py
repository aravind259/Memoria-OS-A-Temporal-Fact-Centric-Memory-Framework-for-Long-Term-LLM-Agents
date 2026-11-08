from typing import Dict, Any, List, Optional
from app.memory.adaptive_decay import AdaptiveDecayEngine
from app.memory.archive_storage import ColdArchiveStorage
from app.memory.chroma import get_all_memories, delete_memory

class OSMemoryCompactor:
    """
    OS Memory Compactor & Garbage Collector:
    Monitors active vector RAM usage, identifies decayed/superseded memories,
    and safely pages them out to Cold Disk Archive storage (SQLite).
    Reclaims active memory vector space ONLY after successful L3 archival.
    """

    def __init__(self, archive_storage: Optional[ColdArchiveStorage] = None):
        self.decay_engine = AdaptiveDecayEngine()
        self.archive_storage = archive_storage or ColdArchiveStorage()

    def run_garbage_collection(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans active vector memories, evaluates retention decay scores,
        pages out low retention / superseded items to Cold SQLite storage, and reclaims RAM.
        Guarantees Archival-First Safety: L2 copy is deleted ONLY after L3 write succeeds.
        """
        active_memories = get_all_memories(include_superseded=True, user_id=user_id)
        
        paged_out_count = 0
        paged_out_details = []
        failed_archival_count = 0

        for mem in active_memories:
            mem_id = mem.get("id")
            meta = mem.get("metadata", {})
            created_at = meta.get("created_at", "")
            importance = float(meta.get("importance", 0.5))
            access_count = int(meta.get("access_count", 0))
            category = meta.get("category", "Fact")
            status = meta.get("status", "active")
            
            # Compute retention decay score
            retention_score = self.decay_engine.calculate_retention(
                created_at_iso=created_at,
                importance=importance,
                access_count=access_count,
                category=category
            )

            # Check if this memory block should be paged out to cold archive
            should_archive = self.decay_engine.should_page_out_to_cold_archive(
                retention_score=retention_score,
                status=status,
                importance=importance
            )

            if should_archive:
                mem["metadata"]["retention_at_archive"] = retention_score
                mem["metadata"]["tier"] = "L3"

                # 1. Save to SQLite Cold Storage Archive FIRST
                archived_successfully = self.archive_storage.archive_memory(mem)
                
                # 2. Reclaim L2 Vector RAM ONLY if L3 archival succeeded
                if archived_successfully:
                    delete_memory(mem_id)
                    paged_out_count += 1
                    paged_out_details.append({
                        "id": mem_id,
                        "document": mem.get("document"),
                        "status": status,
                        "retention_score": retention_score,
                        "reason": "SUPERSEDED" if status == "superseded" else "DECAYED_RETENTION"
                    })
                else:
                    print(f"[OSMemoryCompactor] CRITICAL: Archival to L3 failed for ID {mem_id}. Preserving L2 copy.")
                    failed_archival_count += 1

        return {
            "status": "COMPACTION_COMPLETE",
            "total_scanned": len(active_memories),
            "paged_out_count": paged_out_count,
            "failed_archival_count": failed_archival_count,
            "reclaimed_vector_slots": paged_out_count,
            "paged_out_details": paged_out_details
        }
