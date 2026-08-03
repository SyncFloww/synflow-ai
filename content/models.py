from django.db import models
from django.contrib.auth.models import User

class ContentFolder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_folders')
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Content(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contents')
    workspace = models.ForeignKey('workspaces.Workspace', on_delete=models.SET_NULL, null=True, blank=True, related_name='contents')
    brand = models.ForeignKey('social.Brand', on_delete=models.SET_NULL, null=True, blank=True, related_name='contents')
    folder = models.ForeignKey(ContentFolder, on_delete=models.SET_NULL, null=True, blank=True, related_name='contents')
    title = models.CharField(max_length=255)
    text_content = models.TextField()
    platform = models.CharField(max_length=100, blank=True, default='')
    is_favorite = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ContentVersion(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='versions')
    text_content = models.TextField()
    version_number = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.content.title} - v{self.version_number}"

class ContentTag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_tags')
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name
