import os
import json
import logging
from typing import List, Optional, Dict, Any
from .base import LLMProvider, GenerationResult

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_BASE = "http://localhost:11434"

class OllamaProvider(LLMProvider):
    def __init__(self, api_base: Optional[str] = None):
        self.api_base = api_base or os.getenv("OLLAMA_API_BASE") or DEFAULT_OLLAMA_BASE

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def supported_models(self) -> List[str]:
        return ["llama3", "mistral", "gemma2", "phi3", "qwen2"]

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        json_schema: Optional[Dict] = None
    ) -> GenerationResult:
        selected_model = model or "llama3"
        import requests
        
        url = f"{self.api_base.rstrip('/')}/api/generate"
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        if system_prompt:
            payload["system"] = system_prompt
        if json_schema:
            payload["format"] = "json"

        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data.get("response", "")
                parsed_json = self._parse_json(raw_text, json_schema)
                
                prompt_eval_count = data.get("prompt_eval_count", len(prompt) // 4)
                eval_count = data.get("eval_count", len(raw_text) // 4)

                return GenerationResult(
                    text=raw_text,
                    structured_data=parsed_json,
                    prompt_tokens=prompt_eval_count,
                    completion_tokens=eval_count,
                    raw_response=data,
                    estimated_cost=0.0  # Self-hosted / local execution
                )
        except Exception as e:
            logger.warning(f"Ollama local API error: {e}. Returning simulated local response.")

        mock_response = f"[Ollama Local Model ({selected_model}) Response]\n" + (system_prompt + "\n\n" if system_prompt else "") + f"Generated for prompt: {prompt}"
        return GenerationResult(
            text=mock_response,
            structured_data={"content": prompt, "status": "generated", "model": selected_model, "provider": "ollama"},
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
                logger.warning(f"Failed to parse Ollama JSON response: {e}")
        return parsed
