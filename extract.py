import json
import re
from typing import List, Dict, Any, Optional

from app.llm.gemini import ask_gemini


def extract_facts(
    user_msg: str,
    assistant_msg: str,
    now: str,
    existing_attributes: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Extracts structured facts from a conversation turn using ONE Gemini call.
    Rules:
      - subject is "user" only when the fact is about the user,
        otherwise the specific person (e.g. "user's sister") or "assistant" for commitments/recommendations.
      - Reuse an existing attribute name when it means the same thing (e.g. home_city, not lives_in).
      - Resolve relative dates (e.g. "last week", "last month") against `now`.
      - Trips, visits and one-off happenings are kind=event.
      - kind is one of: trait, state, event.
      - Questions with no new information return [].
      - Do not reject a message just because it contains '?'.
    """
    if not user_msg and not assistant_msg:
        return []

    attr_context = ""
    if existing_attributes:
        attr_context = f"\nExisting user attribute names to reuse if applicable:\n{json.dumps(existing_attributes)}\n"

    prompt = f"""You are a precise Memory Fact Extraction Engine.
Analyze the following conversation turn and extract any new or updated personal facts, states, traits, or events.

Reference Timestamp (now): {now}
{attr_context}
Conversation Turn:
User: {user_msg}
Assistant: {assistant_msg}

Rules for Extraction:
1. Output format: A JSON list of fact objects. Each fact MUST contain:
   - "subject": "user" when the fact is directly about the user; otherwise the specific entity (e.g. "user's sister", "user's friend", "user's spouse") or "assistant" for commitments or specific recommendations made by the assistant.
   - "attribute": Standardized lowercase snake_case attribute name (e.g. home_city, last_name, employer, visited_place, skills). ONLY reuse an existing attribute name if it represents the EXACT SAME semantic concept (e.g. home_city for lives_in). NEVER merge distinct concepts (e.g. never place volleyball techniques into running_preference).
   - "value": The core value or content of the fact. Include specific details (e.g. brand names, counts, durations).
   - "kind": Exactly one of:
       * "trait": permanent or inherent personal traits (e.g. birth date, name, native language).
       * "state": current condition, residence, status, or role that may change over time (e.g. home_city, job_title, relationship).
       * "event": trips, visits, weddings, conferences, or one-off happenings.
   - "cardinality": Exactly one of:
       * "one": for single-valued attributes that can have only one active state at a time (e.g. home_city, last_name, first_name, job_title, employer, relationship_status).
       * "many": for multi-valued attributes that can accumulate multiple entries (e.g. interests, activities, visited_place, owned_items, skills, preferences, sports).
   - "valid_from": The effective date or timestamp of the fact. Resolve relative temporal expressions (such as "last week", "yesterday", "last month", "in 2024") relative to the Reference Timestamp (now). If the fact describes current state with no explicit past timestamp, use {now}.
2. Questions with no new factual information MUST return an empty list [].
3. Do NOT reject a message just because it contains '?'. If the user shares information or updates while asking a question (e.g. "I moved to ... last month, any good cafes?"), extract the new information.
4. If no durable facts, states, traits, or events are stated, return an empty list [].

Respond with ONLY the JSON list of objects, without markdown code fences or explanatory text.
Example format:
[
  {{"subject": "user", "attribute": "home_city", "value": "Example", "kind": "state", "cardinality": "one", "valid_from": "{now}"}},
  {{"subject": "user", "attribute": "visited_place", "value": "Melbourne", "kind": "event", "cardinality": "many", "valid_from": "{now}"}}
]
"""

    response = ask_gemini(prompt)
    if not response:
        return []

    # Clean and parse JSON
    cleaned = response.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    SINGLE_VALUED_ATTRS = {
        "home_city", "last_name", "first_name", "full_name", "job_title",
        "employer", "relationship_status", "birth_date", "current_residence",
        "marital_status", "company", "age"
    }

    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            valid_facts = []
            for item in data:
                if isinstance(item, dict) and "subject" in item and "attribute" in item and "value" in item:
                    subject = str(item.get("subject", "user")).strip()
                    attribute = str(item.get("attribute", "")).strip().lower().replace(" ", "_")
                    value = str(item.get("value", "")).strip()
                    kind = str(item.get("kind", "state")).strip().lower()
                    if kind not in ("trait", "state", "event"):
                        kind = "state"

                    cardinality = str(item.get("cardinality", "")).strip().lower()
                    if cardinality not in ("one", "many"):
                        cardinality = "one" if attribute in SINGLE_VALUED_ATTRS else "many"

                    valid_from = str(item.get("valid_from", now)).strip()

                    valid_facts.append({
                        "subject": subject,
                        "attribute": attribute,
                        "value": value,
                        "kind": kind,
                        "cardinality": cardinality,
                        "valid_from": valid_from
                    })
            return valid_facts
    except Exception as e:
        print(f"[MemoryV2 Extract] JSON parsing error: {e}")

    return []
