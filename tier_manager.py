from datetime import datetime
from app.core import clock
from typing import Dict, Any, Optional, List
from app.memory.working_memory import WorkingMemory
from app.memory.chroma import (
    save_memory,
    search_memory,
    delete_memory as delete_l2_memory,
    get_all_memories
)
from app.memory.archive_storage import ColdArchiveStorage
from app.embeddings.encoder import get_embedding


class MemoryTierManager:
    """
    Explicit 3-Tier OS Storage Hierarchy Manager:
    Manages promotions, movements, archival, restoration, and deletion across:
      - L1: Working Memory / Fast RAM Buffer
      - L2: Active Vector Store / ChromaDB
      - L3: Cold Archive / SQLite Database
    """

    def __init__(
        self,
        working_memory: Optional[WorkingMemory] = None,
        archive_storage: Optional[ColdArchiveStorage] = None
    ):
        self.l1 = working_memory or WorkingMemory()
        self.l3 = archive_storage or ColdArchiveStorage()

    def promote_to_l1(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Promotes/caches a memory object into the L1 fast RAM buffer."""
        mem_id = memory.get("id", "")
        res = self.l1.promote_to_l1(memory)
        print(f"[TIER] Promoted {mem_id[:8]} L2 -> L1")
        return res

    def move_to_l2(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensures a memory is persisted in L2 ChromaDB vector store.
        """
        mem_id = memory.get("id")
        doc = memory.get("document", "")
        meta = dict(memory.get("metadata") or {})

        category = meta.get("category", "Fact")
        importance = float(meta.get("importance", 0.5))
        status = meta.get("status", "active")
        user_id = meta.get("user_id", "default_user")
        tenant_id = meta.get("tenant_id", "default_tenant")
        modality = meta.get("modality", "text")
        image_url = meta.get("image_url", "")
        visual_summary = meta.get("visual_summary", "")

        embedding = get_embedding(doc)

        new_id = save_memory(
            memory=doc,
            embedding=embedding,
            category=category,
            importance=importance,
            status=status,
            superseded_by=meta.get("superseded_by", ""),
            user_id=user_id,
            tenant_id=tenant_id,
            tier="L2",
            modality=modality,
            image_url=image_url,
            visual_summary=visual_summary,
            memory_id=mem_id
        )

        print(f"[TIER] Memory {new_id[:8]} -> L2")

        res = {
            "id": new_id,
            "document": doc,
            "metadata": {
                "id": new_id,
                "category": category,
                "importance": importance,
                "access_count": meta.get("access_count", 0),
                "created_at": meta.get("created_at", clock.get_now().isoformat()),
                "last_accessed_at": meta.get("last_accessed_at", clock.get_now().isoformat()),
                "tier": "L2",
                "status": status,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "superseded_by": meta.get("superseded_by", "")
            }
        }
        return res

    def archive_to_l3(self, memory: Dict[str, Any]) -> bool:
        """
        Archives a memory object into L3 SQLite cold storage.
        Returns True ONLY if SQLite write transaction completes successfully.
        """
        mem_id = memory.get("id", "")
        meta = dict(memory.get("metadata") or {})
        meta["tier"] = "L3"
        memory["metadata"] = meta
        success = self.l3.archive_memory(memory)
        if success:
            print(f"[TIER] Memory {mem_id[:8]} -> L3")
        return success

    def restore_from_l3(self, memory_id: str, promote_l1: bool = True) -> Optional[Dict[str, Any]]:
        """
        Restores a cold memory record from L3 SQLite archive back into L2 ChromaDB and optionally L1 RAM.
        """
        restored = self.l3.restore_memory(memory_id)
        if not restored:
            return None

        doc = restored.get("document", "")
        meta = restored.get("metadata", {})
        
        # Save back to L2 ChromaDB
        l2_res = self.move_to_l2(restored)
        print(f"[TIER] Restored {memory_id[:8]} L3 -> L2")

        # Optionally promote to L1 fast RAM
        if promote_l1:
            self.promote_to_l1(l2_res)

        return l2_res

    def delete_memory(self, memory_id: str) -> bool:
        """
        Explicit deletion: Purges memory entry across all OS tiers (L1, L2, and L3).
        """
        l1_deleted = self.l1.remove_from_l1(memory_id)
        l2_deleted = delete_l2_memory(memory_id)
        l3_deleted = self.l3.delete_memory(memory_id)
        return l1_deleted or l2_deleted or l3_deleted
