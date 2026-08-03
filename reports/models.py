from django.db import models
from django.contrib.auth.models import User
from campaigns.models import Campaign

class Report(models.Model):
    REPORT_TYPES = (
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('campaign', 'Campaign Report'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    data = models.JSONField(default=dict, blank=True) # generated insights, chart points, summaries
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
