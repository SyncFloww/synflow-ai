from django.db import models
from django.contrib.auth.models import User
from campaigns.models import Campaign

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments_made')
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='comments')
    content_id = models.IntegerField(null=True, blank=True) # generic content reference if needed
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} - {self.text[:20]}"
