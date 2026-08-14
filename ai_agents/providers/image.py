import os
import logging
import requests
import uuid
from typing import List, Optional
from .base import ImageProvider, MediaResult

logger = logging.getLogger(__name__)

class FalAIImageProvider(ImageProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FAL_KEY") or os.getenv("FAL_AI_API_KEY")

    @property
    def provider_name(self) -> str:
        return "fal.ai"

    @property
    def supported_models(self) -> List[str]:
        return ["fal-ai/flux/schnell", "fal-ai/flux/dev", "fal-ai/fast-sdxl"]

    def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        aspect_ratio: str = "1:1",
        negative_prompt: str = "",
        reference_image_url: Optional[str] = None,
        style: str = ""
    ) -> MediaResult:
        selected_model = model or "fal-ai/flux/schnell"
        
        # Determine width and height from aspect ratio
        ratio_map = {
            "1:1": (1024, 1024),
            "4:5": (1024, 1280),
            "9:16": (768, 1344),
            "16:9": (1344, 768)
        }
        width, height = ratio_map.get(aspect_ratio, (1024, 1024))
        
        if self.api_key:
            try:
                headers = {
                    "Authorization": f"Key {self.api_key}",
                    "Content-Type": "application/json"
                }
                enhanced_prompt = f"{prompt}, {style}" if style else prompt
                payload = {
                    "prompt": enhanced_prompt,
                    "image_size": {
                        "width": width,
                        "height": height
                    },
                    "num_images": 1
                }
                if negative_prompt:
                    payload["negative_prompt"] = negative_prompt

                response = requests.post(
                    f"https://fal.run/{selected_model}",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                if response.status_code == 200:
                    data = response.json()
                    images = data.get("images", [])
                    if images:
                        image_url = images[0].get("url")
                        return MediaResult(
                            media_url=image_url,
                            file_name=f"generated_{uuid.uuid4().hex[:8]}.png",
                            mime_type="image/png",
                            width=width,
                            height=height,
                            metadata={"prompt": prompt, "provider": "fal.ai", "model": selected_model, "aspect_ratio": aspect_ratio},
                            estimated_cost=0.003
                        )
            except Exception as e:
                logger.error(f"fal.ai image generation error: {e}")

        # Fallback to SVG placeholder / placeholder image generator
        placeholder_url = f"https://picsum.photos/{width}/{height}?random={uuid.uuid4().hex[:6]}"
        return MediaResult(
            media_url=placeholder_url,
            file_name=f"image_{uuid.uuid4().hex[:8]}.png",
            mime_type="image/png",
            width=width,
            height=height,
            metadata={"prompt": prompt, "provider": "fal.ai (preview)", "aspect_ratio": aspect_ratio},
            estimated_cost=0.0
        )


class ReplicateImageProvider(ImageProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("REPLICATE_API_TOKEN")

    @property
    def provider_name(self) -> str:
        return "replicate"

    @property
    def supported_models(self) -> List[str]:
        return ["black-forest-labs/flux-schnell", "stability-ai/sdxl"]

    def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        aspect_ratio: str = "1:1",
        negative_prompt: str = "",
        reference_image_url: Optional[str] = None,
        style: str = ""
    ) -> MediaResult:
        ratio_map = {
            "1:1": (1024, 1024),
            "4:5": (1024, 1280),
            "9:16": (768, 1344),
            "16:9": (1344, 768)
        }
        width, height = ratio_map.get(aspect_ratio, (1024, 1024))
        
        if self.api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "version": "554244515b4d3d85f34803f26bde3cc9c2d30d08e38a52e7208c14438e65f49e",
                    "input": {
                        "prompt": prompt,
                        "aspect_ratio": aspect_ratio
                    }
                }
                resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload, timeout=30)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    # If synchronous output or get prediction url
                    output = data.get("output")
                    if output and isinstance(output, list):
                        return MediaResult(
                            media_url=output[0],
                            file_name=f"replicate_{uuid.uuid4().hex[:8]}.png",
                            mime_type="image/png",
                            width=width,
                            height=height,
                            metadata={"prompt": prompt, "provider": "replicate"},
                            estimated_cost=0.003
                        )
            except Exception as e:
                logger.error(f"Replicate image generation error: {e}")

        # Fallback to FalAI or placeholder
        return FalAIImageProvider().generate_image(prompt, model, aspect_ratio, negative_prompt, reference_image_url, style)


class GeminiImageProvider(ImageProvider):
    @property
    def provider_name(self) -> str:
        return "gemini-imagen"

    @property
    def supported_models(self) -> List[str]:
        return ["imagen-3.0-generate-002"]

    def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        aspect_ratio: str = "1:1",
        negative_prompt: str = "",
        reference_image_url: Optional[str] = None,
        style: str = ""
    ) -> MediaResult:
        # Fallback to fal.ai or mock
        return FalAIImageProvider().generate_image(prompt, model, aspect_ratio, negative_prompt, reference_image_url, style)
