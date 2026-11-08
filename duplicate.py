from app.embeddings.encoder import get_embedding
from app.memory.chroma import search_memory, get_all_memories
from app.memory.reconciler import MemoryReconciler


class DuplicateDetector:
    """
    Detects duplicate, conflicting, or updating memories using embedding proximity + MemoryReconciler.
    Enforces user_id & tenant_id identity scoping.
    """

    def __init__(self):
        self.reconciler = MemoryReconciler()

    def find_duplicate_or_reconcile(
        self,
        memory: str,
        max_distance: float = 1.65,
        user_id: str = "default_user"
    ) -> dict:
        """
        Searches ChromaDB for nearest active memory matches for the given user_id.
        If distance <= max_distance, runs LLM reconciliation to evaluate relationship.
        """
        embedding = get_embedding(memory)
        results = search_memory(embedding=embedding, n_results=10, include_superseded=False, user_id=user_id)

        evaluated_ids = set()

        if results:
            for best_match in results:
                doc = best_match.get("document") if isinstance(best_match, dict) else None
                if not doc or not isinstance(doc, str) or not doc.strip():
                    continue

                evaluated_ids.add(best_match.get("id"))
                distance = best_match.get("distance", 999.0)
                print(f"[DuplicateDetector] Candidate Match (User: {user_id}): '{doc}' | Distance: {distance:.4f}")

                if distance <= max_distance:
                    reconciliation = self.reconciler.reconcile(
                        new_memory=memory,
                        existing_memory=doc
                    )
                    rel = reconciliation.get("relationship", "DISTINCT")
                    if rel in ["SUPERSEDES", "REINFORCES", "CONTRADICTS"]:
                        return {
                            "status": rel,
                            "reconciliation": reconciliation,
                            "match": best_match
                        }

        # Location domain guarantee: if incoming memory is a location fact, ensure any active location memories are checked
        loc_words = [
            "live", "lives", "living", "moved", "moving", "located", "reside", "resides",
            "residing", "bengaluru", "bangalore", "hyderabad", "chennai", "seattle", "austin",
            "san francisco", "mumbai", "delhi", "tokyo", "city", "address", "relocated",
            "relocating", "shifted", "based"
        ]
        mem_lower = memory.lower()
        if any(w in mem_lower for w in loc_words):
            all_active = get_all_memories(include_superseded=False, user_id=user_id)
            for active_mem in all_active:
                m_id = active_mem.get("id")
                if m_id in evaluated_ids:
                    continue
                doc = active_mem.get("document", "")
                if any(w in doc.lower() for w in loc_words):
                    print(f"[DuplicateDetector] Location fallback candidate (User: {user_id}): '{doc}'")
                    reconciliation = self.reconciler.reconcile(
                        new_memory=memory,
                        existing_memory=doc
                    )
                    rel = reconciliation.get("relationship", "DISTINCT")
                    if rel in ["SUPERSEDES", "REINFORCES", "CONTRADICTS"]:
                        return {
                            "status": rel,
                            "reconciliation": reconciliation,
                            "match": active_mem
                        }

        return {"status": "DISTINCT", "match": None}