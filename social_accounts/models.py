import uuid
from django.db import models
from django.conf import settings
from workspaces.models import Workspace

class Platform(models.TextChoices):
    FACEBOOK = "facebook", "Facebook"
    INSTAGRAM = "instagram", "Instagram"
    LINKEDIN = "linkedin", "LinkedIn"
    X = "x", "X"
    MOCK = "mock", "Mock Platform"

class ConnectionStatus(models.TextChoices):
    CONNECTED = "connected", "Connected"
    EXPIRED = "expired", "Token Expired"
    DISCONNECTED = "disconnected", "Disconnected"

class SocialAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="social_accounts")
    platform = models.CharField(max_length=50, choices=Platform.choices)
    
    # External Platform Identifiers
    platform_account_id = models.CharField(max_length=255)
    username = models.CharField(max_length=255, blank=True)
    profile_url = models.URLField(blank=True)
    
    status = models.CharField(max_length=20, choices=ConnectionStatus.choices, default=ConnectionStatus.CONNECTED)
    connected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="connected_social_accounts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['workspace', 'platform', 'platform_account_id'], name='unique_workspace_platform_account')
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.platform} - {self.username or self.platform_account_id}"

class OAuthToken(models.Model):
    social_account = models.OneToOneField(SocialAccount, on_delete=models.CASCADE, related_name="token")
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    scopes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        from django.utils import timezone
        if not self.expires_at:
            return False
        return timezone.now() >= self.expires_at
