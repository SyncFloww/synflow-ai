import os
import json
from typing import Dict, Any, Optional
from google import genai
from google.genai import types

from content.models import Content, ContentVersion
from .models import GeneratedContent, ContentGeneration, AIModel

def get_gemini_client():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

class ContentGeneratorService:
    @staticmethod
    def generate_content(
        user,
        prompt: str,
        brand=None,
        platform: str = 'instagram',
        content_type: str = 'post',
        model_alias: str = 'gemini-3.5-flash'
    ) -> Dict[str, Any]:
        """
        Generates canonical content using Gemini API (or fallback template).
        """
        client = get_gemini_client()
        generated_text = ""

        context_str = ""
        if brand:
            context_str = f"\nBrand Name: {brand.name}\nIndustry: {getattr(brand, 'industry', 'General')}"

        full_prompt = f"Write a high-converting social media {content_type} for {platform}.\nTopic/Prompt: {prompt}\n{context_str}\nKeep it engaging with hashtags and call to action."

        if client:
            try:
                response = client.models.generate_content(
                    model=model_alias,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                    )
                )
                generated_text = response.text or ""
            except Exception:
                generated_text = f"✨ Exciting update for {brand.name if brand else 'our community'}! {prompt} #growth #{platform}"
        else:
            generated_text = f"✨ Exciting update for {brand.name if brand else 'our community'}! {prompt} #growth #{platform}"

        # Save to Content & GeneratedContent models
        workspace = brand.workspace if brand else None
        content = Content.objects.create(
            user=user,
            workspace=workspace,
            brand=brand,
            title=f"Campaign Content: {prompt[:30]}",
            text_content=generated_text,
            platform=platform
        )

        ContentVersion.objects.create(
            content=content,
            version_number=1,
            text_content=content.text_content
        )

        ai_model, _ = AIModel.objects.get_or_create(
            model_id=model_alias,
            defaults={'name': model_alias, 'provider': 'gemini'}
        )

        gen_record = GeneratedContent.objects.create(
            user=user,
            brand=brand,
            prompt_used=prompt,
            content_text=generated_text,
            platform=platform,
            model_used=ai_model
        )

        return {
            'content_id': content.id,
            'generated_content_id': gen_record.id,
            'generated_text': generated_text,
            'platform': platform
        }
