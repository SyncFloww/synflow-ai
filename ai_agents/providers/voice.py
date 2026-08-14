import os
import logging
import requests
import uuid
import json
from typing import List, Optional, Dict, Any
from .base import VoiceProvider, VoiceResult

logger = logging.getLogger(__name__)

# Standard Murf default voices reference list if offline
DEFAULT_MURF_VOICES = [
    {"voice_id": "en-US-marcus", "name": "Marcus", "gender": "male", "locale": "en-US", "accent": "American", "model": "GEN2", "style": "Conversational"},
    {"voice_id": "en-US-natalie", "name": "Natalie", "gender": "female", "locale": "en-US", "accent": "American", "model": "GEN2", "style": "Promo / Energetic"},
    {"voice_id": "en-UK-hazel", "name": "Hazel", "gender": "female", "locale": "en-GB", "accent": "British", "model": "GEN2", "style": "Corporate / Professional"},
    {"voice_id": "en-US-falcon-sam", "name": "Sam (Low Latency)", "gender": "male", "locale": "en-US", "accent": "American", "model": "FALCON_2", "style": "Natural"},
    {"voice_id": "es-ES-alvaro", "name": "Alvaro", "gender": "male", "locale": "es-ES", "accent": "Spanish", "model": "GEN2", "style": "Narrative"},
    {"voice_id": "fr-FR-camille", "name": "Camille", "gender": "female", "locale": "fr-FR", "accent": "French", "model": "GEN2", "style": "Conversational"},
    {"voice_id": "de-DE-jonas", "name": "Jonas", "gender": "male", "locale": "de-DE", "accent": "German", "model": "GEN2", "style": "Professional"},
]

class MurfVoiceProvider(VoiceProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MURF_API_KEY")

    @property
    def provider_name(self) -> str:
        return "murf"

    @property
    def supported_models(self) -> List[str]:
        return ["GEN2", "FALCON_2"]

    def list_voices(self) -> List[Dict[str, Any]]:
        if self.api_key:
            try:
                headers = {"api-key": self.api_key, "accept": "application/json"}
                resp = requests.get("https://api.murf.ai/v1/speech/voices", headers=headers, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data
            except Exception as e:
                logger.error(f"Error fetching Murf voices: {e}")
        return DEFAULT_MURF_VOICES

    def generate_voiceover(
        self,
        text: str,
        voice_id: str,
        language: str = "en",
        style: str = "",
        speed: float = 1.0,
        pitch: int = 0
    ) -> VoiceResult:
        selected_voice = voice_id or "en-US-natalie"
        
        # Calculate simulated word timing data
        words = text.split()
        word_timings = []
        current_time = 0.0
        sec_per_word = 0.4 / max(0.5, speed)
        
        for w in words:
            start = round(current_time, 2)
            end = round(current_time + sec_per_word, 2)
            word_timings.append({
                "word": w,
                "start_time": start,
                "end_time": end
            })
            current_time = end

        total_duration = round(current_time, 2)

        if self.api_key:
            try:
                headers = {
                    "api-key": self.api_key,
                    "Content-Type": "application/json",
                    "accept": "application/json"
                }
                payload = {
                    "voiceId": selected_voice,
                    "text": text,
                    "rate": int((speed - 1.0) * 100),
                    "pitch": pitch,
                    "encodeAs": "MP3",
                    "modelVersion": "GEN2" if "falcon" not in selected_voice.lower() else "FALCON_2"
                }
                if style:
                    payload["style"] = style

                resp = requests.post("https://api.murf.ai/v1/speech/generate", headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    audio_url = data.get("audioFile") or data.get("audio_url")
                    returned_timings = data.get("wordDurations") or data.get("word_timings") or word_timings
                    return VoiceResult(
                        audio_url=audio_url,
                        format="mp3",
                        duration=data.get("audioLengthInSeconds", total_duration),
                        word_timings=returned_timings,
                        metadata={"voice_id": selected_voice, "provider": "murf", "text": text},
                        estimated_cost=0.005
                    )
            except Exception as e:
                logger.error(f"Murf voice generation error: {e}")

        # Fallback audio output preview
        sample_audio = "https://actions.google.com/sounds/v1/ambiences/outdoor_synth.ogg"
        return VoiceResult(
            audio_url=sample_audio,
            format="mp3",
            duration=total_duration,
            word_timings=word_timings,
            metadata={"voice_id": selected_voice, "provider": "murf (preview)", "text": text},
            estimated_cost=0.0
        )
