from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models, transaction
from datetime import timedelta
import uuid

from .models import Workspace, WorkspaceMember, Invitation, WorkspaceSetting
from .serializers import WorkspaceSerializer, WorkspaceMemberSerializer, InvitationSerializer, InvitationCreateSerializer, WorkspaceSettingSerializer
from .permissions import get_user_workspace_role

class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Workspace.objects.filter(
            members__user=self.request.user,
            members__status='ACTIVE',
            is_active=True
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        with transaction.atomic():
            workspace = serializer.save(owner=self.request.user, created_by=self.request.user)
            WorkspaceMember.objects.create(
                workspace=workspace,
                user=self.request.user,
                role='OWNER',
                status='ACTIVE'
            )
            WorkspaceSetting.objects.get_or_create(workspace=workspace)

    def update(self, request, *args, **kwargs):
        workspace = self.get_object()
        role = get_user_workspace_role(request.user, workspace)
        if role not in ['OWNER', 'ADMIN']:
            return Response({'error': 'Only owners and admins can update the workspace.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        workspace = self.get_object()
        role = get_user_workspace_role(request.user, workspace)
        if role != 'OWNER':
            return Response({'error': 'Only the workspace owner can delete the workspace.'}, status=status.HTTP_403_FORBIDDEN)
        # Soft-deactivate or delete
        workspace.is_active = False
        workspace.save()
        return Response({'message': 'Workspace deleted successfully.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'post'], url_path='members')
    def members(self, request, pk=None):
        workspace = self.get_object()
        caller_role = get_user_workspace_role(request.user, workspace)
        if not caller_role:
            return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            members = workspace.members.filter(status='ACTIVE')
            serializer = WorkspaceMemberSerializer(members, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            if caller_role not in ['OWNER', 'ADMIN']:
                return Response({'error': 'You do not have permission to add or modify members.'}, status=status.HTTP_403_FORBIDDEN)

            user_id = request.data.get('user_id')
            role = str(request.data.get('role', 'MEMBER')).upper()
            if role not in ['OWNER', 'ADMIN', 'MANAGER', 'MEMBER']:
                role = 'MEMBER'

            if not user_id:
                return Response({'error': 'user_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

            # ADMIN cannot assign OWNER role
            if caller_role == 'ADMIN' and role == 'OWNER':
                return Response({'error': 'Admins cannot assign OWNER role.'}, status=status.HTTP_403_FORBIDDEN)

            member, created = WorkspaceMember.objects.get_or_create(
                workspace=workspace,
                user_id=user_id,
                defaults={'role': role, 'status': 'ACTIVE'}
            )
            if not created:
                member.role = role
                member.status = 'ACTIVE'
                member.save()

            return Response(WorkspaceMemberSerializer(member).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['patch', 'delete'], url_path=r'members/(?P<member_id>\d+)')
    def manage_member(self, request, pk=None, member_id=None):
        workspace = self.get_object()
        caller_role = get_user_workspace_role(request.user, workspace)
        if caller_role not in ['OWNER', 'ADMIN']:
            return Response({'error': 'Only owners and admins can manage members.'}, status=status.HTTP_403_FORBIDDEN)

        target_member = get_object_or_404(WorkspaceMember, id=member_id, workspace=workspace)

        # ADMIN cannot modify or remove OWNER
        if target_member.role.upper() == 'OWNER' and caller_role != 'OWNER':
            return Response({'error': 'Only owners can modify owner membership.'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'DELETE':
            # Prevent removing the last active OWNER
            if target_member.role.upper() == 'OWNER':
                owner_count = workspace.members.filter(role__in=['OWNER', 'owner'], status='ACTIVE').count()
                if owner_count <= 1:
                    return Response({'error': 'Cannot remove the sole owner of a workspace.'}, status=status.HTTP_400_BAD_REQUEST)

            target_member.status = 'REMOVED'
            target_member.save()
            return Response({'message': 'Member removed successfully.'}, status=status.HTTP_200_OK)

        elif request.method == 'PATCH':
            new_role = str(request.data.get('role', target_member.role)).upper()
            new_status = str(request.data.get('status', target_member.status)).upper()

            if caller_role == 'ADMIN' and new_role == 'OWNER':
                return Response({'error': 'Admins cannot grant OWNER role.'}, status=status.HTTP_403_FORBIDDEN)

            target_member.role = new_role
            target_member.status = new_status
            target_member.save()
            return Response(WorkspaceMemberSerializer(target_member).data)

    @action(detail=True, methods=['post'], url_path='invite')
    def invite(self, request, pk=None):
        workspace = self.get_object()
        caller_role = get_user_workspace_role(request.user, workspace)
        if caller_role not in ['OWNER', 'ADMIN']:
            return Response({'error': 'Only owners and admins can invite members.'}, status=status.HTTP_403_FORBIDDEN)

        email = request.data.get('email') or request.data.get('invited_email')
        role = str(request.data.get('role', 'MEMBER')).upper()
        if role not in ['OWNER', 'ADMIN', 'MANAGER', 'MEMBER']:
            role = 'MEMBER'

        if not email:
            return Response({'error': 'email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if caller_role == 'ADMIN' and role == 'OWNER':
            return Response({'error': 'Admins cannot invite members as OWNER.'}, status=status.HTTP_403_FORBIDDEN)

        token = str(uuid.uuid4())
        invitation = Invitation.objects.create(
            workspace=workspace,
            email=email,
            role=role,
            token=token,
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(days=7)
        )
        return Response(InvitationCreateSerializer(invitation).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'put', 'patch'], url_path='settings')
    def settings_view(self, request, pk=None):
        workspace = self.get_object()
        setting, created = WorkspaceSetting.objects.get_or_create(workspace=workspace)
        caller_role = get_user_workspace_role(request.user, workspace)

        if request.method == 'GET':
            return Response(WorkspaceSettingSerializer(setting).data)

        if caller_role not in ['OWNER', 'ADMIN']:
            return Response({'error': 'Only owners and admins can modify settings.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = WorkspaceSettingSerializer(setting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class InvitationViewSet(viewsets.ModelViewSet):
    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # SECURITY FIX: Only return invitations for workspaces where user is OWNER or ADMIN
        return Invitation.objects.filter(
            workspace__members__user=self.request.user,
            workspace__members__role__in=['OWNER', 'ADMIN', 'owner', 'admin'],
            workspace__members__status='ACTIVE'
        ).distinct().order_by('-created_at')

    def destroy(self, request, *args, **kwargs):
        invitation = self.get_object()
        caller_role = get_user_workspace_role(request.user, invitation.workspace)
        if caller_role not in ['OWNER', 'ADMIN']:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='accept')
    def accept(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        invitation = get_object_or_404(Invitation, token=token, is_accepted=False, expires_at__gt=timezone.now())

        member, created = WorkspaceMember.objects.get_or_create(
            workspace=invitation.workspace,
            user=request.user,
            defaults={'role': invitation.role, 'status': 'ACTIVE'}
        )
        if not created:
            member.role = invitation.role
            member.status = 'ACTIVE'
            member.save()

        invitation.is_accepted = True
        invitation.save()

        return Response({
            'message': f'Successfully joined workspace {invitation.workspace.name}.',
            'workspace_id': invitation.workspace.id,
            'role': member.role
        }, status=status.HTTP_200_OK)
