import json
import re
from app.llm.gemini import ask_gemini


class MemoryReconciler:
    """
    Automated Contradiction & Knowledge Graph Update Engine.
    Determines relationships between new incoming facts and existing vector DB memories:
      - SUPERSEDES: New fact updates/replaces an existing fact.
      - CONTRADICTS: New fact conflicts with an existing fact.
      - REINFORCES: New fact confirms an existing fact.
      - DISTINCT: New fact is separate and novel.
    """

    def reconcile(self, new_memory: str, existing_memory: str) -> dict:
        # Topic Safety Guard: Ensure memories cover the same semantic topic domain before evaluating superseding/contradiction
        loc_words = [
            "live", "lives", "living", "moved", "moving", "located", "reside", "resides",
            "residing", "bengaluru", "bangalore", "hyderabad", "chennai", "seattle", "austin",
            "san francisco", "mumbai", "delhi", "tokyo", "city", "address", "relocated",
            "relocating", "shifted", "shifting", "based"
        ]
        name_words = ["name is", "name:", "called", "i am"]

        new_lower = new_memory.lower()
        ex_lower = existing_memory.lower()

        # 1. Exact match reinforcement check
        if new_lower.strip() == ex_lower.strip():
            return {
                "relationship": "REINFORCES",
                "reason": "New memory exactly confirms existing stored memory.",
                "action": "INCREMENT_COUNT"
            }

        new_is_loc = any(w in new_lower for w in loc_words)
        ex_is_loc = any(w in ex_lower for w in loc_words)
        new_is_name = any(w in new_lower for w in name_words)
        ex_is_name = any(w in ex_lower for w in name_words)

        # Cross-category mismatches (e.g. location vs name) are strictly DISTINCT
        if (new_is_loc and not ex_is_loc) or (ex_is_loc and not new_is_loc):
            return {"relationship": "DISTINCT", "reason": "Memories cover different semantic domains (location vs non-location).", "action": "STORE_NEW"}
        if (new_is_name and not ex_is_name) or (ex_is_name and not new_is_name):
            return {"relationship": "DISTINCT", "reason": "Memories cover different semantic domains (name vs non-name).", "action": "STORE_NEW"}

        # 2. Semantic Location Fact Reconciliation:
        # If both are location facts, determine whether they refer to the same city (REINFORCES) or different city (SUPERSEDES)
        if new_is_loc and ex_is_loc:
            known_cities = [
                "chennai", "hyderabad", "bengaluru", "bangalore", "seattle", "austin",
                "san francisco", "mumbai", "delhi", "tokyo", "pittsburgh", "new york",
                "boston", "chicago", "london", "paris"
            ]
            new_city = next((c for c in known_cities if c in new_lower), None)
            ex_city = next((c for c in known_cities if c in ex_lower), None)

            # If cities are extracted directly
            if new_city and ex_city:
                if new_city == ex_city:
                    return {
                        "relationship": "REINFORCES",
                        "reason": f"New statement confirms active residence in {new_city.capitalize()}.",
                        "action": "INCREMENT_COUNT"
                    }
                else:
                    return {
                        "relationship": "SUPERSEDES",
                        "reason": f"New location fact ({new_city.capitalize()}) updates previous location fact ({ex_city.capitalize()}).",
                        "action": "SUPERSEDE_OLD"
                    }

        prompt = f"""
You are a Memory Reconciliation Engine for an AI Memory OS.

Compare the NEW incoming memory statement with an EXISTING stored memory statement and determine their semantic relationship.

Existing Memory: "{existing_memory}"
New Memory: "{new_memory}"

Classify their relationship into EXACTLY ONE of the following types:
1. "SUPERSEDES"  : The new memory updates, replaces, or evolves the existing memory (e.g. "User lives in NY" -> "User moved to SF").
2. "REINFORCES"  : The new memory repeats, reinforces, or confirms the existing memory.
3. "CONTRADICTS" : The new memory directly contradicts the existing memory without indicating time progression.
4. "DISTINCT"    : The memories are about different topics or entities despite sharing some context.

Return ONLY valid JSON in this exact structure:
{{
  "relationship": "SUPERSEDES" | "REINFORCES" | "CONTRADICTS" | "DISTINCT",
  "reason": "Brief explanation",
  "action": "SUPERSEDE_OLD" | "INCREMENT_COUNT" | "FLAG_CONTRADICTION" | "STORE_NEW"
}}
"""
        try:
            response = ask_gemini(prompt)
            if not response:
                return {"relationship": "DISTINCT", "action": "STORE_NEW", "reason": "Empty LLM response"}

            cleaned = response.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(0)

            result = json.loads(cleaned)
            return result
        except Exception as e:
            print(f"[MemoryReconciler] Error during reconciliation: {e}")
            return {
                "relationship": "DISTINCT",
                "action": "STORE_NEW",
                "reason": f"Reconciler error: {str(e)}"
            }
