from django.db import models
from django.contrib.auth.models import User
from workspaces.models import Workspace
from social.models import Brand

class Campaign(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True, blank=True, related_name='campaigns')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='campaigns')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    goal = models.CharField(max_length=255, blank=True, default='')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class CampaignGoal(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=255)
    target_value = models.CharField(max_length=100, blank=True, default='')
    current_value = models.CharField(max_length=100, blank=True, default='')
    metric = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return f"{self.title} for {self.campaign.name}"

class CampaignBudget(models.Model):
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE, related_name='campaign_budget')
    allocated = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    notes = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Budget for {self.campaign.name}"

class CampaignAsset(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='campaign_assets')
    name = models.CharField(max_length=255)
    file_url = models.CharField(max_length=1000)
    asset_type = models.CharField(max_length=50, default='image') # image, video, document
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CampaignMember(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, default='member') # manager, contributor, viewer

    def __str__(self):
        return f"{self.user.username} in {self.campaign.name}"

class CampaignAnalytics(models.Model):
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE, related_name='campaign_analytics')
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for {self.campaign.name}"

class CampaignSchedule(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='schedules')
    name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    cron_expression = models.CharField(max_length=100, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Schedule '{self.name}' for {self.campaign.name}"

class CampaignStep(models.Model):
    STEP_TYPE_CHOICES = (
        ('content_generation', 'Content Generation'),
        ('schedule_post', 'Schedule Post'),
        ('publish_now', 'Publish Now'),
        ('analytics_sync', 'Analytics Sync'),
        ('notification', 'Notification'),
    )
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='steps')
    step_number = models.IntegerField(default=1)
    name = models.CharField(max_length=255)
    step_type = models.CharField(max_length=50, choices=STEP_TYPE_CHOICES, default='content_generation')
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return f"Step {self.step_number}: {self.name} ({self.campaign.name})"

class CampaignExecution(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Execution {self.id} for {self.campaign.name} [{self.status}]"

class CampaignRun(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    execution = models.ForeignKey(CampaignExecution, on_delete=models.CASCADE, related_name='runs')
    step = models.ForeignKey(CampaignStep, on_delete=models.CASCADE, related_name='runs')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    output = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default='')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Run for Step {self.step.step_number} in Exec {self.execution.id} [{self.status}]"

class CampaignLog(models.Model):
    execution = models.ForeignKey(CampaignExecution, on_delete=models.CASCADE, related_name='logs')
    level = models.CharField(max_length=20, default='info')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.id} for Exec {self.execution.id} [{self.level}]"

class CampaignTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='campaign_templates')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True, blank=True, related_name='campaign_templates')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    structure = models.JSONField(default=dict, blank=True) # predefined steps & configs
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
