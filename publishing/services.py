from rest_framework.exceptions import APIException

class PublishingUnavailable(APIException):
    status_code = 503
    default_detail = 'Social publishing and scheduling are not enabled yet. Your draft has been kept.'

from django.utils import timezone
from django.db import transaction
from typing import List, Optional, Dict, Any

from .models import Post, PostPlatform, PublishJob, PublishLog
from .publishers import get_publisher
from social.models import SocialAccount

class PublishingService:
    @staticmethod
    def create_post(user, caption: str, media_urls: List[str] = None, brand=None, workspace=None, platforms: List[str] = None, scheduled_at=None, timezone_str: str = 'UTC') -> Post:
        media_urls = media_urls or []
        platforms = platforms or ['instagram']

        with transaction.atomic():
            post = Post.objects.create(
                user=user,
                workspace=workspace or (brand.workspace if brand else None),
                brand=brand,
                caption=caption,
                media_urls=media_urls,
                status='draft',
                scheduled_at=scheduled_at,
                timezone=timezone_str
            )

            for platform_name in platforms:
                PostPlatform.objects.create(
                    post=post,
                    platform=platform_name.lower(),
                    status='pending'
                )

            if scheduled_at:
                post.status = 'scheduled'
                post.save()
                PublishJob.objects.create(
                    post=post,
                    scheduled_time=scheduled_at,
                    status='pending'
                )

        return post

    @staticmethod
    def submit_for_review(post: Post) -> Post:
        if post.status in ['draft', 'failed']:
            post.status = 'review'
            post.save()
        return post

    @staticmethod
    def approve_post(post: Post) -> Post:
        if post.status in ['draft', 'review']:
            post.status = 'approved'
            post.save()
        return post

    @staticmethod
    def schedule_post(post: Post, scheduled_at, timezone_str: str = 'UTC') -> Post:
        raise PublishingUnavailable()

    @staticmethod
    def publish_now(post: Post, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        # Legacy adapters return simulated receipts. Keep drafts unchanged.
        raise PublishingUnavailable()

    @staticmethod
    def cancel_post(post: Post) -> Post:
        with transaction.atomic():
            post.status = 'archived'
            post.save()

            post.publish_jobs.filter(status='pending').update(status='cancelled')

            PublishLog.objects.filter(job__post=post).exists()
        return post

    @staticmethod
    def reschedule_post(post: Post, new_scheduled_at, timezone_str: str = 'UTC') -> Post:
        return PublishingService.schedule_post(post, new_scheduled_at, timezone_str)
