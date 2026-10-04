from rest_framework import serializers

class ScriptInputSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=['tiktok', 'instagram', 'reels', 'youtube', 'shorts', 'linkedin', 'facebook', 'x'], default='instagram')
    tone = serializers.CharField(max_length=100, required=False, allow_blank=True)
    audience = serializers.CharField(max_length=255, required=False, allow_blank=True)
    duration = serializers.IntegerField(min_value=15, max_value=240, default=30)
