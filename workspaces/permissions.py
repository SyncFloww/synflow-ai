from rest_framework.permissions import BasePermission

from .models import WorkspaceMember


def member_for(user, workspace):
    if not user.is_authenticated:
        return None
    return WorkspaceMember.objects.filter(workspace=workspace, user=user).first()


def can_manage(member):
    return member and member.role in {WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN, WorkspaceMember.Role.MANAGER}
