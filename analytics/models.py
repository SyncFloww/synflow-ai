from django.db import models
from django.contrib.auth.models import User
from social.models import Brand, SocialAccount
from publishing.models import Post

class AnalyticsSnapshot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_snapshots')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='analytics_snapshots')
    social_account = models.ForeignKey(SocialAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='analytics_snapshots')
    platform = models.CharField(max_length=50) # youtube, instagram, tiktok, linkedin, etc
    followers_count = models.IntegerField(default=0)
    engagement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0) # e.g. 4.15 (%)
    posts_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform} Snapshot - {self.timestamp}"

class PlatformMetric(models.Model):
    snapshot = models.ForeignKey(AnalyticsSnapshot, on_delete=models.CASCADE, related_name='metrics')
    name = models.CharField(max_length=100) # likes, shares, comments, clicks, impressions
    value = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.name}: {self.value}"

class PostMetric(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='metrics')
    platform = models.CharField(max_length=50)
    reach = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    engagement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PostMetric for Post {self.post.id} on {self.platform}"

class DailyAnalytics(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='daily_analytics')
    platform = models.CharField(max_length=50)
    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    date = models.DateField()

    class Meta:
        unique_together = ('brand', 'platform', 'date')

    def __str__(self):
        return f"{self.platform} Analytics for {self.date}"
