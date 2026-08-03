from django.db import models
from django.contrib.auth.models import User

class Workflow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workflows')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class WorkflowNode(models.Model):
    NODE_TYPES = (
        ('trigger', 'Trigger'),
        ('condition', 'Condition'),
        ('action', 'Action'),
    )
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='nodes')
    node_id = models.CharField(max_length=100) # custom UI id (e.g., node_1)
    label = models.CharField(max_length=255)
    node_type = models.CharField(max_length=20, choices=NODE_TYPES)
    config = models.JSONField(default=dict, blank=True) # node configs like parameters, variables
    position_x = models.FloatField(default=0.0)
    position_y = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.label} ({self.node_type}) in {self.workflow.name}"

class WorkflowTrigger(models.Model):
    workflow = models.OneToOneField(Workflow, on_delete=models.CASCADE, related_name='trigger')
    trigger_type = models.CharField(max_length=100) # e.g., 'new_content', 'scheduled_time', 'post_published', etc.
    config = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.trigger_type} for {self.workflow.name}"

class WorkflowAction(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=100) # e.g., 'generate_ai_content', 'publish', 'notify_team', etc.
    config = models.JSONField(default=dict, blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.action_type} action in {self.workflow.name}"

class WorkflowExecution(models.Model):
    STATUS_CHOICES = (
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    logs = models.TextField(blank=True, default='')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Execution of {self.workflow.name} at {self.started_at} - {self.status}"
