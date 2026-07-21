import uuid
from django.db import models
from django.conf import settings
from workspaces.models import Workspace
from content.models import Content
from social_accounts.models import SocialAccount

class Post(models.Model):
    """
    Represents a social media post constructed from a piece of Content.
    """
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHING = "publishing", "Publishing"
        PUBLISHED = "published", "Published"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="posts")
    content = models.ForeignKey(Content, on_delete=models.SET_NULL, null=True, related_name="posts")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # Optional override for the post text. If blank, use content.text_content
    post_text = models.TextField(blank=True)
    media_assets = models.ManyToManyField("content.MediaAsset", blank=True, related_name="posts")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Post for {self.content}"

class Schedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name="schedule")
    scheduled_time = models.DateTimeField()
    timezone = models.CharField(max_length=50, default="UTC")
    is_active = models.BooleanField(default=True)
    
    # We will store the ID of the Celery PeriodicTask here if we use celery beat programmatically
    celery_task_id = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

class PostPlatform(models.Model):
    """
    Maps a Post to specific Social Accounts where it should be published.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="platforms")
    social_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE)
    
    # Platform-specific overrides
    custom_text = models.TextField(blank=True, help_text="Overrides the generic Post text for this specific platform")
    
    def __str__(self):
        return f"{self.social_account.platform} - {self.post.id}"

class PublishJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post_platform = models.ForeignKey(PostPlatform, on_delete=models.CASCADE, related_name="jobs")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PublishResult(models.Model):
    """
    Logs the outcome of a PublishJob.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField(PublishJob, on_delete=models.CASCADE, related_name="result")
    
    success = models.BooleanField()
    platform_post_id = models.CharField(max_length=255, blank=True)
    platform_post_url = models.URLField(blank=True)
    error_message = models.TextField(blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
