import uuid
from django.db import models
from django.contrib.auth.models import User
from social.models import Brand
from workspaces.models import Workspace

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

# --- AI MEDIA STUDIO EXTENDED MODELS ---

class AIJob(models.Model):
    STATUS_CHOICES = (
        ('QUEUED', 'Queued'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    )

    JOB_TYPE_CHOICES = (
        ('idea', 'Idea Generation'),
        ('script', 'Script Generation'),
        ('social_content', 'Social Content Conversion'),
        ('image', 'Image Generation'),
        ('video', 'Video Generation'),
        ('voiceover', 'Voiceover Generation'),
        ('audio_mix', 'Audio Mixing'),
        ('caption', 'Caption Generation'),
        ('composition', 'Video Composition Render'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='ai_jobs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_jobs')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_jobs')
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    provider = models.CharField(max_length=50, default='default')
    model = models.CharField(max_length=100, blank=True, default='')
    input_data = models.JSONField(default=dict, blank=True)
    output_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='QUEUED')
    progress = models.IntegerField(default=0)  # 0 to 100
    error = models.TextField(blank=True, default='')
    idempotency_key = models.CharField(max_length=255, blank=True, default='')
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.job_type} ({self.status}) - {self.id}"


class AIContentProject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='ai_projects')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_projects')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_projects')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    target_platform = models.CharField(max_length=100, blank=True, default='instagram')
    preset_format = models.CharField(max_length=100, blank=True, default='reels')
    
    idea_data = models.JSONField(default=dict, blank=True)
    current_script_id = models.IntegerField(null=True, blank=True)
    social_content_ids = models.JSONField(default=list, blank=True)
    media_asset_ids = models.JSONField(default=list, blank=True)
    audio_project_id = models.IntegerField(null=True, blank=True)
    caption_data = models.JSONField(default=dict, blank=True)
    export_url = models.CharField(max_length=1000, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class AIScript(models.Model):
    project = models.ForeignKey(AIContentProject, on_delete=models.CASCADE, related_name='scripts', null=True, blank=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='ai_scripts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_scripts')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_scripts')
    
    title = models.CharField(max_length=255)
    topic = models.CharField(max_length=255, blank=True, default='')
    platform = models.CharField(max_length=50, default='tiktok')
    target_audience = models.CharField(max_length=255, blank=True, default='')
    tone = models.CharField(max_length=100, blank=True, default='')
    duration_seconds = models.IntegerField(default=30)
    
    hook = models.TextField(blank=True, default='')
    body = models.TextField(blank=True, default='')
    transitions = models.TextField(blank=True, default='')
    cta = models.TextField(blank=True, default='')
    visual_directions = models.TextField(blank=True, default='')
    b_roll_suggestions = models.JSONField(default=list, blank=True)
    voiceover_text = models.TextField(blank=True, default='')
    onscreen_text = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.platform})"


class AIScriptVersion(models.Model):
    script = models.ForeignKey(AIScript, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField(default=1)
    hook = models.TextField(blank=True, default='')
    body = models.TextField(blank=True, default='')
    cta = models.TextField(blank=True, default='')
    voiceover_text = models.TextField(blank=True, default='')
    visual_directions = models.TextField(blank=True, default='')
    change_summary = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']

    def __str__(self):
        return f"{self.script.title} v{self.version_number}"


class AISocialContent(models.Model):
    script = models.ForeignKey(AIScript, on_delete=models.SET_NULL, null=True, blank=True, related_name='social_outputs')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='ai_social_contents')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_social_contents')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_social_contents')
    
    platform = models.CharField(max_length=50) # instagram, linkedin, x, facebook, tiktok, youtube
    content_type = models.CharField(max_length=50, default='post') # caption, post, thread, description
    caption = models.TextField()
    hashtags = models.JSONField(default=list, blank=True)
    call_to_action = models.CharField(max_length=255, blank=True, default='')
    saved_content_id = models.IntegerField(null=True, blank=True) # ID in content.Content model
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform} content derived from {self.script.title if self.script else 'AI'}"


class CustomVoiceProfile(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='custom_voices')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_voices')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    provider_voice_id = models.CharField(max_length=255)
    provider_name = models.CharField(max_length=50, default='murf')
    sample_url = models.CharField(max_length=1000, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.provider_name})"


class VoiceConsent(models.Model):
    voice_profile = models.ForeignKey(CustomVoiceProfile, on_delete=models.CASCADE, related_name='consents', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voice_consents')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='voice_consents')
    consent_statement = models.TextField()
    signature_name = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    granted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consent by {self.signature_name} at {self.granted_at}"


class AudioProject(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='audio_projects')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audio_projects')
    title = models.CharField(max_length=255)
    duration_seconds = models.FloatField(default=30.0)
    tracks = models.JSONField(default=list, blank=True) # list of track objects
    output_url = models.CharField(max_length=1000, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class AICaption(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='ai_captions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_captions')
    audio_url = models.CharField(max_length=1000, blank=True, default='')
    transcript = models.TextField(blank=True, default='')
    srt_content = models.TextField(blank=True, default='')
    vtt_content = models.TextField(blank=True, default='')
    word_timings = models.JSONField(default=list, blank=True)
    style_config = models.JSONField(default=dict, blank=True) # position, font, color, animations
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Caption for {self.user.username} ({self.created_at})"


class AIUsageRecord(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='ai_usage_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_usage_records')
    provider = models.CharField(max_length=50)
    model = models.CharField(max_length=100)
    generation_type = models.CharField(max_length=50) # llm, image, video, voice, audio
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    seconds_used = models.FloatField(default=0.0)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.workspace.name} - {self.generation_type} - ${self.estimated_cost}"
