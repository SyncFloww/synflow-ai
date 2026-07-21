from rest_framework import serializers
from .models import Post, PostPlatform, Schedule, PublishJob, PublishResult

class PostPlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostPlatform
        fields = ['id', 'social_account', 'custom_text']

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'scheduled_time', 'timezone', 'is_active', 'created_at']

class PostSerializer(serializers.ModelSerializer):
    platforms = PostPlatformSerializer(many=True, read_only=True)
    schedule = ScheduleSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'workspace', 'content', 'created_by', 'post_text', 
            'media_assets', 'status', 'platforms', 'schedule', 'created_at'
        ]
        read_only_fields = ['workspace', 'created_by', 'status']

class AtomicPostCreateSerializer(serializers.Serializer):
    content_id = serializers.UUIDField()
    social_account_id = serializers.UUIDField()
    scheduled_for = serializers.DateTimeField()
    media_ids = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)
    custom_text = serializers.CharField(required=False, allow_blank=True)
