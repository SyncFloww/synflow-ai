from celery import shared_task
from .models import PublishJob, Schedule
from .services import MockSocialProviderService

@shared_task
def process_publish_job(job_id):
    try:
        job = PublishJob.objects.get(id=job_id)
        MockSocialProviderService.publish_post(job)
    except PublishJob.DoesNotExist:
        pass

@shared_task
def process_schedule(schedule_id):
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        if not schedule.is_active:
            return
            
        post = schedule.post
        for platform in post.platforms.all():
            job = PublishJob.objects.create(post_platform=platform)
            process_publish_job.delay(job.id)
            
        schedule.is_active = False
        schedule.save()
        
    except Schedule.DoesNotExist:
        pass
