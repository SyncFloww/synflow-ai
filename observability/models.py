import uuid
from django.db import models
from django.conf import settings
from workspaces.models import Workspace

class ActivityLog(models.Model):
    """
    User-facing activity history for audit trails (e.g. "User X generated a post").
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="activity_logs", null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    entity_type = models.CharField(max_length=100, blank=True)
    entity_id = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.action} at {self.created_at}"

class ErrorLog(models.Model):
    """
    System-level errors for developer visibility (e.g. API failures).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True, blank=True)
    module = models.CharField(max_length=100) # e.g., "content_ai", "publishing"
    error_message = models.TextField()
    stack_trace = models.TextField(blank=True)
    context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Error in {self.module} at {self.created_at}"

class JobExecutionLog(models.Model):
    """
    Detailed logs for asynchronous background jobs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_name = models.CharField(max_length=255) # e.g. "process_publish_job"
    job_id = models.CharField(max_length=255, blank=True) # Celery task ID
    status = models.CharField(max_length=50) # "started", "success", "failed"
    result = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Job {self.job_name} ({self.status})"
