from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core import clock
from app.embeddings.encoder import get_embedding
from app.memory.chroma import search_memory, update_access_count
from app.memory.ranker import MemoryRanker
from app.memory.classifier import MemoryClassifier
from app.memory.bm25 import BM25Retriever
from app.memory.archive_storage import ColdArchiveStorage
from app.memory.working_memory import WorkingMemory


def is_historical_query(query: str) -> bool:
    q_lower = query.lower()
    historical_keywords = [
        "before", "previously", "previous", "earlier", "past", "used to",
        "originally", "formerly", "prior", "where did i live", "what was my previous",
        "what was my old", "where did i reside"
    ]
    return any(k in q_lower for k in historical_keywords)


class MemoryRetriever:
    """
    3-Stage Hierarchical OS Memory Retriever with Relevance Gating & Tier Promotions:
      Stage 1: Search L1 Working Memory (Fast RAM Buffer)
      Stage 2: Search L2 Active Vector Memory (ChromaDB)
      Stage 3: Search L3 Cold Disk Archive (SQLite)
    """

    def __init__(
        self,
        working_memory: Optional[WorkingMemory] = None,
        archive_storage: Optional[ColdArchiveStorage] = None
    ):
        self.ranker = MemoryRanker()
        self.classifier = MemoryClassifier()
        self.bm25 = BM25Retriever()
        self.working_memory = working_memory
        self.archive_storage = archive_storage or ColdArchiveStorage()

    def set_working_memory(self, wm: WorkingMemory):
        self.working_memory = wm

    def retrieve(self, message: str, user_id: str = "default_user", min_results: int = 1) -> List[Dict[str, Any]]:
        category = self.classifier.classify(message)
        unified_memories = []
        seen_ids = set()

        is_historical = is_historical_query(message)

        # Stage 1: Search L1 Working Memory RAM Buffer first
        if self.working_memory:
            l1_hits = self.working_memory.search_l1(query=message, user_id=user_id)
            for mem in l1_hits:
                mem_id = mem.get("id")
                if mem_id and mem_id not in seen_ids:
                    seen_ids.add(mem_id)
                    unified_memories.append(self._normalize_memory_format(mem, default_tier="L1"))

        # Stage 2: Search L2 Active ChromaDB Vector Store
        embedding = get_embedding(message)
        l2_memories = search_memory(
            embedding=embedding,
            n_results=10,
            include_superseded=is_historical,
            user_id=user_id
        )

        for mem in l2_memories:
            mem_id = mem.get("id")
            if mem_id and mem_id not in seen_ids:
                seen_ids.add(mem_id)
                unified_memories.append(self._normalize_memory_format(mem, default_tier="L2"))


        # Stage 3: If L2 is insufficient, search L3 SQLite Cold Storage Archive
        if len(unified_memories) < min_results:
            l3_memories = self.archive_storage.search_l3(query=message, user_id=user_id)
            for mem in l3_memories:
                mem_id = mem.get("id")
                if mem_id and mem_id not in seen_ids:
                    seen_ids.add(mem_id)
                    unified_memories.append(self._normalize_memory_format(mem, default_tier="L3"))

        if not unified_memories:
            return []

        # Sparse BM25 Scoring & Dynamic Reranking
        scored_docs = self.bm25.score_documents(query=message, documents=unified_memories)
        ranked_memories = self.ranker.rank(memories=scored_docs, query=message)

        # Apply Strict Relevance Threshold Filtering
        accepted_memories, rejected_memories = self.ranker.filter_by_relevance(ranked_memories, query=message)

        # Access Count Update & L1 Promotion for Frequently Accessed Active Memories
        for memory in accepted_memories:
            meta = memory.get("metadata", {})
            meta["last_accessed_at"] = clock.get_now().isoformat()
            mem_id = memory.get("id")

            if meta.get("tier") in ["L2", "long_term"]:
                new_cnt = update_access_count(mem_id)
                meta["access_count"] = new_cnt
                if new_cnt >= 2 and self.working_memory:
                    self.working_memory.promote_to_l1(memory)
                    print(f"[TIER] Promoted {mem_id[:8]} L2 -> L1 (Access Count: {new_cnt})")
            else:
                meta["access_count"] = int(meta.get("access_count", 0)) + 1

        return accepted_memories

    def _normalize_memory_format(self, mem: Dict[str, Any], default_tier: str = "L2") -> Dict[str, Any]:
        """Normalizes results from all 3 tiers into unified schema before ranking."""
        mem_id = mem.get("id", "")
        doc = mem.get("document", "")
        meta = dict(mem.get("metadata") or {})
        now_iso = clock.get_now().isoformat()

        meta.update({
            "id": mem_id,
            "category": meta.get("category", "Fact"),
            "importance": float(meta.get("importance", 0.5)),
            "access_count": int(meta.get("access_count", 0)),
            "created_at": meta.get("created_at", now_iso),
            "last_accessed_at": meta.get("last_accessed_at", now_iso),
            "tier": meta.get("tier", default_tier),
            "status": meta.get("status", "active"),
            "superseded_by": meta.get("superseded_by", "")
        })

        return {
            "id": mem_id,
            "document": doc,
            "metadata": meta,
            "score": mem.get("score", 0.5),
            "distance": mem.get("distance", 1.0)
        }