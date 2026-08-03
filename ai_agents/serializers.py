from rest_framework import serializers
from .models import AIAgent, AgentTask, AIModel, PromptTemplate, GeneratedContent, ContentGeneration, GenerationHistory

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
