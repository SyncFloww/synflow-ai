from typing import Dict, Optional, Type
from .base import LLMProvider, ImageProvider, VideoProvider, VoiceProvider, AudioProvider

class LLMProviderRegistry:
    _providers: Dict[str, LLMProvider] = {}
    _default: Optional[str] = None

    @classmethod
    def register(cls, name: str, provider: LLMProvider, is_default: bool = False):
        cls._providers[name.lower()] = provider
        if is_default or cls._default is None:
            cls._default = name.lower()

    @classmethod
    def get(cls, name: Optional[str] = None) -> LLMProvider:
        key = (name or cls._default or "").lower()
        if key in cls._providers:
            return cls._providers[key]
        if cls._providers:
            return next(iter(cls._providers.values()))
        raise ValueError(f"No LLMProvider registered for '{name}'. Available: {list(cls._providers.keys())}")


class ImageProviderRegistry:
    _providers: Dict[str, ImageProvider] = {}
    _default: Optional[str] = None

    @classmethod
    def register(cls, name: str, provider: ImageProvider, is_default: bool = False):
        cls._providers[name.lower()] = provider
        if is_default or cls._default is None:
            cls._default = name.lower()

    @classmethod
    def get(cls, name: Optional[str] = None) -> ImageProvider:
        key = (name or cls._default or "").lower()
        if key in cls._providers:
            return cls._providers[key]
        if cls._providers:
            return next(iter(cls._providers.values()))
        raise ValueError(f"No ImageProvider registered for '{name}'. Available: {list(cls._providers.keys())}")


class VideoProviderRegistry:
    _providers: Dict[str, VideoProvider] = {}
    _default: Optional[str] = None

    @classmethod
    def register(cls, name: str, provider: VideoProvider, is_default: bool = False):
        cls._providers[name.lower()] = provider
        if is_default or cls._default is None:
            cls._default = name.lower()

    @classmethod
    def get(cls, name: Optional[str] = None) -> VideoProvider:
        key = (name or cls._default or "").lower()
        if key in cls._providers:
            return cls._providers[key]
        if cls._providers:
            return next(iter(cls._providers.values()))
        raise ValueError(f"No VideoProvider registered for '{name}'. Available: {list(cls._providers.keys())}")


class VoiceProviderRegistry:
    _providers: Dict[str, VoiceProvider] = {}
    _default: Optional[str] = None

    @classmethod
    def register(cls, name: str, provider: VoiceProvider, is_default: bool = False):
        cls._providers[name.lower()] = provider
        if is_default or cls._default is None:
            cls._default = name.lower()

    @classmethod
    def get(cls, name: Optional[str] = None) -> VoiceProvider:
        key = (name or cls._default or "").lower()
        if key in cls._providers:
            return cls._providers[key]
        if cls._providers:
            return next(iter(cls._providers.values()))
        raise ValueError(f"No VoiceProvider registered for '{name}'. Available: {list(cls._providers.keys())}")


class AudioProviderRegistry:
    _providers: Dict[str, AudioProvider] = {}
    _default: Optional[str] = None

    @classmethod
    def register(cls, name: str, provider: AudioProvider, is_default: bool = False):
        cls._providers[name.lower()] = provider
        if is_default or cls._default is None:
            cls._default = name.lower()

    @classmethod
    def get(cls, name: Optional[str] = None) -> AudioProvider:
        key = (name or cls._default or "").lower()
        if key in cls._providers:
            return cls._providers[key]
        if cls._providers:
            return next(iter(cls._providers.values()))
        raise ValueError(f"No AudioProvider registered for '{name}'. Available: {list(cls._providers.keys())}")
