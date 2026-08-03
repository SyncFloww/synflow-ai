from rest_framework import serializers
from .models import ContentFolder, Content, ContentVersion, ContentTag

class ContentFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentFolder
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class ContentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentVersion
        fields = '__all__'

class ContentSerializer(serializers.ModelSerializer):
    versions_detail = ContentVersionSerializer(source='versions', many=True, read_only=True)

    class Meta:
        model = Content
        fields = ['id', 'workspace', 'brand', 'folder', 'title', 'text_content', 'platform', 'is_favorite', 'is_archived', 'tags', 'versions_detail', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

class ContentTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentTag
        fields = '__all__'
        read_only_fields = ['user']
