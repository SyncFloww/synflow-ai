from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, ActivityLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_detail = UserSerializer(source='assigned_to', read_only=True)
    assigned_by_detail = UserSerializer(source='assigned_by', read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['assigned_by']

class ActivityLogSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = ActivityLog
        fields = '__all__'
