from django.db import models
from django.contrib.auth.models import User

class ContentTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_templates')
    title = models.CharField(max_length=255)
    platform = models.CharField(max_length=100) # e.g. instagram, linkedin, tiktok, newsletter
    layout_type = models.CharField(max_length=100, default='image') # e.g. carousel, story, single_post, video
    structure = models.JSONField(default=dict, blank=True) # layout structure or placeholder configs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
