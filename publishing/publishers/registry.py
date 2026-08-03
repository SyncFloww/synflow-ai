from typing import Dict
from .base import BasePublisher
from .instagram import InstagramPublisher
from .facebook import FacebookPublisher
from .linkedin import LinkedInPublisher
from .tiktok import TikTokPublisher
from .x import XPublisher
from .youtube import YouTubePublisher

class PublisherRegistry:
    _publishers: Dict[str, BasePublisher] = {}
    _initialized: bool = False

    @classmethod
    def _init_default(cls):
        if cls._initialized:
            return
        cls.register('instagram', InstagramPublisher())
        cls.register('facebook', FacebookPublisher())
        cls.register('linkedin', LinkedInPublisher())
        cls.register('tiktok', TikTokPublisher())
        x_pub = XPublisher()
        cls.register('x', x_pub)
        cls.register('twitter', x_pub)
        cls.register('youtube', YouTubePublisher())
        cls._initialized = True

    @classmethod
    def register(cls, platform_name: str, publisher: BasePublisher):
        cls._publishers[platform_name.lower()] = publisher

    @classmethod
    def get_publisher(cls, platform_name: str) -> BasePublisher:
        cls._init_default()
        name = platform_name.lower()
        if name in cls._publishers:
            return cls._publishers[name]
        # Fallback to InstagramPublisher for unknown platform
        return InstagramPublisher()

def get_publisher(platform_name: str) -> BasePublisher:
    return PublisherRegistry.get_publisher(platform_name)
