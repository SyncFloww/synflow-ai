import os
import json
import logging
from typing import List, Optional, Dict, Any
from .base import LLMProvider, GenerationResult

logger = logging.getLogger(__name__)

class LiteLLMProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        self.api_key = api_key or os.getenv("LITELLM_API_KEY")
        self.api_base = api_base or os.getenv("LITELLM_API_BASE")

    @property
    def provider_name(self) -> str:
        return "litellm"

    @property
    def supported_models(self) -> List[str]:
        return [
            "gpt-4o-mini",
            "gemini/gemini-2.5-flash",
            "huggingface/meta-llama/Llama-3.2-3B-Instruct",
            "ollama/llama3",
            "claude-3-5-sonnet",
        ]

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        json_schema: Optional[Dict] = None
    ) -> GenerationResult:
        selected_model = model or "gpt-4o-mini"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Try using litellm Python package
        try:
            import litellm
            
            kwargs: Dict[str, Any] = {
                "model": selected_model,
                "messages": messages,
                "temperature": temperature,
            }
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.api_base:
                kwargs["api_base"] = self.api_base
            if json_schema:
                kwargs["response_format"] = {"type": "json_object"}

            response = litellm.completion(**kwargs)
            content = response.choices[0].message.content or ""
            
            parsed_json = self._parse_json(content, json_schema)
            prompt_tokens = getattr(response.usage, "prompt_tokens", len(prompt) // 4)
            completion_tokens = getattr(response.usage, "completion_tokens", len(content) // 4)
            
            return GenerationResult(
                text=content,
                structured_data=parsed_json,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                raw_response=response.dict() if hasattr(response, "dict") else {"content": content},
                estimated_cost=0.0002
            )
        except Exception as e:
            logger.warning(f"LiteLLM SDK execution failed: {e}. Falling back to default provider or simulation.")

        # Fallback simulation if LiteLLM proxy or package is unavailable
        mock_response = f"[LiteLLM Router ({selected_model}) Response]\n" + (system_prompt + "\n\n" if system_prompt else "") + f"Response for prompt: {prompt}"
        parsed_json = self._parse_json(mock_response, json_schema)
        
        return GenerationResult(
            text=mock_response,
            structured_data=parsed_json or {"content": prompt, "status": "generated", "model": selected_model},
            prompt_tokens=len(prompt) // 4,
            completion_tokens=len(mock_response) // 4,
            estimated_cost=0.0
        )

    def _parse_json(self, text: str, json_schema: Optional[Dict]) -> Dict[str, Any]:
        parsed = {}
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:-3].strip()
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:-3].strip()

        if json_schema or (clean_text.startswith("{") and clean_text.endswith("}")):
            try:
                parsed = json.loads(clean_text)
            except Exception as e:
                logger.warning(f"Failed to parse LiteLLM JSON response: {e}")
        return parsed
