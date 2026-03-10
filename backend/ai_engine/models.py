from django.db import models
from core.models import Brand

class Agent(models.Model):
    """
    Configuration for an AI agent.
    Ties a specific brand voice and set of tools to an active processing entity.
    """
    name = models.CharField(max_length=255)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='agents')
    system_prompt = models.TextField(help_text="The core identity and instructions for this agent.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.brand.name})"

class AutomationRule(models.Model):
    """
    Defines when an Agent should be triggered.
    """
    name = models.CharField(max_length=255)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='rules')
    trigger_type = models.CharField(max_length=50, choices=[
        ('mention', 'Social Media Mention'),
        ('schedule', 'Scheduled Time'),
        ('keyword', 'Keyword Match'),
    ])
    trigger_config = models.JSONField(default=dict, help_text="Specifics for the trigger (e.g., keywords, cron schedule).")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rule: {self.name} -> {self.agent.name}"

class AgentTask(models.Model):
    """
    A specific execution instance of an Agent, usually created by an AutomationRule.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='tasks')
    rule_triggered = models.ForeignKey(AutomationRule, null=True, blank=True, on_delete=models.SET_NULL)
    input_data = models.JSONField(help_text="The context/input that triggered the task (e.g., tweet text).")
    output_data = models.JSONField(null=True, blank=True, help_text="The final response or error from the LLM.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Task {self.id} for {self.agent.name} ({self.status})"
