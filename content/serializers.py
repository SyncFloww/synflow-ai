from rest_framework import serializers
from .models import Content, ContentVersion, MediaAsset, ContentFolder, ContentTag

class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = ['id', 'workspace', 'uploaded_by', 'file', 'file_type', 'size_bytes', 'created_at']
        read_only_fields = ['workspace', 'uploaded_by', 'file_type', 'size_bytes']

class ContentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentVersion
        fields = ['id', 'text_content', 'edited_by', 'created_at']
        read_only_fields = fields

class ContentSerializer(serializers.ModelSerializer):
    versions = ContentVersionSerializer(many=True, read_only=True)
    media_assets = MediaAssetSerializer(many=True, read_only=True)

    class Meta:
        model = Content
        fields = [
            'id', 'workspace', 'author', 'folder', 'tags', 'media_assets',
            'title', 'text_content', 'status', 'created_at', 'updated_at', 'versions'
        ]
        read_only_fields = ['workspace', 'author']
