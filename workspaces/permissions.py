from rest_framework import permissions
from .models import Workspace, WorkspaceMember

def get_user_workspace_role(user, workspace):
    if not user or not user.is_authenticated or not workspace:
        return None
    try:
        member = WorkspaceMember.objects.get(
            workspace=workspace,
            user=user,
            status='ACTIVE'
        )
        return member.role.upper()
    except WorkspaceMember.DoesNotExist:
        return None

class IsWorkspaceMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        workspace = obj if isinstance(obj, Workspace) else getattr(obj, 'workspace', None)
        if not workspace:
            return False
        role = get_user_workspace_role(request.user, workspace)
        return role is not None

class IsWorkspaceAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        workspace = obj if isinstance(obj, Workspace) else getattr(obj, 'workspace', None)
        if not workspace:
            return False
        role = get_user_workspace_role(request.user, workspace)
        return role in ['OWNER', 'ADMIN']

class IsWorkspaceOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        workspace = obj if isinstance(obj, Workspace) else getattr(obj, 'workspace', None)
        if not workspace:
            return False
        role = get_user_workspace_role(request.user, workspace)
        return role == 'OWNER'
