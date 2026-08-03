from django.db import models
from django.contrib.auth.models import User
from social.models import Brand
from workspaces.models import Workspace
from ai_agents.models import GeneratedContent
from scheduler.models import Schedule

class Post(models.Model):
    PIPELINE_STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('review', 'Review'),
        ('approved', 'Approved'),
        ('scheduled', 'Scheduled'),
        ('publishing', 'Publishing'),
        ('published', 'Published'),
        ('failed', 'Failed'),
        ('archived', 'Archived'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    content = models.ForeignKey(GeneratedContent, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    title = models.CharField(max_length=255, blank=True, default='')
    caption = models.TextField()
    media_urls = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=PIPELINE_STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=100, default='UTC')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Post {self.id} ({self.status}) - {self.user.username}"

class PostPlatform(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('publishing', 'Publishing'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='platforms')
    platform = models.CharField(max_length=50) # instagram, facebook, linkedin, tiktok, x, youtube
    platform_post_id = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, default='')
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.post.id} on {self.platform} - {self.status}"

class PublishJob(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    schedule = models.ForeignKey(Schedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='publish_jobs')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='publish_jobs')
    scheduled_time = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempt_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    last_error = models.TextField(blank=True, default='')

    def __str__(self):
        return f"PublishJob for post {self.post.id} - {self.status}"

class PublishLog(models.Model):
    job = models.ForeignKey(PublishJob, on_delete=models.CASCADE, related_name='logs')
    status = models.CharField(max_length=20)
    message = models.TextField(blank=True, default='')
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PublishLog {self.id} for Job {self.job.id} [{self.status}]"
