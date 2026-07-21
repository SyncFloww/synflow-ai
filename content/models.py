import uuid
from django.db import models
from django.conf import settings
from workspaces.models import Workspace

class ContentFolder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="folders")
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ('workspace', 'name', 'parent')

    def __str__(self):
        return self.name

class ContentTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default="#000000")

    class Meta:
        unique_together = ('workspace', 'name')

    def __str__(self):
        return self.name

class MediaAsset(models.Model):
    """
    Local file storage for Phase 1. S3 will be added in Phase 2.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="media_assets")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to="media_assets/%Y/%m/%d/")
    file_type = models.CharField(max_length=50) # 'image/jpeg', 'video/mp4'
    size_bytes = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class Content(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEW = "review", "In Review"
        APPROVED = "approved", "Approved"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="contents")
    brand = models.ForeignKey('brands.Brand', on_delete=models.SET_NULL, null=True, blank=True, related_name="contents")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="authored_contents")
    folder = models.ForeignKey(ContentFolder, on_delete=models.SET_NULL, null=True, blank=True, related_name="contents")
    tags = models.ManyToManyField(ContentTag, blank=True)
    media_assets = models.ManyToManyField(MediaAsset, blank=True)
    
    title = models.CharField(max_length=255, blank=True)
    text_content = models.TextField(blank=True) # Current active text
    content_type = models.CharField(max_length=50, blank=True, help_text="e.g., Post, Article, Thread")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"Content {self.id}"

class ContentVersion(models.Model):
    """
    Tracks edits to the content text.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="versions")
    text_content = models.TextField()
    edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Version of {self.content.id} at {self.created_at}"
