from django.db import models
from django.contrib.auth.models import User

class MediaFolder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_folders')
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Media(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_items')
    workspace = models.ForeignKey('workspaces.Workspace', on_delete=models.CASCADE, null=True, blank=True, related_name='media_items')
    brand = models.ForeignKey('social.Brand', on_delete=models.SET_NULL, null=True, blank=True, related_name='media_items')
    folder = models.ForeignKey(MediaFolder, on_delete=models.SET_NULL, null=True, blank=True, related_name='media_items')
    file_name = models.CharField(max_length=255)
    file_url = models.CharField(max_length=1000)
    file_size_bytes = models.IntegerField(default=0)
    mime_type = models.CharField(max_length=100, default='image/png')
    tags = models.JSONField(default=list, blank=True)
    is_starred = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

class MediaTag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_tags')
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

