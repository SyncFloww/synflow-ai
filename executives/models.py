from django.db import models
from django.contrib.auth.models import User

class ExecutiveMeeting(models.Model):
    MEETING_TYPES = (
        ('weekly', 'Weekly Operations Sync'),
        ('monthly', 'Monthly Strategic Alignment'),
        ('emergency', 'Ad-hoc Emergency Review'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='executive_meetings')
    title = models.CharField(max_length=255)
    meeting_type = models.CharField(max_length=50, choices=MEETING_TYPES, default='weekly')
    transcript = models.TextField()  # Dialogue between CEO, CFO, CMO, etc.
    summary = models.TextField()
    recommendations = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.created_at.date()})"
