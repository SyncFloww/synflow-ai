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
    AGENT_TYPES = [
        ("manager", "Manager Agent"),
        ("content", "Content Agent"),
        ("engagement", "Engagement Agent"),
        ("sales", "Sales Agent"),
        ("analytics", "Analytics Agent"),
    ]

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand.name} - {self.agent_type}"

class AgentTask(models.Model):
    TASK_STATUS = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    task_type = models.CharField(max_length=100)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task_type} for {self.agent.name}"

class AutomationRule(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    trigger_event = models.CharField(max_length=100)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trigger_event} -> {self.agent.name} ({self.action_type})"

class AgentMemory(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    memory_type = models.CharField(max_length=100)
    content = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Memory ({self.memory_type}) for {self.agent.name}"

class ToolExecution(models.Model):
    task = models.ForeignKey(AgentTask, on_delete=models.CASCADE)
    tool_name = models.CharField(max_length=100)
    parameters = models.JSONField(default=dict)
    result = models.JSONField(null=True, blank=True)
    executed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tool_name} execution for task {self.task.id}"
