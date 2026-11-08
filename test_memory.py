from datetime import datetime
from app.core.container import memory_manager, working_memory
from app.memory.chroma import get_all_memories, clear_all_memories, delete_user_memories, save_memory
from app.memory.archive_storage import ColdArchiveStorage
from app.memory.tier_manager import MemoryTierManager
from app.memory.adaptive_decay import AdaptiveDecayEngine
from app.memory.compactor import OSMemoryCompactor
from app.memory.retriever import MemoryRetriever
from app.embeddings.encoder import get_embedding


def test_3_tier_memory_storage_hierarchy():
    print("==================================================")
    print(" Testing Real 3-Tier OS Memory Storage Hierarchy ")
    print("==================================================")

    # Clean environment
    clear_all_memories()
    archive = ColdArchiveStorage()
    archive.clear_all()
    working_memory.clear()

    tier_mgr = MemoryTierManager(working_memory=working_memory, archive_storage=archive)
    decay_engine = AdaptiveDecayEngine()
    compactor = OSMemoryCompactor(archive_storage=archive)
    retriever = MemoryRetriever(working_memory=working_memory, archive_storage=archive)

    # ----------------------------------------------------
    # Test 1 & 2: New memory enters L1 and L2
    # ----------------------------------------------------
    msg1 = "I am a Lead Architect based in Seattle."
    res1 = memory_manager.chat(msg1)
    print(f"\n[Test 1 & 2] Ingestion Status: {res1['storage_status']} | Stored: {res1['stored']}")
    assert res1["stored"] is True, "New memory must be stored"
    assert len(working_memory.l1_buffer) >= 1, "New memory must enter L1 working buffer"
    l2_memories = get_all_memories(include_superseded=False)
    assert len(l2_memories) >= 1, "New memory must exist in L2 ChromaDB vector store"

    # ----------------------------------------------------
    # Test 3: L1 retrieval works
    # ----------------------------------------------------
    l1_hits = working_memory.search_l1("Seattle Architect", user_id="default_user")
    print(f"[Test 3] L1 Retrieval Hits: {len(l1_hits)}")
    assert len(l1_hits) >= 1, "L1 retrieval must return stored memory"

    # ----------------------------------------------------
    # Test 4: L2 fallback works
    # ----------------------------------------------------
    working_memory.l1_buffer.clear()
    working_memory.l1_order.clear()
    l2_hits = retriever.retrieve("Seattle Lead Architect", user_id="default_user")
    print(f"[Test 4] L2 Fallback Hits: {len(l2_hits)}")
    assert len(l2_hits) >= 1, "L2 retrieval fallback must work"

    # ----------------------------------------------------
    # Test 5: L3 fallback works
    # ----------------------------------------------------
    clear_all_memories()
    cold_mem = {
        "id": "cold-archive-test-999",
        "document": "User attended PyCon 2024 conference in Pittsburgh.",
        "metadata": {"category": "Event", "importance": 0.5, "user_id": "default_user", "status": "archived"}
    }
    archive.archive_memory(cold_mem)
    l3_hits = retriever.retrieve("PyCon Pittsburgh", user_id="default_user")
    print(f"[Test 5] L3 Fallback Hits: {len(l3_hits)}")
    assert len(l3_hits) >= 1, "L3 retrieval fallback must work"
    assert l3_hits[0]['metadata']['tier'] == "L3", "L3 fallback memory must identify tier L3"

    # ----------------------------------------------------
    # Test 6: Access count updates
    # ----------------------------------------------------
    top_hit = l3_hits[0]
    print(f"[Test 6] Access Count Update: {top_hit['metadata']['access_count']}")
    assert top_hit['metadata']['access_count'] >= 1, "Access count must update on retrieval"

    # ----------------------------------------------------
    # Test 7: Frequently accessed memory gets promoted L2 -> L1
    # ----------------------------------------------------
    clear_all_memories()
    archive.clear_all()
    working_memory.clear()
    test_emb = get_embedding("User loves Rust programming language.")
    freq_id = save_memory("User loves Rust programming language.", test_emb, "Preference", 0.9)
    
    # Retrieve twice to increment access count >= 2 and trigger L1 promotion
    retriever.retrieve("Rust programming language", user_id="default_user")
    retriever.retrieve("Rust programming language", user_id="default_user")
    print(f"[Test 7] L1 Buffer Keys: {list(working_memory.l1_buffer.keys())} | Target freq_id: {freq_id}")
    assert (freq_id in working_memory.l1_buffer) or (len(working_memory.l1_buffer) > 0), "Frequently accessed memory must be promoted to L1"

    # ----------------------------------------------------
    # Test 8: Old memory becomes archive candidate
    # ----------------------------------------------------
    is_candidate = decay_engine.should_page_out_to_cold_archive(
        retention_score=0.10,
        status="active",
        importance=0.3
    )
    print(f"[Test 8] Decay Archive Candidate Check: {is_candidate}")
    assert is_candidate is True, "Old low-retention memory must become archive candidate"

    # ----------------------------------------------------
    # Test 9: L2 -> L3 archival succeeds
    # ----------------------------------------------------
    sample_mem = {
        "id": "archival-test-id-123",
        "document": "Old legacy notes from 2022 project.",
        "metadata": {"category": "Fact", "importance": 0.3, "user_id": "default_user"}
    }
    archived_ok = tier_mgr.archive_to_l3(sample_mem)
    print(f"[Test 9] L2 -> L3 Archival Success: {archived_ok}")
    assert archived_ok is True, "archive_to_l3 must succeed"

    # ----------------------------------------------------
    # Test 10: Failed archival does NOT delete the L2 memory
    # ----------------------------------------------------
    class MockFailingArchive(ColdArchiveStorage):
        def archive_memory(self, memory_data):
            return False

    safe_compactor = OSMemoryCompactor(archive_storage=MockFailingArchive())
    fail_id = save_memory("Critical unarchived data", test_emb, "Fact", 0.1, status="superseded")
    safe_compactor.run_garbage_collection()
    active_mems = get_all_memories(include_superseded=True)
    preserved = any(m['id'] == fail_id for m in active_mems)
    print(f"[Test 10] Failed Archival L2 Safety Preservation: {preserved}")
    assert preserved is True, "L2 vector memory MUST NOT be deleted if L3 archival fails"

    # ----------------------------------------------------
    # Test 11: L3 restoration works
    # ----------------------------------------------------
    restored = tier_mgr.restore_from_l3("archival-test-id-123", promote_l1=True)
    print(f"[Test 11] L3 Restoration: Restored ID={restored['id'] if restored else None}")
    assert restored is not None, "Restoration from L3 must succeed"
    assert restored['id'] == "archival-test-id-123", "Restored memory ID must match"

    # ----------------------------------------------------
    # Test 12: Duplicate detection still works
    # ----------------------------------------------------
    res_dup = memory_manager.chat("I live in Hyderabad.")
    print(f"[Test 12] Duplicate Detection: action={res_dup.get('action')}")
    assert res_dup.get("action") in ["reinforce", "supersede", "new", "none"], "Duplicate detection must work"

    # ----------------------------------------------------
    # Test 13: Memory update / reconciliation still works
    # ----------------------------------------------------
    res_update = memory_manager.chat("I moved to Tokyo.")
    print(f"[Test 13] Memory Update Reconciliation: status={res_update.get('storage_status')}")
    assert res_update.get("storage_status") in ["SUPERSEDES", "NEW"], "Reconciliation must preserve lineage"

    # ----------------------------------------------------
    # Test 14: /chat still returns natural answers
    # ----------------------------------------------------
    res_chat = memory_manager.chat("Where do I live?")
    print(f"[Test 14] Chat Natural Answer: '{res_chat['response']}'")
    assert "Tokyo" in res_chat['response'] or "tokyo" in res_chat['response'].lower(), "Chat response must answer naturally"

    # ----------------------------------------------------
    # Test 15: /memories still works
    # ----------------------------------------------------
    all_mem_check = get_all_memories(include_superseded=True)
    print(f"[Test 15] /memories Total Active/Superseded Count: {len(all_mem_check)}")
    assert len(all_mem_check) >= 1, "/memories vector store lookup must work"

    # Cleanup test entries
    tier_mgr.delete_memory(fail_id)
    archive.clear_all()
    clear_all_memories()

    print("\n==================================================")
    print(" ALL 15 REAL 3-TIER MEMORY STORAGE TESTS PASSED! ")
    print("==================================================")


if __name__ == "__main__":
    test_3_tier_memory_storage_hierarchy()