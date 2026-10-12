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
