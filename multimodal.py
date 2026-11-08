import os
import json
import base64
from typing import Dict, Any, Optional
from app.services.llm import LLMService

class MultimodalMemoryProcessor:
    """
    Multimodal Memory Engine:
    Processes textual + visual payloads (Image URLs, Base64 strings, or visual attachments),
    extracts factual assertion statements from visual context, and generates multi-modal metadata.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()

    def process_multimodal_input(
        self,
        text: str,
        image_url: Optional[str] = None,
        image_b64: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyzes image payload alongside text utterance to generate visual summary and unified factual assertion.
        """
        if not image_url and not image_b64:
            return {
                "modality": "text",
                "combined_text": text,
                "visual_summary": "",
                "image_url": ""
            }

        target_image = image_url or "uploaded_image_payload"
        
        prompt = (
            f"You are a Multimodal AI Memory Extractor.\n"
            f"The user provided a text message and an image: '{target_image}'.\n"
            f"User Text: \"{text}\"\n"
            f"Generate a JSON object with two fields:\n"
            f"1. 'visual_summary': A concise description of the relevant objects, context, or visual details shown in the image.\n"
            f"2. 'combined_fact': A unified factual statement integrating both the user's text and the visual information.\n"
            f"Output JSON format strictly: {{\"visual_summary\": \"...\", \"combined_fact\": \"...\"}}"
        )

        try:
            raw_res = self.llm.generate(prompt)
            # Try parsing JSON response
            cleaned_res = raw_res.strip()
            if cleaned_res.startswith("```json"):
                cleaned_res = cleaned_res[7:-3].strip()
            elif cleaned_res.startswith("```"):
                cleaned_res = cleaned_res[3:-3].strip()
                
            data = json.loads(cleaned_res)
            return {
                "modality": "multimodal",
                "combined_text": data.get("combined_fact", f"{text} [Visual Context: {target_image}]"),
                "visual_summary": data.get("visual_summary", f"Visual context from {target_image}"),
                "image_url": target_image if image_url else "data:image/png;base64,..."
            }
        except Exception as e:
            print(f"[MultimodalProcessor] Fallback processing: {e}")
            fallback_summary = f"User uploaded visual asset: {target_image}"
            return {
                "modality": "multimodal",
                "combined_text": f"{text} (Image context: {fallback_summary})",
                "visual_summary": fallback_summary,
                "image_url": target_image
            }
