from rest_framework import serializers
from .models import PromptLibrary, PromptCategory, PromptVariable

class PromptCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptCategory
        fields = '__all__'

class PromptVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptVariable
        fields = '__all__'

class PromptLibrarySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    prompt_variables = PromptVariableSerializer(many=True, read_only=True)

    class Meta:
        model = PromptLibrary
        fields = '__all__'
        read_only_fields = ['user']
