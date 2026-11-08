import re
from app.memory.decay import EbbinghausDecayEngine
from app.core import clock


def classify_query_intent(query: str) -> str:
    """
    Classifies query intent before memory retrieval into fine-grained semantic categories:
      - PERSONAL_LOCATION: Where do I live?, My current city, Where do I reside?
      - PERSONAL_NAME: What is my name?, Who am I?
      - PREFERENCE: What programming language do I like?, My favorite food
      - PROJECT: What project am I building?, What is my goal?
      - SKILL: What are my technical skills?, Background/Experience
      - GENERAL_KNOWLEDGE: What languages are spoken in Hyderabad?, Capital of India, Explain X
      - CURRENT_INFORMATION: Weather, live external info
      - CONVERSATION: Casual greetings (Hello, Hi)
    """
    q_lower = query.lower().strip()

    # 1. CONVERSATION
    greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "greetings"]
    if any(q_lower == g or q_lower.startswith(g + " ") or q_lower.startswith(g + "!") or q_lower.startswith(g + ",") for g in greetings):
        return "CONVERSATION"

    # 2. GENERAL KNOWLEDGE (Languages in city, capital of, public facts)
    gk_phrases = [
        "languages", "language spoken", "languages are spoken", "languages does speak", "languages does speal",
        "capital of", "who invented", "who created", "who discovered", "who was", "who is the president",
        "who is the prime minister", "what is the population", "what is the currency", "explain", "how does", "what causes"
    ]
    if any(phrase in q_lower for phrase in gk_phrases):
        if not any(personal_term in q_lower for personal_term in ["i speak", "i like", "my language", "my preference"]):
            return "GENERAL_KNOWLEDGE"

    # 3. HISTORICAL LOCATION (Prior/previous living locations)
    historical_loc_phrases = [
        "where did i live before", "where did i live previously", "where did i live earlier",
        "where did i used to live", "where i lived before", "where was i living before",
        "where was i located before", "what was my previous location", "what was my old city",
        "previous location", "prior location", "where did i live", "where i lived",
        "where did i reside before", "where was i before"
    ]
    if any(phrase in q_lower for phrase in historical_loc_phrases) or (
        any(w in q_lower for w in ["before", "previously", "earlier", "past", "used to", "prior"]) and
        any(w in q_lower for w in ["live", "lived", "living", "located", "reside", "resided", "stay", "stayed"])
    ):
        return "HISTORICAL_LOCATION"

    # 4. PERSONAL LOCATION (Current living location)
    if any(phrase in q_lower for phrase in [
        "where do i", "where am i", "my location", "my address", "my home", "where i live", "where i do live", "where do i live", "my city", "reside", "where do i reside"
    ]):
        return "PERSONAL_LOCATION"

    # 5. PERSONAL NAME
    if any(phrase in q_lower for phrase in ["my name", "who am i", "what is my name", "what's my name", "do you know my name"]):
        return "PERSONAL_NAME"

    # 5. PREFERENCE
    if any(phrase in q_lower for phrase in ["preference", "preferences", "prefer", "prefers", "favorite", "favourite", "language do i like", "programming language do i", "what do i like", "what programming language"]):
        return "PREFERENCE"

    # 6. PROJECT / GOAL
    if any(phrase in q_lower for phrase in ["goal", "goals", "target", "aim", "project", "projects", "building", "work toward", "working toward", "what project", "my project"]):
        return "PROJECT"

    # 7. SKILL / BACKGROUND
    if any(phrase in q_lower for phrase in ["skill", "skills", "experience", "background", "skilled", "expertise", "proficient", "vector retrieval", "vector memory", "architecture"]):
        return "SKILL"

    # 8. HEALTH
    if any(phrase in q_lower for phrase in ["health", "anxiety", "diabetes", "medical", "allergies", "allergy", "illness", "condition", "doctor", "medicine"]):
        return "HEALTH"

    # 9. CURRENT INFORMATION
    if "weather" in q_lower:
        return "CURRENT_INFORMATION"

    # Default fallback intent classification for personal queries
    if any(p in f" {q_lower} " for p in ["i", "my", "me", "mine"]):
        if "name" in q_lower or "who am i" in q_lower:
            return "PERSONAL_NAME"
        if any(w in q_lower for w in ["live", "located", "city", "stay", "reside"]):
            return "PERSONAL_LOCATION"
        if any(w in q_lower for w in ["preference", "prefer", "favorite", "like"]):
            return "PREFERENCE"
        if any(w in q_lower for w in ["skill", "experience", "background", "knowledge"]):
            return "SKILL"
        if any(w in q_lower for w in ["goal", "project", "building"]):
            return "PROJECT"
        if any(w in q_lower for w in ["health", "anxiety", "diabetes", "medical", "allergy"]):
            return "HEALTH"
        return "GENERAL_PERSONAL"

    if any(q_lower.startswith(w) for w in ["what ", "where ", "who ", "how ", "why ", "which "]):
        return "GENERAL_KNOWLEDGE"

    return "GENERAL_PERSONAL"



class MemoryRanker:
    """
    Ranks and filters memories based on dynamic hybrid relevance scoring:
      - Vector Distance / Similarity (Weight: 0.45)
      - BM25 Lexical Score (Weight: 0.20)
      - Ebbinghaus Retention Decay (Weight: 0.25)
      - Semantic Importance (Weight: 0.10)
    """

    def __init__(self):
        self.decay_engine = EbbinghausDecayEngine()

    def rank(self, memories, query: str = ""):
        if not memories:
            return []

        for memory in memories:
            metadata = memory.get("metadata") or {}
            importance = float(metadata.get("importance", 0.5))
            access_count = int(metadata.get("access_count", 0))
            created_at = metadata.get("created_at", "")
            distance = memory.get("distance", 999.0)

            vector_similarity = 1.0 / (1.0 + distance)
            raw_bm25 = memory.get("bm25_score", 0.0)
            bm25_score = raw_bm25 / (raw_bm25 + 1.0)


            retention_score = self.decay_engine.calculate_retention(
                created_at_iso=created_at,
                importance=importance,
                access_count=access_count,
                current_time=clock.get_now()
            )

            composite_score = (
                (vector_similarity * 0.45) +
                (bm25_score * 0.20) +
                (retention_score * 0.25) +
                (importance * 0.10)
            )

            memory["retention_score"] = retention_score
            memory["vector_similarity"] = round(vector_similarity, 4)
            memory["score"] = round(composite_score, 4)
            memory["breakdown"] = {
                "vector_weight": round(vector_similarity * 0.45, 4),
                "bm25_weight": round(bm25_score * 0.20, 4),
                "decay_weight": round(retention_score * 0.25, 4),
                "importance_weight": round(importance * 0.10, 4)
            }

        memories.sort(key=lambda m: m["score"], reverse=True)
        return memories

    def filter_by_relevance(self, memories, query: str, min_similarity_threshold: float = 0.45):
        """
        Applies Category-Aware & Semantic Intent Relevance Filtering:
          Distinguishes topic relevance from answer relevance.
          - LOCATION queries accept location facts and reject name/skill memories.
          - NAME queries accept name facts and reject location/skill memories.
          - GENERAL KNOWLEDGE queries filter out 100% of personal background memories.
        """
        intent = classify_query_intent(query)
        print(f"[Retriever] Query: '{query}'")
        print(f"[Retriever] Intent: {intent}")

        if not memories or not query:
            print(f"[Retriever] Accepted: 0")
            print(f"[Retriever] Rejected: 0")
            return [], memories

        accepted = []
        rejected = []

        if intent in ["CONVERSATION", "GENERAL_KNOWLEDGE"]:
            for m in memories:
                doc = m.get("document", "")
                dist = round(m.get("distance", 999.0), 4)
                similarity = round(1.0 / (1.0 + dist), 4)
                print(f"[Retriever] Candidate: '{doc}'")
                print(f"[Retriever] Similarity: {similarity}")
                print(f"[Retriever] Relevance: LOW")
                print(f"[Retriever] Rejected: 1 ('{doc}')")
                rejected.append(m)

            print(f"[Retriever] Accepted: {len(accepted)}")
            print(f"[Retriever] Rejected: {len(rejected)}")
            return accepted, rejected

        q_lower = query.lower()

        for m in memories:
            doc = m.get("document") or ""
            doc_lower = doc.lower()
            meta = m.get("metadata") or {}
            category = meta.get("category", "Fact")
            dist = round(m.get("distance", 999.0), 4)
            similarity = round(1.0 / (1.0 + dist), 4)
            bm25 = m.get("bm25_score", 0.0)

            is_relevant = False

            if intent == "HISTORICAL_LOCATION":
                # Historical location query: matches previous/historical location facts
                location_terms = ["live", "moved", "located", "reside", "residing", "address", "city", "hyderabad", "bangalore", "bengaluru", "chennai", "seattle", "austin", "san francisco", "california", "texas", "tokyo", "mumbai", "delhi"]
                has_loc_term = any(w in doc_lower for w in location_terms)
                is_name_doc = ("name is" in doc_lower or "name:" in doc_lower or (doc_lower.startswith("user's name") and not has_loc_term))
                if has_loc_term and not is_name_doc:
                    is_relevant = True
                elif not is_name_doc and (dist <= 0.85 or bm25 > 0.0 or similarity >= 0.45):
                    is_relevant = True

            elif intent == "PERSONAL_LOCATION":
                # Current location query: strictly prefer active facts, reject superseded facts
                if meta.get("status") == "superseded":
                    is_relevant = False
                else:
                    location_terms = ["live", "moved", "located", "reside", "residing", "address", "city", "hyderabad", "bangalore", "bengaluru", "chennai", "seattle", "austin", "san francisco", "california", "texas", "tokyo", "mumbai", "delhi"]
                    has_loc_term = any(w in doc_lower for w in location_terms)
                    is_name_doc = ("name is" in doc_lower or "name:" in doc_lower or (doc_lower.startswith("user's name") and not has_loc_term))
                    
                    if has_loc_term and not is_name_doc:
                        is_relevant = True
                    elif not is_name_doc and (dist <= 0.85 or bm25 > 0.0 or similarity >= 0.45):
                        is_relevant = True


            elif intent == "PERSONAL_NAME":
                # Name query: must contain name terms and NOT be a location/skill memory
                name_terms = ["name is", "name:", "i am", "called"]
                has_name_term = any(w in doc_lower for w in name_terms)
                is_loc_doc = ("live in" in doc_lower or "moved to" in doc_lower or "located" in doc_lower)

                if has_name_term and not is_loc_doc:
                    is_relevant = True
                elif not is_loc_doc and (dist <= 0.85 or bm25 > 0.0 or similarity >= 0.45):
                    is_relevant = True

            elif intent == "PREFERENCE":
                # Preference query: match preference category or preference words
                pref_terms = ["prefer", "like", "love", "favorite", "favourite", "python", "rust", "typescript", "javascript"]
                has_pref_term = any(w in doc_lower for w in pref_terms)
                is_unrelated_doc = ("name is" in doc_lower or "live in" in doc_lower or "moved to" in doc_lower)

                if (category == "Preference" or has_pref_term) and not is_unrelated_doc:
                    is_relevant = True

            elif intent == "PROJECT":
                # Project/Goal query
                proj_terms = ["project", "building", "goal", "developing", "system", "memory os"]
                has_proj_term = any(w in doc_lower for w in proj_terms)
                is_unrelated_doc = ("name is" in doc_lower or "live in" in doc_lower or "moved to" in doc_lower)

                if (category in ["Project", "Goal"] or has_proj_term) and not is_unrelated_doc:
                    is_relevant = True

            elif intent == "SKILL":
                # Skill query
                skill_terms = ["skill", "expert", "experience", "know", "fastapi", "distributed", "vector"]
                has_skill_term = any(w in doc_lower for w in skill_terms)
                is_unrelated_doc = ("name is" in doc_lower or "live in" in doc_lower or "moved to" in doc_lower)

                if (category == "Skill" or has_skill_term) and not is_unrelated_doc:
                    is_relevant = True

            elif intent == "HEALTH":
                # Health query: matches health conditions, illnesses, allergies, medical facts
                health_terms = ["anxiety", "diabetes", "depression", "health", "medical", "allerg", "asthma", "diagnos", "doctor", "medicine", "wellness", "illness", "condition"]
                has_health_term = any(w in doc_lower for w in health_terms)
                is_unrelated_doc = ("name is" in doc_lower or "live in" in doc_lower or "moved to" in doc_lower)

                if (category == "Health" or has_health_term) and not is_unrelated_doc:
                    is_relevant = True

            else:
                # Fallback check
                if similarity >= 0.45 or bm25 > 0.0:
                    is_relevant = True

            print(f"[Retriever] Candidate: '{doc}' | Category: '{category}' | Similarity: {similarity:.4f} | BM25: {bm25:.2f}")

            if is_relevant:
                print(f"[Retriever] Relevance: HIGH")
                print(f"[Retriever] Accepted: 1 ('{doc}')")
                accepted.append(m)
            else:
                print(f"[Retriever] Relevance: LOW")
                print(f"[Retriever] Rejected: 1 ('{doc}')")
                rejected.append(m)

        print(f"[Retriever] Accepted: {len(accepted)}")
        print(f"[Retriever] Rejected: {len(rejected)}")
        return accepted, rejected