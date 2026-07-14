from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Workspace, WorkspaceMember, Invitation, WorkspaceSetting
from .permissions import member_for, can_manage
from .serializers import WorkspaceSerializer, MemberSerializer, InviteSerializer, InvitationSerializer, WorkspaceSettingSerializer


class WorkspaceListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = WorkspaceMember.objects.filter(user=request.user).select_related("workspace")
        workspaces = []
        for membership in memberships:
            membership.workspace.current_membership = membership
            workspaces.append(membership.workspace)
        return Response(WorkspaceSerializer(workspaces, many=True).data)

    def post(self, request):
        serializer = WorkspaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workspace = serializer.save(owner=request.user)
        WorkspaceMember.objects.create(workspace=workspace, user=request.user, role=WorkspaceMember.Role.OWNER)
        WorkspaceSetting.objects.create(workspace=workspace)
        workspace.current_membership = workspace.members.get(user=request.user)
        return Response(WorkspaceSerializer(workspace).data, status=status.HTTP_201_CREATED)


class WorkspaceDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        workspace = get_object_or_404(Workspace, pk=pk)
        membership = member_for(request.user, workspace)
        if not membership:
            return None
        workspace.current_membership = membership
        return workspace

    def get(self, request, pk):
        workspace = self.get_object(request, pk)
        if not workspace:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(WorkspaceSerializer(workspace).data)

    def patch(self, request, pk):
        workspace = self.get_object(request, pk)
        if not workspace or not can_manage(workspace.current_membership):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = WorkspaceSerializer(workspace, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(WorkspaceSerializer(workspace).data)

    def delete(self, request, pk):
        workspace = self.get_object(request, pk)
        if not workspace or workspace.current_membership.role != WorkspaceMember.Role.OWNER:
            return Response(status=status.HTTP_403_FORBIDDEN)
        workspace.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkspaceMembersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        workspace = get_object_or_404(Workspace, pk=pk)
        if not member_for(request.user, workspace):
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(MemberSerializer(workspace.members.select_related("user"), many=True).data)


class WorkspaceInviteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        workspace = get_object_or_404(Workspace, pk=pk)
        if not can_manage(member_for(request.user, workspace)):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = InviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation, _ = Invitation.objects.update_or_create(
            workspace=workspace, email=serializer.validated_data["email"].lower(),
            defaults={"role": serializer.validated_data["role"], "invited_by": request.user, "expires_at": timezone.now() + timedelta(days=7), "accepted_at": None},
        )
        return Response(InvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)


class AcceptInvitationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        invitation = get_object_or_404(Invitation, token=token, accepted_at__isnull=True, expires_at__gt=timezone.now())
        if invitation.email.lower() != request.user.email.lower():
            return Response({"detail": "This invitation belongs to another email address."}, status=status.HTTP_403_FORBIDDEN)
        WorkspaceMember.objects.update_or_create(workspace=invitation.workspace, user=request.user, defaults={"role": invitation.role})
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["accepted_at"])
        return Response({"success": True})
