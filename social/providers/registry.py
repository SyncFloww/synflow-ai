from typing import Dict, List, Type, Optional, Any
from .base import BaseSocialProvider
from .mock import MockSocialProvider
from .instagram import InstagramOAuthProvider
from .facebook import FacebookOAuthProvider
from .linkedin import LinkedInOAuthProvider
from .tiktok import TikTokOAuthProvider
from .x import XOAuthProvider
from .youtube import YouTubeOAuthProvider

SUPPORTED_PLATFORMS = ['instagram', 'facebook', 'linkedin', 'tiktok', 'x', 'twitter', 'youtube']

class ProviderRegistry:
    """
    Registry for managing Social Media OAuth Providers.
    Registers concrete provider implementations (Instagram, Facebook, LinkedIn, TikTok, X/Twitter, YouTube)
    and supports dynamic fallback to MockSocialProvider for development.
    """
    _providers: Dict[str, BaseSocialProvider] = {}
    _initialized: bool = False

    @classmethod
    def _init_default_providers(cls):
        if cls._initialized:
            return
        cls.register('instagram', InstagramOAuthProvider())
        cls.register('facebook', FacebookOAuthProvider())
        cls.register('linkedin', LinkedInOAuthProvider())
        cls.register('tiktok', TikTokOAuthProvider())
        x_provider = XOAuthProvider()
        cls.register('x', x_provider)
        cls.register('twitter', x_provider)
        cls.register('youtube', YouTubeOAuthProvider())
        cls._initialized = True

    @classmethod
    def register(cls, provider_name: str, provider_instance: BaseSocialProvider):
        cls._providers[provider_name.lower()] = provider_instance

    @classmethod
    def get_provider(cls, provider_name: str) -> BaseSocialProvider:
        cls._init_default_providers()
        name = provider_name.lower()
        if name in cls._providers:
            return cls._providers[name]
        if name in SUPPORTED_PLATFORMS:
            mock = MockSocialProvider(provider_name=name)
            cls._providers[name] = mock
            return mock
        raise ValueError(f"Unsupported social provider: '{provider_name}'. Supported providers: {', '.join(SUPPORTED_PLATFORMS)}")

    @classmethod
    def list_providers(cls) -> List[Dict[str, Any]]:
        cls._init_default_providers()
        result = []
        display_names = {
            'instagram': 'Instagram',
            'facebook': 'Facebook',
            'linkedin': 'LinkedIn',
            'tiktok': 'TikTok',
            'x': 'X (Twitter)',
            'twitter': 'X (Twitter)',
            'youtube': 'YouTube'
        }
        seen = set()
        for name in SUPPORTED_PLATFORMS:
            if name in seen:
                continue
            seen.add(name)
            provider = cls._providers.get(name) or MockSocialProvider(provider_name=name)
            is_mock = isinstance(provider, MockSocialProvider)
            result.append({
                'name': name,
                'display_name': display_names.get(name, name.capitalize()),
                'mode': 'mock' if is_mock else 'production',
                'is_supported': True
            })
        return result

def get_provider(provider_name: str) -> BaseSocialProvider:
    return ProviderRegistry.get_provider(provider_name)

def list_providers() -> List[Dict[str, Any]]:
    return ProviderRegistry.list_providers()
