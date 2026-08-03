from django.db import models
from django.contrib.auth.models import User
from social.models import Brand
from ai_agents.models import GeneratedContent

class CalendarEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='calendar_events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    color = models.CharField(max_length=50, default='#3B82F6') # hex or tailwind class
    recurrence = models.CharField(max_length=100, blank=True, default='') # daily, weekly, custom
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Schedule(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('published', 'Published'),
        ('failed', 'Failed'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules')
    content = models.ForeignKey(GeneratedContent, on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules')
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Schedule for {self.scheduled_time} - {self.status}"
