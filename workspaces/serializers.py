from django.utils.text import slugify
from rest_framework import serializers

from .models import Workspace, WorkspaceMember, Invitation, WorkspaceSetting


class WorkspaceSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = ("id", "name", "slug", "owner", "role", "created_at", "updated_at")
        read_only_fields = ("id", "owner", "role", "created_at", "updated_at")

    def get_role(self, obj):
        membership = getattr(obj, "current_membership", None)
        return membership.role if membership else None

    def validate_slug(self, value):
        return slugify(value)


class MemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ("id", "user", "email", "full_name", "role", "joined_at")
        read_only_fields = ("id", "user", "email", "full_name", "joined_at")


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ("id", "email", "role", "token", "expires_at", "created_at")
        read_only_fields = ("id", "token", "expires_at", "created_at")


class InviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=WorkspaceMember.Role.choices, default=WorkspaceMember.Role.VIEWER)


class WorkspaceSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkspaceSetting
        fields = ("timezone", "week_starts_on")
