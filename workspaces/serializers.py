from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Workspace, WorkspaceMember, Invitation, WorkspaceSetting

class WorkspaceSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkspaceSetting
        fields = '__all__'

class WorkspaceMemberSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = WorkspaceMember
        fields = ['id', 'workspace', 'user', 'username', 'email', 'role', 'status', 'joined_at', 'updated_at']
        read_only_fields = ['id', 'joined_at', 'updated_at']

class WorkspaceSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    created_by_username = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Workspace
        fields = ['id', 'owner', 'owner_username', 'created_by', 'created_by_username', 'name', 'slug', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_by', 'created_at', 'updated_at']

class InvitationSerializer(serializers.ModelSerializer):
    invited_by_username = serializers.ReadOnlyField(source='invited_by.username')
    workspace_name = serializers.ReadOnlyField(source='workspace.name')
    invited_email = serializers.ReadOnlyField(source='email')

    class Meta:
        model = Invitation
        fields = ['id', 'workspace', 'workspace_name', 'email', 'invited_email', 'role', 'is_accepted', 'invited_by', 'invited_by_username', 'created_at', 'expires_at']
        read_only_fields = ['id', 'is_accepted', 'invited_by', 'created_at']

class InvitationCreateSerializer(serializers.ModelSerializer):
    invited_by_username = serializers.ReadOnlyField(source='invited_by.username')
    workspace_name = serializers.ReadOnlyField(source='workspace.name')
    invited_email = serializers.ReadOnlyField(source='email')

    class Meta:
        model = Invitation
        fields = ['id', 'workspace', 'workspace_name', 'email', 'invited_email', 'role', 'token', 'is_accepted', 'invited_by', 'invited_by_username', 'created_at', 'expires_at']
        read_only_fields = ['id', 'token', 'is_accepted', 'invited_by', 'created_at']
