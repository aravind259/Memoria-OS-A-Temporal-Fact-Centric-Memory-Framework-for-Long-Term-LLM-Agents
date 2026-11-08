from app.llm.gemini import ask_gemini


class LLMService:

    def generate(self, prompt: str):
        return ask_gemini(prompt)