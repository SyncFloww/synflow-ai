from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    thumbnail_url = models.CharField(max_length=1000, blank=True, default='')
    project_type = models.CharField(max_length=50, default='idea')  # e.g., 'idea', 'script', 'video'
    generations_count = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='draft')  # e.g., 'draft', 'generating', 'completed', 'failed'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
