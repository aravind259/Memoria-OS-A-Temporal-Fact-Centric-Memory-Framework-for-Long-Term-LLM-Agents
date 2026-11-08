import json
import re
from app.llm.gemini import ask_gemini


class MemoryClassifier:
    """
    Classifies user messages and distilled facts into semantic memory categories:
    Preference, Goal, Task, Project, Skill, Event, Fact, Conversation.
    Uses LLM zero-shot classification with heuristic fallback.
    """

    CATEGORIES = ["Preference", "Goal", "Task", "Project", "Skill", "Event", "Fact", "Health", "Conversation"]

    def classify(self, text: str) -> str:
        # Step 1: Fast Heuristic Rules
        heuristic_cat = self._heuristic_classify(text)
        if heuristic_cat != "Conversation":
            return heuristic_cat

        # Step 2: Zero-shot LLM Classification for ambiguity
        prompt = f"""
Classify the following user message into EXACTLY ONE of these categories:
- Preference: Personal tastes, likes, dislikes, favorite items
- Goal: Aspirations, ambitions, intentions, things the user wants to achieve, learn, or overcome (e.g. "I want to join Microsoft", "I want to overcome anxiety")
- Task: Action items, todos, reminders, urgent actions to take
- Project: Systems, software, applications, or products the user is actively building
- Skill: Technical abilities, professional experience, languages spoken, expertise
- Event: Specific dated occurrences, meetings, trips (yesterday, last week, etc.)
- Health: Medical conditions, physical or mental health status, chronic diseases, allergies, diagnoses (e.g. "I have anxiety", "User has anxiety issues", "I have diabetes", "Allergic to nuts")
- Fact: Stable factual information about identity, residence, workplace, demographics
- Conversation: Transient chit-chat, greetings, questions, acknowledgments

Categories allowed:
{", ".join(self.CATEGORIES)}

User Message: "{text}"

Return ONLY a JSON object:
{{"category": "<category_name>"}}
"""
        try:
            response = ask_gemini(prompt)
            cleaned = re.sub(r"^```(?:json)?\s*", "", response.strip(), flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(0)
            data = json.loads(cleaned)
            cat = data.get("category", "Conversation")
            if cat in self.CATEGORIES:
                return cat
        except Exception:
            pass

        return heuristic_cat

    def _heuristic_classify(self, text: str) -> str:
        t = text.lower()

        # 1. Goal / Aspiration: Intentions and future ambitions (even about health, e.g. "want to overcome anxiety")
        goal_markers = ["goal", "want to", "dream", "aspire", "plan to", "aim to", "hoping to", "wish to", "trying to"]
        if any(w in t for w in goal_markers):
            return "Goal"

        # 2. Preference: Subjective likes, tastes, habits
        if any(w in t for w in ["favorite", "favourite", "like", "love", "prefer", "hate", "dislike"]):
            return "Preference"

        # 3. Health: Medical conditions, mental/physical health status, chronic illnesses, allergies, diagnoses
        health_markers = [
            "anxiety", "diabetes", "depression", "depressed", "asthma", "allergy", "allergies",
            "allergic", "bipolar", "migraine", "insomnia", "adhd", "hypertension", "blood pressure",
            "chronic", "diagnosed", "health issue", "health condition", "medical condition",
            "have anxiety", "has anxiety", "have diabetes", "has diabetes", "suffering from",
            "suffers from", "illness", "disease", "mental health", "physical health"
        ]
        if any(w in t for w in health_markers):
            return "Health"

        # 4. Task: Action items, todos
        if any(w in t for w in ["todo", "task", "remind", "must do", "need to"]):
            return "Task"

        # 5. Project: Development, engineering, building projects
        if any(w in t for w in ["project", "building", "developing", "creating", "coding"]):
            return "Project"

        # 6. Skill: Competencies, knowledge, proficiencies
        if any(w in t for w in ["know", "learned", "experience", "skill", "speak", "expert", "proficient"]):
            return "Skill"

        # 7. Fact: Personal biographical/locational facts
        if any(w in t for w in ["live", "age", "name", "born", "work", "located", "moved", "relocated", "shifted", "reside"]):
            return "Fact"

        # 8. Event: Temporal occurrences
        if any(w in t for w in ["yesterday", "today", "last week", "visited", "went", "met"]):
            return "Event"

        return "Conversation"