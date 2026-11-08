"""
Background Memory Lifecycle Scheduler for Memory OS
Periodically monitors memory retention decay, pages out stale/superseded memories to L3 Cold Archive,
preserves high-importance facts, and operates in a non-blocking background asyncio loop.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core import clock

from app.core import config
from app.memory.adaptive_decay import AdaptiveDecayEngine
from app.memory.compactor import OSMemoryCompactor
from app.memory.archive_storage import ColdArchiveStorage
from app.memory.tier_manager import MemoryTierManager
from app.memory.chroma import get_all_memories, delete_memory

logger = logging.getLogger("memory_os.scheduler")
logging.basicConfig(level=logging.INFO)


class MemoryLifecycleScheduler:
    """
    Background Lifecycle Scheduler Engine:
    Configurable, non-blocking background loop that enforces memory retention decay,
    pages out stale/superseded items to cold storage, protects high-importance memories,
    and supports restoration/promotion.
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        interval_seconds: Optional[float] = None,
        decay_threshold: Optional[float] = None,
        important_threshold: Optional[float] = None,
        archive_storage: Optional[ColdArchiveStorage] = None,
        working_memory=None
    ):
        self.enabled = enabled if enabled is not None else config.LIFECYCLE_SCHEDULER_ENABLED
        self.interval_seconds = interval_seconds if interval_seconds is not None else config.LIFECYCLE_INTERVAL_SECONDS
        self.decay_threshold = decay_threshold if decay_threshold is not None else config.LIFECYCLE_DECAY_THRESHOLD
        self.important_threshold = important_threshold if important_threshold is not None else config.LIFECYCLE_IMPORTANT_THRESHOLD

        self.decay_engine = AdaptiveDecayEngine()
        self.archive_storage = archive_storage or ColdArchiveStorage()
        self.compactor = OSMemoryCompactor(archive_storage=self.archive_storage)
        self.tier_manager = MemoryTierManager(working_memory=working_memory, archive_storage=self.archive_storage)

        self._task: Optional[asyncio.Task] = None
        self._running = False
        self.cycle_count = 0
        self.last_run_at: Optional[str] = None

    def start(self):
        """Starts the background scheduler task loop in non-blocking mode."""
        if not self.enabled:
            logger.info("[LifecycleScheduler] Scheduler is DISABLED in configuration.")
            return

        if self._running or (self._task and not self._task.done()):
            logger.info("[LifecycleScheduler] Scheduler is already running.")
            return

        self._running = True
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._background_loop())
            logger.info(f"[LifecycleScheduler] Background scheduler STARTED (interval={self.interval_seconds}s).")
        except RuntimeError:
            # If no running event loop, loop will be launched when event loop starts
            logger.info("[LifecycleScheduler] Event loop not currently active. Will launch on startup event.")

    def stop(self):
        """Gracefully stops the background scheduler task."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("[LifecycleScheduler] Background scheduler STOPPED.")

    async def _background_loop(self):
        """Internal background loop running periodically without blocking FastAPI handlers."""
        logger.info("[LifecycleScheduler] Entering background execution loop...")
        while self._running:
            try:
                await asyncio.sleep(self.interval_seconds)
                if not self._running:
                    break
                self.run_lifecycle_cycle()
            except asyncio.CancelledError:
                logger.info("[LifecycleScheduler] Background loop cancelled.")
                break
            except Exception as e:
                logger.error(f"[LifecycleScheduler] Error during background cycle execution: {e}", exc_info=True)

    def run_lifecycle_cycle(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes one full memory lifecycle sweep:
          1. Scans active memories in ChromaDB.
          2. Computes adaptive retention decay scores using AdaptiveDecayEngine.
          3. Identifies stale vs preserved memories (high importance >= threshold protected).
          4. Pages out eligible decayed/superseded memories to L3 Cold Archive (SQLite).
          5. Reclaims active vector store slots after safe L3 write.
        """
        self.cycle_count += 1
        self.last_run_at = clock.get_now().isoformat()
        logger.info(f"[LifecycleScheduler] --- Starting Cycle #{self.cycle_count} at {self.last_run_at} ---")

        try:
            active_memories = get_all_memories(include_superseded=True, user_id=user_id)
        except Exception as e:
            logger.error(f"[LifecycleScheduler] Failed to fetch active memories: {e}")
            return {"status": "ERROR", "reason": str(e), "cycle": self.cycle_count}

        total_scanned = len(active_memories)
        stale_detected = []
        preserved_important = []
        paged_out_count = 0
        failed_archival = 0

        for mem in active_memories:
            mem_id = mem.get("id")
            doc = mem.get("document", "")
            meta = mem.get("metadata", {})

            importance = float(meta.get("importance", 0.5))
            access_count = int(meta.get("access_count", 0))
            category = meta.get("category", "Fact")
            status = meta.get("status", "active")
            created_at = meta.get("created_at", "")

            # 1. Compute retention decay score using existing AdaptiveDecayEngine
            retention = self.decay_engine.calculate_retention(
                created_at_iso=created_at,
                importance=importance,
                access_count=access_count,
                category=category
            )

            # 2. Protection Rule: High importance facts (>= important_threshold) or frequently accessed memories are preserved
            is_important_or_reinforced = (importance >= self.important_threshold or access_count >= 2)

            if is_important_or_reinforced and status == "active":
                preserved_important.append({
                    "id": mem_id,
                    "document": doc,
                    "importance": importance,
                    "retention": retention,
                    "reason": "HIGH_IMPORTANCE_PRESERVED"
                })
                continue

            # 3. Check if memory is stale or superseded
            should_page_out = self.decay_engine.should_page_out_to_cold_archive(
                retention_score=retention,
                status=status,
                importance=importance
            )

            if should_page_out:
                stale_detected.append(mem_id)
                mem["metadata"]["retention_at_archive"] = retention
                mem["metadata"]["tier"] = "L3"

                # 4. Transactional L2 -> L3 Archival: Write to L3 SQLite FIRST
                archived_ok = self.archive_storage.archive_memory(mem)
                if archived_ok:
                    delete_memory(mem_id)
                    paged_out_count += 1
                    logger.info(f"[LifecycleScheduler] ACTION: Paged out memory '{mem_id[:8]}' to L3 Cold Storage (Status: {status}, Retention: {retention:.4f})")
                else:
                    failed_archival += 1
                    logger.error(f"[LifecycleScheduler] FAILURE RECOVERY: L3 Archival failed for '{mem_id[:8]}'. Preserving L2 copy.")

        result_summary = {
            "status": "SUCCESS",
            "cycle": self.cycle_count,
            "timestamp": self.last_run_at,
            "total_scanned": total_scanned,
            "stale_detected_count": len(stale_detected),
            "preserved_important_count": len(preserved_important),
            "paged_out_count": paged_out_count,
            "failed_archival_count": failed_archival
        }

        logger.info(f"[LifecycleScheduler] Cycle #{self.cycle_count} COMPLETE: Scanned={total_scanned}, Stale={len(stale_detected)}, Preserved={len(preserved_important)}, ArchivalSuccess={paged_out_count}")
        return result_summary

    def restore_cold_memory(self, memory_id: str, promote_l1: bool = True) -> Optional[Dict[str, Any]]:
        """
        Restores a cold memory record from L3 SQLite archive back into L2 ChromaDB & L1 RAM when queried.
        """
        restored = self.tier_manager.restore_from_l3(memory_id, promote_l1=promote_l1)
        if restored:
            logger.info(f"[LifecycleScheduler] ACTION: Restored cold memory '{memory_id[:8]}' L3 -> L2/L1.")
        return restored
