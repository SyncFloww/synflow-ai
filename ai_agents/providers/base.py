from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import time

@dataclass
class GenerationResult:
    text: str = ""
    structured_data: Dict[str, Any] = field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw_response: Dict[str, Any] = field(default_factory=dict)
    estimated_cost: float = 0.0

@dataclass
class MediaResult:
    media_url: str = ""
    file_name: str = ""
    mime_type: str = "image/png"
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    file_size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    estimated_cost: float = 0.0

@dataclass
class VoiceResult:
    audio_url: str = ""
    format: str = "mp3"
    duration: float = 0.0
    word_timings: List[Dict[str, Any]] = field(default_factory=list) # [{word, start_time, end_time}]
    metadata: Dict[str, Any] = field(default_factory=dict)
    estimated_cost: float = 0.0

@dataclass
class CaptionResult:
    srt_content: str = ""
    vtt_content: str = ""
    segments: List[Dict[str, Any]] = field(default_factory=list)
    word_timings: List[Dict[str, Any]] = field(default_factory=list)

class AIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        pass

    def is_available(self) -> bool:
        return True

class LLMProvider(AIProvider):
    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None, temperature: float = 0.7, json_schema: Optional[Dict] = None) -> GenerationResult:
        pass

class ImageProvider(AIProvider):
    @abstractmethod
    def generate_image(self, prompt: str, model: Optional[str] = None, aspect_ratio: str = "1:1", negative_prompt: str = "", reference_image_url: Optional[str] = None, style: str = "") -> MediaResult:
        pass

class VideoProvider(AIProvider):
    @abstractmethod
    def generate_video(self, prompt: str, model: Optional[str] = None, image_url: Optional[str] = None, aspect_ratio: str = "16:9", duration_seconds: int = 5) -> MediaResult:
        pass

class VoiceProvider(AIProvider):
    @abstractmethod
    def list_voices(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def generate_voiceover(self, text: str, voice_id: str, language: str = "en", style: str = "", speed: float = 1.0, pitch: int = 0) -> VoiceResult:
        pass

class AudioProvider(AIProvider):
    @abstractmethod
    def mix_audio_tracks(self, tracks: List[Dict[str, Any]], output_format: str = "mp3") -> MediaResult:
        pass
