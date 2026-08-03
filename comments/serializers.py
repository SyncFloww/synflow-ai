from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Comment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CommentSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['user']
