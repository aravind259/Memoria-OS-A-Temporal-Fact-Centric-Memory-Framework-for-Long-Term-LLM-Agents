import re
from typing import Dict, Any, List, Optional
from app.memory.chroma import get_all_memories


class UserPersonaEngine:
    """
    Enhanced Personalization Engine:
    Dynamically synthesizes user memories into structured persona attributes
    and provides relevance-gated persona context injection.
    """

    def synthesize_persona(self, user_id: str = "default_user") -> Dict[str, Any]:
        memories = get_all_memories(include_superseded=False, user_id=user_id)
        
        categories = {
            "Preference": [],
            "Skill": [],
            "Goal": [],
            "Project": [],
            "Fact": [],
            "Health": [],
            "Multimodal": []
        }

        name_val = ""
        location_val = ""

        for mem in memories:
            doc = mem.get("document", "")
            meta = mem.get("metadata", {})
            cat = meta.get("category", "Fact")
            modality = meta.get("modality", "text")

            doc_lower = doc.lower()
            
            # Extract structured name if present
            m_name = re.search(r"(?:user'?s\s+name\s+is|my name is|i am|name:)\s*([a-zA-Z]+)", doc_lower)
            excluded_words = {"a", "the", "building", "living", "working", "lead", "developer", "architect", "skilled"}
            if m_name:
                extracted = m_name.group(1).lower()
                if extracted not in excluded_words:
                    name_val = m_name.group(1).capitalize()


            # Extract structured location if present (supporting 1st and 3rd person and adverbs like recently/just)
            m_loc = re.search(
                r"(?:(?:user|i)\s+(?:recently\s+|just\s+|lately\s+)?(?:moved\s+to|relocated\s+to|shifted\s+to|lives?\s+in|resides?\s+in)|located in|is based in|location:)\s*([a-zA-Z\s]+?)(?:[;\.\n]|$)",
                doc_lower
            )
            if m_loc:
                raw_loc = m_loc.group(1).strip()
                # Clean extraneous words like 'last week' or 'recently' if present
                clean_loc = re.sub(
                    r"\b(?:last|this|next)\s+(?:week|month|year)\b|\b(?:recently|lately|now|temporarily|permanently)\b",
                    "",
                    raw_loc,
                    flags=re.IGNORECASE
                ).strip()
                if clean_loc:
                    location_val = clean_loc.title()

            if modality == "multimodal":
                categories["Multimodal"].append(doc)

            if cat in categories:
                categories[cat].append(doc)
            else:
                categories["Fact"].append(doc)

        summary_text = self._build_persona_summary_text(categories, name_val, location_val)

        return {
            "user_id": user_id,
            "total_active_memories": len(memories),
            "name": name_val,
            "location": location_val,
            "categories": categories,
            "persona_summary": summary_text
        }

    def get_relevant_persona(self, query: str, user_id: str = "default_user") -> str:
        """
        Relevance-gated persona retrieval: returns persona summary ONLY if relevant to query context.
        """
        q_lower = query.lower()
        
        # Check query relevance for persona context injection
        personal_triggers = [
            "who am i", "my name", "where do i", "where am i", "my location", "my preferences",
            "my favorite", "my skills", "my project", "my background", "tell me about me", "where i do live", "where i live"
        ]

        if any(trigger in q_lower for trigger in personal_triggers):
            persona = self.synthesize_persona(user_id=user_id)
            return persona.get("persona_summary", "")

        return ""

    def generate_quick_action_suggestions(self, user_id: str = "default_user") -> List[Dict[str, str]]:
        """
        Generates dynamic quick-action suggestions tailored to active user persona and memories.
        Never suggests old/superseded locations as current locations.
        Falls back to general suggestions when no suitable personal context exists.
        """
        persona = self.synthesize_persona(user_id=user_id)
        name = persona.get("name")
        location = persona.get("location")

        # Check for historical / superseded memories to enable historical exploration (across L2 Chroma and L3 Cold Archive)
        all_memories = get_all_memories(include_superseded=True, user_id=user_id)
        cold_memories = []
        try:
            from app.memory.archive_storage import ColdArchiveStorage
            cold_memories = ColdArchiveStorage().get_archived_memories(user_id=user_id)
        except Exception:
            pass

        all_history = all_memories + cold_memories
        has_historical_location = any(
            (
                m.get("metadata", {}).get("status") in ["superseded", "archived"] or
                m.get("status") in ["superseded", "archived"] or
                bool(m.get("metadata", {}).get("superseded_by"))
            ) and
            any(w in m.get("document", "").lower() for w in ["live", "lives", "living", "moved", "moving", "located", "reside", "resides", "hyderabad", "chennai", "bengaluru", "seattle", "austin"])
            for m in all_history
        )

        suggestions = []

        if name:
            suggestions.append({"icon": "👤", "text": "What is my name?"})

        if location:
            suggestions.append({"icon": "❓", "text": "Where do I live now?"})
            suggestions.append({"icon": "🌐", "text": f"What languages are spoken in {location}?"})
            suggestions.append({"icon": "🏖️", "text": f"Suggest holiday destinations near {location}"})

        if has_historical_location:
            suggestions.append({"icon": "🕰️", "text": "Where did I live before?"})

        categories = persona.get("categories", {})
        if categories.get("Preference"):
            suggestions.append({"icon": "💻", "text": "What programming languages do I like?"})
        elif categories.get("Project"):
            suggestions.append({"icon": "🚀", "text": "What project am I building?"})

        # Fallback to general suggestions if no personalized context is established
        if not suggestions or (not name and not location):
            return [
                {"icon": "👤", "text": "My name is Aravind"},
                {"icon": "📍", "text": "I live in Hyderabad"},
                {"icon": "🚀", "text": "I recently moved to Chennai"},
                {"icon": "❓", "text": "Where do I live now?"},
                {"icon": "❓", "text": "What is my name?"},
                {"icon": "🌐", "text": "What languages are spoken in India?"},
                {"icon": "🏖️", "text": "Suggest holiday destinations for me"}
            ]

        return suggestions[:7]

    def _build_persona_summary_text(self, categories: Dict[str, List[str]], name: str, location: str) -> str:
        parts = []
        if name:
            parts.append(f"Name: {name}")
        if location:
            parts.append(f"Location: {location}")
        
        for cat, items in categories.items():
            if items:
                joined = "; ".join(items[:3])
                parts.append(f"{cat}s: {joined}")

        return " | ".join(parts)
