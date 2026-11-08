import json
import re

from app.llm.gemini import ask_gemini


class MemoryGate:
    """
    Decides whether a user message should be stored
    as long-term memory.
    """

    def should_store(self, text: str) -> dict:

        prompt = f"""
You are a Memory Gate for an AI Memory Operating System.

Your job is to decide whether the user's latest message should be stored as long-term memory.

Store ONLY durable information that is likely to remain useful across future conversations.

Store:
- Personal facts
- Preferences
- Habits
- Skills
- Goals
- Ongoing projects
- Relationships
- Permanent information

Do NOT store:
- Greetings
- Questions
- Small talk
- Temporary requests
- Thank you messages
- One-time instructions
- Anything only relevant to the current conversation.

Return ONLY valid JSON.

Example:
{{
  "store": true,
  "reason": "Stable personal fact."
}}

or

{{
  "store": false,
  "reason": "User is asking a question."
}}

User message:
{text}
"""

        try:
            response = ask_gemini(prompt)

            if not response:
                print("[MemoryGate] Empty response from Gemini.")
                return {
                    "store": False,
                    "reason": "Empty Gemini response."
                }

            print(f"[MemoryGate] Raw Response:\n{response}")

            # Remove markdown code fences
            cleaned = response.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

            # Extract the first JSON object if extra text exists
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(0)

            result = json.loads(cleaned)

            # Validate expected fields
            if not isinstance(result, dict):
                raise ValueError("Response is not a JSON object.")

            if "store" not in result:
                result["store"] = False

            if "reason" not in result:
                result["reason"] = "No reason provided."

            return result

        except Exception as e:
            print(f"[MemoryGate] Error: {e}")

            return {
                "store": False,
                "reason": f"Memory Gate error: {str(e)}"
            }