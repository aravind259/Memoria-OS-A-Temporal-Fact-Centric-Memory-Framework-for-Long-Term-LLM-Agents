"""
Memory Reclassification & Safe Migration Service:
Inspects existing active, superseded, and cold archived memories,
identifies records needing reclassification (such as health statements
misclassified under Goal), and updates category metadata safely without deleting records.
"""

import sys
import os

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Dict, Any, List
from app.memory.classifier import MemoryClassifier
from app.memory.chroma import collection
from app.memory.archive_storage import ColdArchiveStorage


def reclassify_existing_memories(dry_run: bool = False) -> Dict[str, Any]:
    """
    Safely reclassifies existing memories across ChromaDB and ColdArchiveStorage.
    Preserves all memory IDs, documents, embeddings, and timestamps.
    """
    classifier = MemoryClassifier()
    archive_storage = ColdArchiveStorage()

    reclassified_chroma = []
    reclassified_archive = []

    # 1. ChromaDB Active/Superseded Memories
    all_chroma = collection.get(include=["documents", "embeddings", "metadatas"])
    ids = all_chroma.get("ids", [])
    documents = all_chroma.get("documents", [])
    embeddings = all_chroma.get("embeddings", [])
    metadatas = all_chroma.get("metadatas", [])

    for mem_id, doc, emb, meta in zip(ids, documents, embeddings, metadatas):
        meta = dict(meta or {})
        old_cat = meta.get("category", "Fact")
        new_cat = classifier.classify(doc)

        if new_cat != old_cat:
            reclassified_chroma.append({
                "id": mem_id,
                "document": doc,
                "old_category": old_cat,
                "new_category": new_cat
            })
            if not dry_run:
                meta["category"] = new_cat
                collection.update(
                    ids=[mem_id],
                    documents=[doc],
                    embeddings=[emb] if emb is not None else None,
                    metadatas=[meta]
                )

    # 2. Cold SQLite Archive Memories
    cold_mems = archive_storage.get_archived_memories()
    for cm in cold_mems:
        c_id = cm.get("id")
        doc = cm.get("document", "")
        old_cat = cm.get("metadata", {}).get("category", "Fact")
        new_cat = classifier.classify(doc)

        if new_cat != old_cat:
            reclassified_archive.append({
                "id": c_id,
                "document": doc,
                "old_category": old_cat,
                "new_category": new_cat
            })
            if not dry_run:
                archive_storage.update_memory_category(c_id, new_cat)

    total_updated = len(reclassified_chroma) + len(reclassified_archive)
    return {
        "status": "success",
        "dry_run": dry_run,
        "scanned_chroma": len(ids),
        "scanned_archive": len(cold_mems),
        "total_reclassified": total_updated,
        "chroma_changes": reclassified_chroma,
        "archive_changes": reclassified_archive
    }


if __name__ == "__main__":
    result = reclassify_existing_memories(dry_run=False)
    print("========================================")
    print(" MEMORY RECLASSIFICATION MIGRATION")
    print("========================================")
    print(f"Scanned ChromaDB: {result['scanned_chroma']}")
    print(f"Scanned Archive:  {result['scanned_archive']}")
    print(f"Reclassified:     {result['total_reclassified']}")
    print("Chroma changes:")
    for change in result["chroma_changes"]:
        print(f"  [{change['id'][:8]}] '{change['document']}': {change['old_category']} -> {change['new_category']}")
    print("========================================")
