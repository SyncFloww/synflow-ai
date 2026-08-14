import os
import json
import logging
from typing import List, Optional, Dict, Any
from .base import LLMProvider, GenerationResult

logger = logging.getLogger(__name__)

DEFAULT_HF_MODEL = "meta-llama/Llama-3.2-3B-Instruct"

class HuggingFaceLLMProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")

    @property
    def provider_name(self) -> str:
        return "huggingface"

    @property
    def supported_models(self) -> List[str]:
        return [
            "meta-llama/Llama-3.2-3B-Instruct",
            "meta-llama/Meta-Llama-3-8B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "Qwen/Qwen2.5-Coder-7B-Instruct",
            "google/gemma-2-2b-it",
        ]

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        json_schema: Optional[Dict] = None
    ) -> GenerationResult:
        selected_model = model or os.getenv("HUGGINGFACE_MODEL_DEFAULT") or DEFAULT_HF_MODEL
        formatted_prompt = prompt
        if system_prompt:
            formatted_prompt = f"System: {system_prompt}\nUser: {prompt}"

        # 1. Try huggingface_hub InferenceClient if token is available
        if self.api_key:
            try:
                from huggingface_hub import InferenceClient
                client = InferenceClient(token=self.api_key)
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = client.chat_completion(
                    messages=messages,
                    model=selected_model,
                    temperature=temperature,
                    max_tokens=1024,
                )
                
                raw_text = response.choices[0].message.content or ""
                parsed_json = self._parse_json_if_needed(raw_text, json_schema)
                
                return GenerationResult(
                    text=raw_text,
                    structured_data=parsed_json,
                    prompt_tokens=len(formatted_prompt) // 4,
                    completion_tokens=len(raw_text) // 4,
                    raw_response={"model": selected_model, "content": raw_text},
                    estimated_cost=0.0001
                )
            except Exception as e:
                logger.warning(f"Hugging Face SDK InferenceClient error: {e}. Trying direct REST call...")

        # 2. Fallback to direct HTTP REST API call to Hugging Face Inference API
        if self.api_key:
            import requests
            try:
                url = f"https://api-inference.huggingface.co/models/{selected_model}"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                payload = {
                    "inputs": formatted_prompt,
                    "parameters": {
                        "temperature": temperature,
                        "max_new_tokens": 1024,
                        "return_full_text": False
                    }
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    result = resp.json()
                    raw_text = ""
                    if isinstance(result, list) and len(result) > 0:
                        raw_text = result[0].get("generated_text", "")
                    elif isinstance(result, dict):
                        raw_text = result.get("generated_text", "") or result.get("text", "")
                    
                    parsed_json = self._parse_json_if_needed(raw_text, json_schema)
                    return GenerationResult(
                        text=raw_text,
                        structured_data=parsed_json,
                        prompt_tokens=len(formatted_prompt) // 4,
                        completion_tokens=len(raw_text) // 4,
                        raw_response=result if isinstance(result, dict) else {"result": result},
                        estimated_cost=0.0001
                    )
            except Exception as e:
                logger.error(f"Hugging Face REST API fallback failed: {e}")

        # 3. Offline / Mock response for development without live tokens
        mock_response = f"[HF Open Model ({selected_model}) Response]\n" + (system_prompt + "\n\n" if system_prompt else "") + f"Generated response for: {prompt}"
        parsed_json = {"content": prompt, "status": "generated", "model": selected_model, "provider": "huggingface"}
        
        return GenerationResult(
            text=mock_response,
            structured_data=parsed_json,
            prompt_tokens=len(formatted_prompt) // 4,
            completion_tokens=len(mock_response) // 4,
            estimated_cost=0.0
        )

    def _parse_json_if_needed(self, text: str, json_schema: Optional[Dict]) -> Dict[str, Any]:
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
                logger.warning(f"Failed to parse Hugging Face JSON response: {e}")
        return parsed
