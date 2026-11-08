from app.memory.persona import UserPersonaEngine


class MemoryManager:

    def __init__(
        self,
        retriever,
        storage,
        prompt_builder,
        working_memory,
        conversation_service,
        llm_service,
    ):
        self.retriever = retriever
        self.storage = storage
        self.prompt_builder = prompt_builder
        self.working_memory = working_memory
        self.conversation = conversation_service
        self.llm = llm_service
        self.persona_engine = UserPersonaEngine()

    def chat(
        self,
        message: str,
        user_id: str = "default_user",
        tenant_id: str = "default_tenant",
        image_url: str = None,
        image_b64: str = None
    ):
        print(f"[CHAT] User message: {message}")

        # 1. Fetch short-term working memory conversation context
        short_term_context = []
        if self.working_memory:
            short_term_context = self.working_memory.get_short_term_context()

        # 2. Retrieve relevant long-term memories for user
        memories = self.retriever.retrieve(message, user_id=user_id)
        print(f"[CHAT] Retrieved memories: {len(memories)}")

        # 3. Get relevance-gated User Persona Profile context
        relevant_persona = self.persona_engine.get_relevant_persona(query=message, user_id=user_id)

        # 4. Build augmented RAG prompt with relevant persona, long-term memories & short-term context
        prompt = self.prompt_builder.build(
            memories=memories,
            user_message=message,
            persona_summary=relevant_persona,
            visual_summary=f"Attached image URL: {image_url}" if image_url else "",
            short_term_context=short_term_context
        )

        # 4. Generate actual LLM Response FIRST
        answer = self.llm.generate(prompt)
        print(f"[CHAT] Generated response: {answer}")

        # 5. Save to conversation service DB
        try:
            self.conversation.save(
                user_message=message,
                ai_response=answer
            )
        except Exception as e:
            print(f"[MemoryManager] Warning saving conversation log: {e}")

        # 6. Memory storage/update happens as a SEPARATE pipeline AFTER response generation
        result = self.storage.store(
            user_message=message,
            ai_response=answer,
            user_id=user_id,
            tenant_id=tenant_id,
            image_url=image_url,
            image_b64=image_b64
        )
        storage_status = result.get("status", "NOT_STORED")
        print(f"[MEMORY] Storage result: {storage_status}")

        # 7. Add turn to short-term working memory
        try:
            self.working_memory.add_turn(
                user_message=message,
                ai_response=answer,
                category=result.get("category"),
                importance=result.get("importance", 0.5)
            )
        except Exception as e:
            print(f"[MemoryManager] Working memory warning: {e}")

        # Return actual LLM answer in "response" field (never overwritten by internal storage status)
        return {
            "response": answer,
            "category": result.get("category", "Conversation"),
            "importance": result.get("importance", 0.1),
            "stored": result.get("stored", False),
            "action": result.get("action", "none"),
            "storage_status": storage_status,
            "memories_used": memories,
            "persona_summary": relevant_persona,
            "has_pii": result.get("has_pii", False),
            "detected_pii": result.get("detected_pii", []),
            "reason": result.get("reason", "")
        }