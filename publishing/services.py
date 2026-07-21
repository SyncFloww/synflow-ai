import time
from django.utils import timezone
from .models import PublishJob, PublishResult

class MockSocialProviderService:
    @staticmethod
    def publish_post(job: PublishJob):
        """
        Simulates publishing a post to a social platform.
        Updates the PublishJob and creates a PublishResult.
        """
        job.status = PublishJob.Status.PROCESSING
        job.started_at = timezone.now()
        job.save()
        
        # Simulate network latency
        time.sleep(1)
        
        platform = job.post_platform.social_account.platform
        text = job.post_platform.custom_text or job.post_platform.post.post_text or job.post_platform.post.content.text_content
        
        try:
            # Simulate failure condition (e.g. if the word 'fail' is in the text)
            if "fail" in text.lower():
                raise Exception("Simulated network or API error")
                
            job.status = PublishJob.Status.SUCCESS
            job.completed_at = timezone.now()
            job.save()
            
            PublishResult.objects.create(
                job=job,
                success=True,
                platform_post_id=f"mock_{platform}_{job.id}",
                platform_post_url=f"https://{platform}.com/mock_post/{job.id}",
                raw_response={"status": 200, "message": "Successfully published"}
            )
            
        except Exception as e:
            try:
                from observability.models import ErrorLog
                ErrorLog.objects.create(
                    workspace=job.post_platform.post.workspace,
                    module="publishing",
                    error_message=str(e),
                    context={"job_id": str(job.id), "platform": platform}
                )
            except ImportError:
                pass
                
            job.status = PublishJob.Status.FAILED
            job.completed_at = timezone.now()
            job.save()
            
            PublishResult.objects.create(
                job=job,
                success=False,
                error_message=str(e),
                raw_response={"status": 500, "error": str(e)}
            )


class SchedulingService:
    @staticmethod
    def schedule_post(schedule):
        """
        Integrates with Celery Beat to trigger the publish job at the scheduled time.
        For Phase 1 MVP, we will rely on a periodic task that sweeps the DB for due schedules.
        """
        pass

    @staticmethod
    def process_due_schedules():
        """
        Periodic task logic to find schedules that are due and publish them idempotently.
        """
        from .models import Schedule, Post, PublishJob
        from django.db import transaction

        due_schedules = Schedule.objects.filter(
            is_active=True, 
            scheduled_time__lte=timezone.now(),
            post__status=Post.Status.SCHEDULED
        )

        for schedule in due_schedules:
            with transaction.atomic():
                # Lock the post to prevent concurrent execution
                post = Post.objects.select_for_update().filter(
                    id=schedule.post.id, 
                    status=Post.Status.SCHEDULED
                ).first()
                
                if not post:
                    continue # Someone else picked it up or it's not SCHEDULED

                # State Transition: SCHEDULED -> PUBLISHING
                post.status = Post.Status.PUBLISHING
                post.save(update_fields=['status'])
                
                # We mark the schedule inactive now
                schedule.is_active = False
                schedule.save(update_fields=['is_active'])

            # Now publish to all attached platforms
            for platform in post.platforms.all():
                job = PublishJob.objects.create(
                    post_platform=platform,
                    status=PublishJob.Status.PENDING
                )
                MockSocialProviderService.publish_post(job)
                
            # Verify if all jobs succeeded
            has_failure = post.platforms.filter(jobs__status=PublishJob.Status.FAILED).exists()
            
            # State Transition: PUBLISHING -> PUBLISHED or FAILED
            if has_failure:
                post.status = Post.Status.FAILED
            else:
                post.status = Post.Status.PUBLISHED
                
            post.save(update_fields=['status'])
