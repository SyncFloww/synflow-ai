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
        with transaction.atomic():
            post.status = 'scheduled'
            post.scheduled_at = scheduled_at
            post.timezone = timezone_str
            post.save()

            # Update existing pending job or create new one
            job = post.publish_jobs.filter(status='pending').first()
            if job:
                job.scheduled_time = scheduled_at
                job.save()
            else:
                PublishJob.objects.create(
                    post=post,
                    scheduled_time=scheduled_at,
                    status='pending'
                )

        return post

    @staticmethod
    def publish_now(post: Post, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        with transaction.atomic():
            post.status = 'publishing'
            post.save()

            if platforms:
                # Remove existing post platforms not in list and add missing ones
                for plat in platforms:
                    PostPlatform.objects.get_or_create(post=post, platform=plat.lower())

            target_platforms = post.platforms.all()
            if not target_platforms.exists():
                PostPlatform.objects.create(post=post, platform='instagram')
                target_platforms = post.platforms.all()

            job, _ = PublishJob.objects.get_or_create(
                post=post,
                status__in=['pending', 'running'],
                defaults={'scheduled_time': timezone.now(), 'status': 'running', 'started_at': timezone.now()}
            )
            job.status = 'running'
            job.started_at = timezone.now()
            job.attempt_count += 1
            job.save()

            all_successful = True
            errors = []

            for pp in target_platforms:
                pp.status = 'publishing'
                pp.save()

                # Get connected account token if present
                social_account = SocialAccount.objects.filter(
                    brand=post.brand,
                    platform__iexact=pp.platform,
                    is_active=True
                ).first()

                access_token = social_account.access_token if social_account else None
                account_id = social_account.account_id if social_account else None

                publisher = get_publisher(pp.platform)
                res = publisher.publish(
                    caption=post.caption,
                    media_urls=post.media_urls,
                    access_token=access_token,
                    account_id=account_id
                )

                if res.get('success'):
                    pp.status = 'successful'
                    pp.platform_post_id = res.get('platform_post_id', '')
                    pp.published_at = timezone.now()
                    pp.error_message = ''
                    pp.save()

                    PublishLog.objects.create(
                        job=job,
                        status='success',
                        message=f"Successfully published to {pp.platform}",
                        details=res
                    )
                else:
                    all_successful = False
                    error_msg = res.get('error_message', 'Unknown publishing error')
                    pp.status = 'failed'
                    pp.error_message = error_msg
                    pp.save()
                    errors.append(f"{pp.platform}: {error_msg}")

                    PublishLog.objects.create(
                        job=job,
                        status='error',
                        message=f"Failed publishing to {pp.platform}: {error_msg}",
                        details=res
                    )

            if all_successful:
                post.status = 'published'
                post.published_at = timezone.now()
                post.save()

                job.status = 'completed'
                job.completed_at = timezone.now()
                job.save()
            else:
                if job.attempt_count >= job.max_retries:
                    post.status = 'failed'
                    post.save()
                    job.status = 'failed'
                    job.last_error = "; ".join(errors)
                    job.save()
                else:
                    # Keep job pending for retry
                    post.status = 'scheduled'
                    post.save()
                    job.status = 'pending'
                    job.last_error = "; ".join(errors)
                    job.save()

        return {
            'post_id': post.id,
            'status': post.status,
            'published_at': post.published_at.isoformat() if post.published_at else None,
            'job_status': job.status,
            'errors': errors
        }

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
