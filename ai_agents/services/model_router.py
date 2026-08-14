import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Task Type -> (Default Provider, Default Model)
TASK_ROUTING_MAP = {
    "sentiment": ("gemini", "gemini-2.5-flash"),
    "comment_classification": ("gemini", "gemini-2.5-flash"),
    "caption": ("gemini", "gemini-2.5-flash"),
    "idea": ("gemini", "gemini-2.5-flash"),
    "social_content": ("gemini", "gemini-2.5-flash"),
    "script": ("gemini", "gemini-2.5-flash"),
    "agent_reasoning": ("gemini", "gemini-2.5-pro"),
    "huggingface_default": ("huggingface", "meta-llama/Llama-3.2-3B-Instruct"),
    "ollama_default": ("ollama", "llama3"),
}

class ModelRouter:
    def resolve_target(
        self,
        task_type: str = "content",
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Resolves provider and model string based on explicit overrides or task type routing logic.
        """
        resolved_provider = (provider or "").lower().strip()
        resolved_model = model or ""

        if resolved_provider and resolved_model:
            return resolved_provider, resolved_model

        if resolved_provider:
            if resolved_provider == "huggingface":
                return "huggingface", resolved_model or "meta-llama/Llama-3.2-3B-Instruct"
            if resolved_provider == "ollama":
                return "ollama", resolved_model or "llama3"
            if resolved_provider == "litellm":
                return "litellm", resolved_model or "gpt-4o-mini"
            if resolved_provider == "openai":
                return "openai", resolved_model or "gpt-4o-mini"
            if resolved_provider == "gemini":
                return "gemini", resolved_model or "gemini-2.5-flash"

        # Fallback to Task Map
        default_prov, default_mdl = TASK_ROUTING_MAP.get(task_type, ("gemini", "gemini-2.5-flash"))
        return (resolved_provider or default_prov), (resolved_model or default_mdl)
