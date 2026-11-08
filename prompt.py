class PromptBuilder:
    """
    Responsible for constructing clean, high-precision prompts for the LLM,
    injecting long-term memories, user persona profile, short-term conversation context, and multimodal visual context.
    """

    def build(
        self,
        memories,
        user_message: str,
        persona_summary: str = "",
        visual_summary: str = "",
        short_term_context: list = None
    ):
        memory_lines = []
        if memories:
            for memory in memories:
                doc = memory.get('document', '')
                meta = memory.get('metadata', {})
                if meta.get('modality') == 'multimodal' and meta.get('visual_summary'):
                    memory_lines.append(f"- {doc} (Visual Context: {meta.get('visual_summary')})")
                else:
                    memory_lines.append(f"- {doc}")

        memory_block = "\n".join(memory_lines) if memory_lines else "No specific memory retrieved for this turn."

        history_lines = []
        if short_term_context:
            for turn in short_term_context[-5:]:
                history_lines.append(f"User: {turn.get('user', '')}")
                history_lines.append(f"Assistant: {turn.get('assistant', '')}")

        history_block = "\n".join(history_lines) if history_lines else "No recent conversation history."

        prompt = f"""SYSTEM:
You are a helpful, direct, and conversational AI assistant with persistent memory.

USER PROFILE:
{persona_summary if persona_summary else "No persistent user profile recorded yet."}

RELEVANT MEMORY:
{memory_block}

RECENT CONVERSATION HISTORY:
{history_block}
"""

        if visual_summary:
            prompt += f"\nATTACHED VISUAL CONTEXT:\n{visual_summary}\n"

        prompt += f"""
CURRENT USER MESSAGE:
{user_message}

INSTRUCTIONS:
- Answer the user's CURRENT question first, directly, naturally, and concisely.
- Use RECENT CONVERSATION HISTORY to resolve follow-up questions, pronouns, or ambiguous references (e.g., "for Telangana", "capital for ?", "what about Karnataka?", "what were we talking about?").
- Use profile/memory ONLY when it is directly relevant to the current user message.
- Never output the profile or memory list itself.
- Never expose raw memory records, IDs, metadata, distances, scores, or profile dumps.
- Never mention that you retrieved memories or database records unless explicitly asked.
- Do not repeat unrelated personal information.
- If the user asks for real-time live data (such as current weather or stock prices) that is unavailable, state so honestly.
"""

        return prompt