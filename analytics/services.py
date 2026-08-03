from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable, Optional
from django.utils import timezone
from .models import AnalyticsSnapshot, PlatformMetric, PostMetric, DailyAnalytics
from social.models import SocialAccount, Brand
from publishing.models import Post

class BaseAnalyticsProvider(ABC):
    """
    Abstract base class for analytics providers.
    Provides standardized interface for fetching social account & post metrics.
    """
    platform_name: str = "base"

    @abstractmethod
    def fetch_account_metrics(self, social_account: SocialAccount) -> Dict[str, Any]:
        """
        Returns account level metrics: followers_count, engagement_rate, posts_count, views_count, platform_metrics.
        """
        pass

    @abstractmethod
    def fetch_post_metrics(self, post: Post, platform: str) -> Dict[str, Any]:
        """
        Returns post level metrics: reach, impressions, clicks, likes, shares, comments, engagement_rate.
        """
        pass

class MockAnalyticsProvider(BaseAnalyticsProvider):
    def __init__(self, platform_name: str = "mock"):
        self.platform_name = platform_name

    def fetch_account_metrics(self, social_account: SocialAccount) -> Dict[str, Any]:
        return {
            'followers_count': 12500,
            'engagement_rate': 4.25,
            'posts_count': 142,
            'views_count': 89200,
            'metrics': {
                'likes': 1240,
                'shares': 310,
                'comments': 185,
                'clicks': 920,
                'impressions': 45000
            }
        }

    def fetch_post_metrics(self, post: Post, platform: str) -> Dict[str, Any]:
        return {
            'reach': 3400,
            'impressions': 5200,
            'clicks': 210,
            'likes': 380,
            'shares': 45,
            'comments': 28,
            'engagement_rate': 5.12
        }

class EventBus:
    """
    In-memory pub/sub event bus for decoupled event emission and automation handling.
    """
    _listeners: Dict[str, List[Callable]] = {}

    @classmethod
    def subscribe(cls, event_type: str, handler: Callable):
        if event_type not in cls._listeners:
            cls._listeners[event_type] = []
        cls._listeners[event_type].append(handler)

    @classmethod
    def publish(cls, event_type: str, payload: Dict[str, Any]):
        handlers = cls._listeners.get(event_type, [])
        for handler in handlers:
            try:
                handler(payload)
            except Exception as e:
                print(f"EventBus handler error for {event_type}: {e}")

class MetricsCollector:
    """
    Service responsible for collecting and storing metrics across accounts and posts.
    """
    @staticmethod
    def collect_account_snapshot(social_account: SocialAccount, provider: Optional[BaseAnalyticsProvider] = None) -> AnalyticsSnapshot:
        provider = provider or MockAnalyticsProvider(platform_name=social_account.platform)
        data = provider.fetch_account_metrics(social_account)

        snapshot = AnalyticsSnapshot.objects.create(
            user=social_account.user,
            brand=social_account.brand,
            social_account=social_account,
            platform=social_account.platform,
            followers_count=data.get('followers_count', 0),
            engagement_rate=data.get('engagement_rate', 0.0),
            posts_count=data.get('posts_count', 0),
            views_count=data.get('views_count', 0)
        )

        for name, val in data.get('metrics', {}).items():
            PlatformMetric.objects.create(snapshot=snapshot, name=name, value=val)

        EventBus.publish('analytics.snapshot_collected', {
            'snapshot_id': snapshot.id,
            'platform': social_account.platform,
            'user_id': social_account.user_id
        })

        return snapshot

    @staticmethod
    def collect_post_metrics(post: Post, platform: str, provider: Optional[BaseAnalyticsProvider] = None) -> PostMetric:
        provider = provider or MockAnalyticsProvider(platform_name=platform)
        data = provider.fetch_post_metrics(post, platform)

        pm, _ = PostMetric.objects.get_or_create(
            post=post,
            platform=platform,
            defaults=data
        )
        if not pm:
            for k, v in data.items():
                setattr(pm, k, v)
            pm.save()

        EventBus.publish('analytics.post_metrics_collected', {
            'post_id': post.id,
            'platform': platform
        })

        return pm

class AutomationEngine:
    """
    Automation engine foundation listening to events and triggering automated workflows.
    """
    @staticmethod
    def initialize():
        EventBus.subscribe('publishing.post_published', AutomationEngine.on_post_published)
        EventBus.subscribe('analytics.snapshot_collected', AutomationEngine.on_snapshot_collected)

    @staticmethod
    def on_post_published(payload: Dict[str, Any]):
        post_id = payload.get('post_id')
        print(f"[AutomationEngine] Processing post_published event for post_id: {post_id}")

    @staticmethod
    def on_snapshot_collected(payload: Dict[str, Any]):
        snapshot_id = payload.get('snapshot_id')
        print(f"[AutomationEngine] Processing snapshot_collected event for snapshot_id: {snapshot_id}")
