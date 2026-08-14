import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

PLATFORM_GUIDELINES = {
    "instagram": "Format with engaging hook, short paragraph lines, relevant emojis, and 3-5 high-converting hashtags.",
    "linkedin": "Professional tone, industry insight focus, spacing between lines for readability, thought-provoking question at end.",
    "x": "Concise (under 280 chars unless thread specified), punchy line breaks, minimal hashtags, strong call-to-action.",
    "twitter": "Concise (under 280 chars unless thread specified), punchy line breaks, minimal hashtags, strong call-to-action.",
    "tiktok": "Casual, fast-paced script layout with visual directions, engaging hook within 3 seconds, clear call-to-action.",
    "facebook": "Conversational, community-oriented tone with clear storytelling and engagement question.",
    "youtube": "Detailed description format with timestamp placeholders, links section, and key topic breakdown."
}

class PromptManager:
    def build_system_prompt(
        self,
        task_type: str = "content",
        platform: Optional[str] = None,
        brand: Optional[Any] = None,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> str:
        instructions = [
            "You are Syncfloww's elite AI Content Specialist.",
            "Generate high-quality, engaging social media and marketing content optimized for growth."
        ]

        if brand:
            brand_name = getattr(brand, "name", "our brand")
            brand_voice = getattr(brand, "voice", "") or getattr(brand, "tone", "")
            brand_desc = getattr(brand, "description", "")
            
            instructions.append(f"\n--- BRAND CONTEXT ---")
            instructions.append(f"Brand Name: {brand_name}")
            if brand_desc:
                instructions.append(f"Brand Description: {brand_desc}")
            if brand_voice:
                instructions.append(f"Brand Voice/Tone: {brand_voice}")

        if platform:
            plat_key = platform.lower()
            guidelines = PLATFORM_GUIDELINES.get(plat_key, "")
            if guidelines:
                instructions.append(f"\n--- PLATFORM GUIDELINES ({platform.upper()}) ---")
                instructions.append(guidelines)

        if task_type == "comment_classification" or task_type == "sentiment":
            instructions.append("\n--- TASK GUIDELINES ---")
            instructions.append("Analyze sentiment and intent accurately. Return structured JSON with fields: 'sentiment', 'category', 'urgency', 'summary'.")

        elif task_type == "script":
            instructions.append("\n--- TASK GUIDELINES ---")
            instructions.append("Structure output into clear sections: Hook, Body, Transitions, Call To Action, and Visual Directions.")

        if extra_context and extra_context.get("system_instructions"):
            instructions.append(f"\n--- ADDITIONAL DIRECTIVES ---")
            instructions.append(str(extra_context["system_instructions"]))

        return "\n".join(instructions)

    def build_user_prompt(
        self,
        prompt: str,
        task_type: str = "content",
        platform: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None
    ) -> str:
        parts = [prompt]
        if inputs:
            parts.append("\n--- INPUT DATA ---")
            for k, v in inputs.items():
                parts.append(f"{k}: {v}")
        return "\n".join(parts)
