from django.db import models
from django.contrib.auth.models import User

class AIRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=100) # e.g. "time", "format", "engagement"
    text = models.TextField()
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0) # e.g. percentage confidence
    is_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recommendation_type}: {self.text[:20]}"
