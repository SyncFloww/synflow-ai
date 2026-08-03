from django.db import models
from django.contrib.auth.models import User

class PromptCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class PromptLibrary(models.Model):
    title = models.CharField(max_length=255)
    prompt_text = models.TextField()
    category = models.ForeignKey(PromptCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='prompts')
    variables = models.JSONField(default=list, blank=True) # list of strings of variables, e.g. ["topic", "tone"]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library_prompts')
    version = models.IntegerField(default=1)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class PromptVariable(models.Model):
    prompt = models.ForeignKey(PromptLibrary, on_delete=models.CASCADE, related_name='prompt_variables')
    name = models.CharField(max_length=100)
    default_value = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"{self.name} in {self.prompt.title}"
