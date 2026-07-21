import uuid
from django.db import models
from django.conf import settings
from workspaces.models import Workspace

class AIModel(models.Model):
    """
    Represents an AI Model configuration (e.g., gpt-4, claude-3-opus).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100) # e.g. "GPT-4o"
    provider_string = models.CharField(max_length=100) # e.g. "openai/gpt-4o" or "openrouter/anthropic/claude-3-opus"
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class PromptTemplate(models.Model):
    """
    Pre-defined or user-defined prompt structures.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="prompt_templates", null=True, blank=True)
    name = models.CharField(max_length=150)
    system_prompt = models.TextField(blank=True)
    user_prompt_template = models.TextField(help_text="Use {topic}, {tone}, {platform} for substitution")
    is_system_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ContentGeneration(models.Model):
    """
    Tracks a specific generation request.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="generations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    template_used = models.ForeignKey(PromptTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Input
    platform = models.CharField(max_length=50, blank=True)
    topic = models.TextField(blank=True)
    tone = models.CharField(max_length=100, blank=True)
    extra_instructions = models.TextField(blank=True)
    
    # Output
    generated_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Generation for {self.platform} - {self.id}"

class GenerationHistory(models.Model):
    """
    Detailed log of generation parameters for observability.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    generation = models.OneToOneField(ContentGeneration, on_delete=models.CASCADE, related_name="history")
    full_prompt = models.TextField()
    provider_response = models.JSONField(default=dict)
    tokens_used = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"History of {self.generation.id}"
