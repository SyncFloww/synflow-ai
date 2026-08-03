from django.db import models
from django.contrib.auth.models import User

class MarketplaceApp(models.Model):
    APP_CATEGORIES = (
        ('agent', 'AI Agent Assistant'),
        ('connector', 'Database Connector'),
        ('utility', 'Automation Tool'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='installed_apps', null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=APP_CATEGORIES, default='agent')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_installed = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    icon = models.CharField(max_length=100, default='🧩')

    def __str__(self):
        return self.name

# Alias for MarketplaceItem
MarketplaceItem = MarketplaceApp

class PromptPack(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100, default='Social Media')
    prompts_count = models.IntegerField(default=10)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_installed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class PluginExtension(models.Model):
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50, default='1.0.0')
    publisher = models.CharField(max_length=255, default='SyncflowAI')
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} v{self.version}"

