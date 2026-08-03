from rest_framework import serializers
from .models import APIKey, WebhookEndpoint

class APIKeySerializer(serializers.ModelSerializer):
    key_preview = serializers.SerializerMethodField()

    class Meta:
        model = APIKey
        fields = ['id', 'name', 'prefix', 'key_preview', 'is_active', 'created_at']
        read_only_fields = ['user', 'prefix']

    def get_key_preview(self, obj):
        if getattr(obj, 'prefix', None):
            return f"{obj.prefix}****"
        return "****"

class WebhookEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEndpoint
        fields = '__all__'
        read_only_fields = ['user']
