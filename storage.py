from app.embeddings.encoder import get_embedding
from app.memory.chroma import save_memory, mark_memory_superseded, update_access_count
from app.memory.classifier import MemoryClassifier
from app.memory.importance import MemoryImportance
from app.memory.extractor import MemoryExtractor
from app.memory.gate import MemoryGate
from app.memory.duplicate import DuplicateDetector
from app.memory.pii import PIIScrubber
from app.memory.multimodal import MultimodalMemoryProcessor


class MemoryStorage:
    """
    Patentable Multi-Tier Memory Storage Engine:
    Handles PII sanitization, semantic classification, dynamic importance scoring,
    LLM gating, distillation extraction, contradiction resolution, multimodal processing, and persistence.
    """

    def __init__(self):
        self.classifier = MemoryClassifier()
        self.importance = MemoryImportance()
        self.extractor = MemoryExtractor()
        self.gate = MemoryGate()
        self.duplicate = DuplicateDetector()
        self.pii_scrubber = PIIScrubber()
        self.multimodal = MultimodalMemoryProcessor()

    def store(
        self,
        user_message: str,
        ai_response: str,
        user_id: str = "default_user",
        tenant_id: str = "default_tenant",
        image_url: str = None,
        image_b64: str = None
    ):
        # Step 0: PII Detection & Sanitization
        pii_res = self.pii_scrubber.sanitize(user_message)
        clean_user_msg = pii_res["clean_text"]
        has_pii = pii_res["has_pii"]
        detected_pii = pii_res["detected_pii"]

        if has_pii:
            print(f"[MemoryStorage] PII Detected & Redacted ({detected_pii}): '{clean_user_msg}'")

        # Step 1: Question / Query Check (Do NOT store user questions as memories)
        msg_clean = clean_user_msg.strip().lower()
        is_question = (
            "?" in clean_user_msg or
            any(msg_clean.startswith(q) for q in [
                "where", "what", "who", "when", "why", "how", "tell me", "do i", "can you", "show me", "is it", "do u", "do you", "did you", "are you", "is there", "would you"
            ])
        )
        if is_question:
            print("[MemoryStorage] Rejected: Message is a query/question.")
            return {
                "category": "Conversation",
                "importance": 0.1,
                "stored": False,
                "reason": "User message is a query/question.",
                "has_pii": has_pii,
                "detected_pii": detected_pii
            }

        # Step 2: Semantic Classification
        category = self.classifier.classify(clean_user_msg)
        print(f"[MemoryStorage] Category: {category}")

        # Step 3: Importance Evaluation
        importance = self.importance.score(clean_user_msg)
        print(f"[MemoryStorage] Importance Score: {importance:.2f}")

        # Step 4: Heuristic Filter
        should_store = (
            importance >= 0.65 or
            category in ["Preference", "Fact", "Goal", "Project", "Skill", "Health"]
        )

        if not should_store:
            print("[MemoryStorage] Rejected: Low importance / conversational")
            return {
                "category": category,
                "importance": importance,
                "stored": False,
                "reason": "Low importance or temporary message.",
                "has_pii": has_pii,
                "detected_pii": detected_pii
            }

        # Step 5: Memory Gate (LLM Filter)
        try:
            gate_decision = self.gate.should_store(clean_user_msg)
            print(f"[MemoryStorage] Gate Decision: {gate_decision}")
            if not gate_decision.get("store", False):
                if "error" not in gate_decision.get("reason", "").lower():
                    return {
                        "category": category,
                        "importance": importance,
                        "stored": False,
                        "reason": gate_decision.get("reason", "Filtered by Memory Gate."),
                        "has_pii": has_pii,
                        "detected_pii": detected_pii
                    }
        except Exception as e:
            print(f"[MemoryStorage] Gate warning: {e}")

        # Step 6: Distillation & Multimodal Extraction
        mm_payload = self.multimodal.process_multimodal_input(
            text=clean_user_msg,
            image_url=image_url,
            image_b64=image_b64
        )
        modality = mm_payload.get("modality", "text")
        visual_summary = mm_payload.get("visual_summary", "")
        img_url = mm_payload.get("image_url", "")

        raw_fact = mm_payload.get("combined_text", clean_user_msg)
        memory = self.extractor.extract(raw_fact)
        print(f"[MemoryStorage] Extracted Fact (Modality: {modality}): '{memory}'")

        # Additional sanity check on extracted string
        if memory.lower().startswith("user statement: where") or memory.lower().startswith("user statement: what"):
            return {
                "category": category,
                "importance": importance,
                "stored": False,
                "reason": "Extracted text is a query.",
                "has_pii": has_pii,
                "detected_pii": detected_pii
            }

        # Step 7: Reconciliation & Duplicate Detection (Scoped to user_id)
        reconcile_res = self.duplicate.find_duplicate_or_reconcile(memory, user_id=user_id)
        status = reconcile_res.get("status", "DISTINCT")
        match = reconcile_res.get("match")

        if status == "REINFORCES" and match:
            print("[MemoryStorage] Memory reinforced existing knowledge. Incrementing access count.")
            update_access_count(match["id"])
            return {
                "category": category,
                "importance": importance,
                "stored": True,
                "status": "REINFORCED",
                "action": "reinforce",
                "memory": memory,
                "reinforced_id": match["id"],
                "has_pii": has_pii,
                "detected_pii": detected_pii
            }

        # Step 8: Generate Vector Embedding
        embedding = get_embedding(memory)

        # Step 9: Save Memory to ChromaDB (L2) & Promote to L1 Fast RAM
        new_memory_id = save_memory(
            memory=memory,
            embedding=embedding,
            category=category,
            importance=importance,
            status="active",
            user_id=user_id,
            tenant_id=tenant_id,
            modality=modality,
            image_url=img_url,
            visual_summary=visual_summary
        )

        try:
            from app.core.container import working_memory
            working_memory.promote_to_l1({
                "id": new_memory_id,
                "document": memory,
                "metadata": {
                    "id": new_memory_id,
                    "category": category,
                    "importance": importance,
                    "status": "active",
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "modality": modality,
                    "image_url": img_url
                }
            })
        except Exception as e:
            print(f"[MemoryStorage] L1 promotion warning: {e}")

        # Handle SUPERSEDES relationship
        if status == "SUPERSEDES" and match:
            print(f"[MemoryStorage] New memory supersedes existing memory ID: {match['id']}")
            mark_memory_superseded(old_memory_id=match["id"], new_memory_id=new_memory_id)

            # Evict superseded memory from L1 RAM buffer
            try:
                from app.core.container import working_memory
                working_memory.remove_from_l1(match["id"])
            except Exception as e:
                print(f"[MemoryStorage] L1 eviction warning: {e}")

            # If location memory was updated, ensure all previous active location memories for this user are marked superseded
            loc_words = [
                "live", "lives", "living", "moved", "moving", "located", "reside", "resides",
                "residing", "bengaluru", "bangalore", "hyderabad", "chennai", "seattle", "austin",
                "san francisco", "mumbai", "delhi", "tokyo", "city", "address", "relocated",
                "relocating", "shifted", "based"
            ]
            mem_lower = memory.lower()
            if any(w in mem_lower for w in loc_words):
                from app.memory.chroma import get_all_memories
                all_active = get_all_memories(include_superseded=False, user_id=user_id)
                for old_act in all_active:
                    o_id = old_act.get("id")
                    if o_id != new_memory_id:
                        o_doc = old_act.get("document", "").lower()
                        # Strictly target location memories; preserve name/skill/preference facts
                        if any(w in o_doc for w in loc_words) and not any(w in o_doc for w in ["name is", "name:", "called", "i am"]):
                            print(f"[MemoryStorage] Archiving previous active location memory: {o_id}")
                            mark_memory_superseded(old_memory_id=o_id, new_memory_id=new_memory_id)
                            try:
                                from app.core.container import working_memory
                                working_memory.remove_from_l1(o_id)
                            except Exception:
                                pass

        action_name = "supersede" if status == "SUPERSEDES" else "new"

        print(f"[MemoryStorage] Successfully persisted memory ID: {new_memory_id}")
        return {
            "category": category,
            "importance": importance,
            "stored": True,
            "status": status,
            "action": action_name,
            "memory_id": new_memory_id,
            "memory": memory,
            "has_pii": has_pii,
            "detected_pii": detected_pii
        }