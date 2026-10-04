"""Bounded, server-configured inference. Never substitutes simulated output."""
import json
import os
import requests
from rest_framework.exceptions import APIException
from ai_agents.providers.base import GenerationResult


class AIUnavailable(APIException):
    status_code = 503
    default_detail = 'AI is unavailable or its free quota is exhausted. Please try again later.'
    default_code = 'ai_unavailable'


def generate_text(prompt, system_prompt='', json_output=False):
    provider = os.getenv('AI_PROVIDER', 'gemini').strip().lower()
    try:
        if provider == 'huggingface':
            token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_API_KEY')
            model = os.getenv('AI_MODEL') or os.getenv('HUGGINGFACE_MODEL_DEFAULT')
            if not token or not model:
                raise AIUnavailable('The AI provider is not configured yet.')
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}]
            payload = {'model': model, 'messages': messages, 'max_tokens': 1800, 'temperature': 0.7}
            if json_output:
                payload['response_format'] = {'type': 'json_object'}
            response = requests.post('https://router.huggingface.co/v1/chat/completions',
                headers={'Authorization': f'Bearer {token}'}, json=payload, timeout=(5, 45))
            response.raise_for_status()
            data = response.json()
            text = data['choices'][0]['message']['content']
        elif provider == 'gemini':
            token = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_GENAI_API_KEY')
            model = os.getenv('AI_MODEL', '')
            if not token or not model:
                raise AIUnavailable('The AI provider or model is not configured yet.')
            # Restrict model names to a single path segment.
            if not model.replace('-', '').replace('.', '').replace('_', '').isalnum():
                raise AIUnavailable('The configured AI model is invalid.')
            config = {'temperature': 0.7, 'maxOutputTokens': 2400}
            if json_output:
                config['responseMimeType'] = 'application/json'
            response = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                headers={'x-goog-api-key': token}, timeout=(5, 45), json={
                    'systemInstruction': {'parts': [{'text': system_prompt}]},
                    'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
                    'generationConfig': config,
                })
            response.raise_for_status()
            data = response.json()
            text = ''.join(p.get('text', '') for p in data['candidates'][0]['content']['parts'] if not p.get('thought'))
        else:
            raise AIUnavailable('Choose a supported AI provider in the server settings.')
        if not isinstance(text, str) or not text.strip():
            raise AIUnavailable()
        structured = None
        if json_output:
            from .output_parser import OutputParser
            structured = OutputParser().parse_json(text)
            if not isinstance(structured, dict) or not structured:
                raise AIUnavailable('The AI response was incomplete. Please try again.')
        return GenerationResult(text=text, structured_data=structured or {}, raw_response={'provider': provider, 'model': model})
    except AIUnavailable:
        raise
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        # Never expose provider response bodies, API keys, or submitted brand context.
        raise AIUnavailable() from None
