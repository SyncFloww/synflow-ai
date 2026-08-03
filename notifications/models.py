from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    STATUS_CHOICES = (
        ('info', 'Info'),
        ('system', 'System'),
        ('success', 'Success'),
        ('warning', 'Warning'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=STATUS_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} for {self.user.username} - Read: {self.is_read}"

class NotificationSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    weekly_digest = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification settings for {self.user.username}"
