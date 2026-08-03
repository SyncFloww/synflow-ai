from rest_framework import serializers
from .models import ContentTemplate

class ContentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentTemplate
        fields = '__all__'
        read_only_fields = ['user']
