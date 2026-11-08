class MemoryImportance:
    """
    Evaluates the temporal permanence and personal importance of a memory (0.0 to 1.0).
    High importance = Durable identity, long-term preference, relocation, core skill, or major life fact.
    Low importance = Transient chat, small talk, or minor detail.
    """

    def score(self, message: str) -> float:
        msg = message.lower()
        if len(msg) < 8:
            return 0.1

        high_priority_signals = [
            "my name", "i am", "i'm", "live in", "work as", "my job",
            "favorite", "love", "hate", "prefer", "allergic", "speak",
            "goal", "building", "project", "remember", "never", "always",
            "moved", "moved to", "moved from", "relocated", "shifted", "living in", "reside", "residing in",
            "anxiety", "diabetes", "depression", "asthma", "allergy", "allergies", "diagnosed", "health", "medical"
        ]

        medium_priority_signals = [
            "learned", "bought", "visited", "plan", "want", "think", "studied"
        ]

        for signal in high_priority_signals:
            if signal in msg:
                return 0.90

        for signal in medium_priority_signals:
            if signal in msg:
                return 0.70

        if len(msg) > 40:
            return 0.60

        return 0.40