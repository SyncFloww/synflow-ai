from rest_framework import serializers
from .models import (
    AIAgent,
    AgentTask,
    AIModel,
    PromptTemplate,
    GeneratedContent,
    ContentGeneration,
    GenerationHistory,
    AIJob,
    AIContentProject,
    AIScript,
    AIScriptVersion,
    AISocialContent,
    CustomVoiceProfile,
    VoiceConsent,
    AudioProject,
    AICaption,
    AIUsageRecord
)

class AIAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAgent
        fields = ['id', 'name', 'description', 'task_type', 'is_active']

class AgentTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentTask
        fields = ['id', 'agent', 'agent_name', 'input_data', 'output_data', 'status', 'completed_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'agent_name', 'output_data', 'status', 'completed_at', 'created_at', 'updated_at']

class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = '__all__'

class PromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTemplate
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']

class GeneratedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedContent
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class ContentGenerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentGeneration
        fields = '__all__'

class GenerationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GenerationHistory
        fields = '__all__'

class AIJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIJob
        fields = '__all__'
        read_only_fields = ['id', 'user', 'workspace', 'created_at', 'started_at', 'completed_at']

class AIScriptVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIScriptVersion
        fields = '__all__'

class AIScriptSerializer(serializers.ModelSerializer):
    versions = AIScriptVersionSerializer(many=True, read_only=True)

    class Meta:
        model = AIScript
        fields = '__all__'
        read_only_fields = ['user', 'workspace', 'created_at', 'updated_at']

class AISocialContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AISocialContent
        fields = '__all__'
        read_only_fields = ['user', 'workspace', 'created_at']

class AIContentProjectSerializer(serializers.ModelSerializer):
    scripts = AIScriptSerializer(many=True, read_only=True)

    class Meta:
        model = AIContentProject
        fields = '__all__'
        read_only_fields = ['id', 'user', 'workspace', 'created_at', 'updated_at']

class CustomVoiceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomVoiceProfile
        fields = '__all__'
        read_only_fields = ['user', 'workspace', 'created_at']

class VoiceConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceConsent
        fields = '__all__'
        read_only_fields = ['user', 'workspace', 'granted_at']

class AudioProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioProject
        fields = '__all__'
        read_only_fields = ['user', 'workspace', 'created_at', 'updated_at']

class AICaptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AICaption
        fields = '__all__'
        read_only_fields = ['user', 'workspace', 'created_at']

class AIUsageRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIUsageRecord
        fields = '__all__'
