from rest_framework.permissions import BasePermission

from .models import WorkspaceMember


def member_for(user, workspace):
    if not user.is_authenticated:
        return None
    # Support direct ownership or WorkspaceMember link
    if workspace.owner_id == user.id:
        # Create a mock member object for permissions check if they are owner
        return WorkspaceMember(workspace=workspace, user=user, role=WorkspaceMember.Role.OWNER)
    return WorkspaceMember.objects.filter(workspace=workspace, user=user).first()


def can_manage(member):
    return member and member.role in {WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN, WorkspaceMember.Role.MANAGER}


class IsWorkspaceMember(BasePermission):
    """
    Allows access only to authenticated users who are members (or owner) of the workspace.
    Assumes the URL kwargs contains 'workspace_id'.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        workspace_id = view.kwargs.get('workspace_id')
        if not workspace_id:
            return False
            
        from workspaces.models import Workspace
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return False
            
        return member_for(request.user, workspace) is not None
