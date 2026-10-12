from django.db import models
from django.conf import settings
from .models import Brand

class MetaSession(models.Model):
    nonce = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

class MetaConnection(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    platform = models.CharField(max_length=20)
    remote_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    encrypted_token = models.TextField()
    active = models.BooleanField(default=True)
    auto_reply = models.BooleanField(default=False)
    reply_enabled_at = models.DateTimeField(null=True, blank=True)
    automation_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('brand', 'platform', 'remote_id')

class MetaPublication(models.Model):
    connection = models.ForeignKey(MetaConnection, on_delete=models.CASCADE)
    caption = models.TextField()
    image_url = models.URLField(max_length=2000, blank=True)
    status = models.CharField(max_length=20, default='sending')
    remote_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    request_id = models.UUIDField(unique=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

class MetaReply(models.Model):
    publication = models.ForeignKey(MetaPublication, on_delete=models.CASCADE)
    comment_id = models.CharField(max_length=100)
    comment_text = models.TextField(blank=True)
    reply = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='pending')
    remote_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('publication', 'comment_id')

class MetaWorkerLease(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    expires_at = models.DateTimeField()
