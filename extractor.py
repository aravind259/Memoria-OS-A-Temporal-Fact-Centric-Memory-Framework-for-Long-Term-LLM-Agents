from app.llm.gemini import ask_gemini


class MemoryExtractor:

    def extract(self, text: str) -> str:

        prompt = f"""
You are a memory extraction system.

Convert the user's message into ONE concise memory.

Rules:
- Write in third person.
- Start with "User".
- Keep only useful long-term information.
- Remove conversational words.
- Keep it under one sentence.

Examples:

Input:
I speak Telugu most of the time.

Output:
User speaks Telugu most of the time.

Input:
I'm building a Memory OS.

Output:
User is building a Memory OS.

Input:
I love cricket.

Output:
User likes cricket.

Input:
My favorite color is green.

Output:
User's favorite color is green.

Now convert this:

{text}
"""

        return ask_gemini(prompt).strip()