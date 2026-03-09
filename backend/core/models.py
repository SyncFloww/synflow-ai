from django.db import models
from django.contrib.auth.models import User

class Brand(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='brands')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return self.name

class SocialAccount(models.Model):
    platform_name = models.CharField(max_length=50)
    account_id = models.CharField(max_length=100)
    access_token = models.TextField()
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='social_accounts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['brand']),
            models.Index(fields=['platform_name', 'account_id']),
        ]

    def __str__(self):
        return f"{self.platform_name} - {self.account_id}"

class Agent(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    social_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name='agents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['social_account']),
        ]

    def __str__(self):
        return self.name

class AgentTask(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='tasks')
    task_type = models.CharField(max_length=50)
    parameters = models.JSONField(default=dict)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['agent']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.task_type} for {self.agent.name}"

class AutomationRule(models.Model):
    name = models.CharField(max_length=100)
    trigger_condition = models.JSONField(default=dict)
    action = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    agent_task = models.ForeignKey(AgentTask, on_delete=models.CASCADE, related_name='automation_rules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['agent_task']),
        ]

    def __str__(self):
        return self.name
