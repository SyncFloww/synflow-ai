import uuid
from django.db import models
from workspaces.models import Workspace


class Brand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="brands")
    name = models.CharField(max_length=160)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    target_audience = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    keywords = models.JSONField(default=list, blank=True)
    primary_color = models.CharField(max_length=7, blank=True)
    secondary_color = models.CharField(max_length=7, blank=True)
    logo = models.ImageField(upload_to="logos/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["workspace", "name"], name="unique_workspace_brand_name")]
        ordering = ["name"]


class BrandVoice(models.Model):
    brand = models.OneToOneField(Brand, on_delete=models.CASCADE, related_name="voice")
    tone = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    do_list = models.JSONField(default=list, blank=True)
    dont_list = models.JSONField(default=list, blank=True)


class BrandGuideline(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="guidelines")
    title = models.CharField(max_length=160)
    content = models.TextField()


class BrandAsset(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="assets")
    name = models.CharField(max_length=160)
    file = models.FileField(upload_to="brand-assets/")
    created_at = models.DateTimeField(auto_now_add=True)
