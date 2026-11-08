from collections import deque
from datetime import datetime
from app.core import clock
from typing import List, Dict, Any, Optional


class WorkingMemory:
    """
    Hierarchical Memory System - L1 Working RAM & Short-Term Tier Engine.
    
    - L1 Working Memory Buffer: Low-latency fast RAM buffer of hot active long-term memories.
    - Short-Term: Sliding window buffer of raw conversation turns.
    - Mid-Term (Episodic): Session-level summaries.
    """

    def __init__(self, max_l1: int = 15, max_short_term: int = 10, max_mid_term: int = 20):
        self.max_l1 = max_l1
        self.max_short_term = max_short_term
        self.max_mid_term = max_mid_term
        
        self.l1_buffer: Dict[str, Dict[str, Any]] = {}  # Map of memory_id -> memory_dict
        self.l1_order = deque(maxlen=max_l1)
        
        self.short_term = deque(maxlen=max_short_term)
        self.mid_term = deque(maxlen=max_mid_term)
        self.session_started = clock.get_now().isoformat()

    def promote_to_l1(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """
        Promotes/inserts a memory record into the L1 fast RAM buffer.
        Maintains bounded max capacity using FIFO eviction when full.
        """
        mem_id = memory.get("id")
        if not mem_id:
            return memory

        doc = memory.get("document", "")
        meta = dict(memory.get("metadata") or {})
        now_iso = clock.get_now().isoformat()

        meta.update({
            "id": mem_id,
            "category": meta.get("category", "Fact"),
            "importance": float(meta.get("importance", 0.5)),
            "access_count": int(meta.get("access_count", 0)),
            "created_at": meta.get("created_at", now_iso),
            "last_accessed_at": now_iso,
            "tier": "L1",
            "status": meta.get("status", "active"),
            "superseded_by": meta.get("superseded_by", "")
        })

        l1_entry = {
            "id": mem_id,
            "document": doc,
            "metadata": meta,
            "score": memory.get("score", 1.0)
        }

        # Handle capacity eviction if new memory ID is added and buffer is full
        if mem_id not in self.l1_buffer and len(self.l1_order) >= self.max_l1:
            oldest_id = self.l1_order.popleft()
            self.l1_buffer.pop(oldest_id, None)

        self.l1_buffer[mem_id] = l1_entry
        if mem_id in self.l1_order:
            self.l1_order.remove(mem_id)
        self.l1_order.append(mem_id)

        return l1_entry

    def search_l1(self, query: str, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """
        Searches L1 Working Memory RAM buffer lexically for relevant active facts.
        """
        q_lower = query.lower()
        q_tokens = set(q_lower.split())
        results = []

        for mem_id in reversed(self.l1_order):
            mem = self.l1_buffer.get(mem_id)
            if not mem:
                continue
            
            meta = mem.get("metadata", {})
            if user_id and meta.get("user_id") and meta.get("user_id") != user_id:
                continue
            if meta.get("status") == "superseded":
                continue

            doc_lower = mem.get("document", "").lower()
            # Simple keyword hit relevance check
            if any(t in doc_lower for t in q_tokens if len(t) > 2) or q_lower in doc_lower:
                mem["metadata"]["last_accessed_at"] = clock.get_now().isoformat()
                mem["metadata"]["access_count"] = mem["metadata"].get("access_count", 0) + 1
                results.append(mem)

        return results

    def remove_from_l1(self, memory_id: str) -> bool:
        """Removes a memory entry from L1 working memory buffer."""
        if memory_id in self.l1_buffer:
            self.l1_buffer.pop(memory_id, None)
            if memory_id in self.l1_order:
                self.l1_order.remove(memory_id)
            return True
        return False

    def add_turn(self, user_message: str, ai_response: str, category: str = None, importance: float = 0.5):
        """Adds conversation turn to short-term working memory."""
        entry = {
            "timestamp": clock.get_now().isoformat(),
            "user": user_message,
            "assistant": ai_response,
            "category": category or "Conversation",
            "importance": importance
        }
        self.short_term.append(entry)

        if importance >= 0.7:
            self.mid_term.append({
                "timestamp": entry["timestamp"],
                "summary": f"[{category}] {user_message}",
                "importance": importance,
                "access_count": 1
            })


    def get_short_term_context(self) -> List[Dict[str, Any]]:
        return list(self.short_term)

    def get_mid_term_summaries(self) -> List[Dict[str, Any]]:
        return list(self.mid_term)

    def get_tier_stats(self) -> Dict[str, Any]:
        return {
            "l1_buffer_count": len(self.l1_buffer),
            "short_term_count": len(self.short_term),
            "mid_term_count": len(self.mid_term),
            "session_start": self.session_started
        }

    def get_all_tiers_summary(self) -> Dict[str, Any]:
        return self.get_tier_stats()

    def clear(self):
        self.l1_buffer.clear()
        self.l1_order.clear()
        self.short_term.clear()
        self.mid_term.clear()
        self.session_started = clock.get_now().isoformat()