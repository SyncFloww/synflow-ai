from django.db import models
from django.contrib.auth.models import User
from social.models import Brand

class AIAgent(models.Model):
    id = models.CharField(max_length=50, primary_key=True)  # e.g., 'idea-generator', 'scriptwriter', 'video-editor', 'social-publisher'
    name = models.CharField(max_length=255)
    description = models.TextField()
    task_type = models.CharField(max_length=50)  # e.g., 'idea', 'script', 'video', 'publish'
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class AgentTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_tasks')
    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name='tasks')
    agent_name = models.CharField(max_length=255)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=50, default='pending')  # e.g., 'pending', 'processing', 'completed', 'failed'
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.agent_name} - {self.status}"

class AIModel(models.Model):
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=100) # e.g. gemini, openrouter, deepseek, openai
    model_id = models.CharField(max_length=100) # e.g. gemini-3.5-flash, deepseek-chat
    is_active = models.BooleanField(default=True)
    cost_per_1k_tokens = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)

    def __str__(self):
        return f"{self.provider} - {self.name}"

class PromptTemplate(models.Model):
    name = models.CharField(max_length=255)
    platform = models.CharField(max_length=100) # e.g. instagram, linkedin, x, facebook
    template_text = models.TextField()
    input_fields = models.JSONField(default=list, blank=True) # e.g. ['topic', 'audience', 'tone']
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prompt_templates')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class GeneratedContent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_contents')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_contents')
    prompt_used = models.TextField()
    content_text = models.TextField()
    platform = models.CharField(max_length=100) # e.g. instagram, linkedin, x, facebook
    model_used = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True)
    generation_time_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform} content by {self.user.username} at {self.created_at}"

class ContentGeneration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_generations')
    prompt_template = models.ForeignKey(PromptTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    inputs = models.JSONField(default=dict)
    output = models.ForeignKey(GeneratedContent, on_delete=models.CASCADE, related_name='generation_records')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Generation for {self.user.username} - {self.created_at}"

class GenerationHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generation_histories')
    action = models.CharField(max_length=50, default='created') # e.g., created, updated, edited
    generated_content = models.ForeignKey(GeneratedContent, on_delete=models.CASCADE, related_name='histories')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - {self.generated_content.id} by {self.user.username}"
