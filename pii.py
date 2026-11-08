import re
from typing import Dict, List, Any


class PIIScrubber:
    """
    Automated PII & Sensitive Data Sanitization Engine.
    Scans incoming memory strings for sensitive personal identifiable information (PII)
    and redacts them before vector store ingestion or embedding generation.
    """

    PATTERNS = {
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "PHONE": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
        "API_KEY": r"\b(?:sk-[a-zA-Z0-9]{20,}|AIzaSy[a-zA-Z0-9_-]{33})\b"
    }

    REPLACEMENTS = {
        "EMAIL": "[REDACTED_EMAIL]",
        "PHONE": "[REDACTED_PHONE]",
        "SSN": "[REDACTED_SSN]",
        "CREDIT_CARD": "[REDACTED_CARD]",
        "API_KEY": "[REDACTED_SECRET_KEY]"
    }

    def sanitize(self, text: str) -> Dict[str, Any]:
        """
        Sanitizes text by replacing detected PII patterns with redacted placeholders.
        Returns clean text and metadata regarding PII findings.
        """
        if not text:
            return {"clean_text": "", "has_pii": False, "detected_pii": []}

        clean_text = text
        detected = []

        for pii_type, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, clean_text)
            if matches:
                detected.append(pii_type)
                replacement = self.REPLACEMENTS[pii_type]
                clean_text = re.sub(pattern, replacement, clean_text)

        return {
            "clean_text": clean_text,
            "has_pii": len(detected) > 0,
            "detected_pii": detected
        }
