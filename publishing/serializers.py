from rest_framework import serializers
from .models import Post, PostPlatform, PublishJob, PublishLog

class PostPlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostPlatform
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    platforms_detail = PostPlatformSerializer(source='platforms', many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'brand', 'workspace', 'content', 'caption', 'media_urls', 'status', 'scheduled_at', 'timezone', 'platforms_detail', 'published_at', 'created_at', 'updated_at']
        read_only_fields = ['user', 'published_at', 'created_at', 'updated_at']

class PublishLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishLog
        fields = '__all__'

class PublishJobSerializer(serializers.ModelSerializer):
    logs = PublishLogSerializer(many=True, read_only=True)

    class Meta:
        model = PublishJob
        fields = '__all__'
