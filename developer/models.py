from django.db import models
from django.contrib.auth.models import User

class APIKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=150, default='Production Key')
    prefix = models.CharField(max_length=16, unique=True)
    secret_key = models.CharField(max_length=128)  # stored in plain/partially masked format for mockup, or hashed
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.prefix}...)"

class WebhookEndpoint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webhooks')
    url = models.URLField()
    description = models.CharField(max_length=255, blank=True)
    secret_token = models.CharField(max_length=100)
    event_types = models.CharField(max_length=255, default='campaign.created,task.completed')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url
