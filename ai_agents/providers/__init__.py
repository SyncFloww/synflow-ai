from .base import (
    AIProvider,
    LLMProvider,
    ImageProvider,
    VideoProvider,
    VoiceProvider,
    AudioProvider,
    GenerationResult,
    MediaResult,
    VoiceResult,
    CaptionResult,
)
from .registries import (
    LLMProviderRegistry,
    ImageProviderRegistry,
    VideoProviderRegistry,
    VoiceProviderRegistry,
    AudioProviderRegistry,
)
from .llm import GoogleGeminiProvider, OpenAIProvider, DeepSeekProvider
from .huggingface import HuggingFaceLLMProvider
from .litellm import LiteLLMProvider
from .ollama import OllamaProvider
from .image import FalAIImageProvider, ReplicateImageProvider, GeminiImageProvider
from .video import RunwayVideoProvider, ReplicateVideoProvider
from .voice import MurfVoiceProvider
from .audio_media import FFmpegAudioProcessor

# Register default providers
LLMProviderRegistry.register("gemini", GoogleGeminiProvider(), is_default=True)
LLMProviderRegistry.register("openai", OpenAIProvider())
LLMProviderRegistry.register("deepseek", DeepSeekProvider())
LLMProviderRegistry.register("huggingface", HuggingFaceLLMProvider())
LLMProviderRegistry.register("litellm", LiteLLMProvider())
LLMProviderRegistry.register("ollama", OllamaProvider())

ImageProviderRegistry.register("fal", FalAIImageProvider(), is_default=True)
ImageProviderRegistry.register("replicate", ReplicateImageProvider())
ImageProviderRegistry.register("gemini", GeminiImageProvider())

VideoProviderRegistry.register("runway", RunwayVideoProvider(), is_default=True)
VideoProviderRegistry.register("replicate", ReplicateVideoProvider())

VoiceProviderRegistry.register("murf", MurfVoiceProvider(), is_default=True)

AudioProviderRegistry.register("ffmpeg", FFmpegAudioProcessor(), is_default=True)
