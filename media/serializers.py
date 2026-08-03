from rest_framework import serializers
from .models import MediaFolder, Media, MediaTag

class MediaFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFolder
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class MediaTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaTag
        fields = '__all__'
        read_only_fields = ['user']
