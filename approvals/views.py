from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import models

from .models import (
    ApprovalWorkflow, ApprovalStage, ApprovalRequest,
    ReviewerAssignment, ApprovalDecision, ApprovalComment,
    ReviewHistory, WorkspaceActivityFeed, NotificationEvent
)
from .serializers import (
    ApprovalWorkflowSerializer, ApprovalStageSerializer, ApprovalRequestSerializer,
    ReviewerAssignmentSerializer, ApprovalDecisionSerializer, ApprovalCommentSerializer,
    ReviewHistorySerializer, WorkspaceActivityFeedSerializer, NotificationEventSerializer
)
from .services import ApprovalWorkflowService

class ApprovalWorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ApprovalWorkflow.objects.filter(
            models.Q(workspace__members__user=user, workspace__members__status='ACTIVE') |
            models.Q(workspace__owner=user)
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save()

class ApprovalRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ApprovalRequest.objects.filter(
            models.Q(user=user) |
            models.Q(reviewer=user) |
            models.Q(workspace__members__user=user, workspace__members__status='ACTIVE') |
            models.Q(workspace__owner=user)
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        req = serializer.save(user=user)
        ApprovalWorkflowService.submit_for_review(
            user=user,
            content_type=req.content_type,
            object_id=req.object_id,
            title=req.title,
            workspace=req.workspace,
            workflow=req.workflow,
            reviewer=req.reviewer,
            comments=req.comments
        )

    @action(detail=True, methods=['post'], url_path='decide')
    def decide(self, request, pk=None):
        approval_request = self.get_object()
        decision = request.data.get('decision') # 'approved', 'rejected', 'changes_requested'
        reason = request.data.get('reason', '')

        if not decision or decision not in ['approved', 'rejected', 'changes_requested']:
            return Response(
                {'error': "Valid 'decision' is required: approved, rejected, or changes_requested."},
                status=status.HTTP_400_BAD_REQUEST
            )

        dec = ApprovalWorkflowService.make_decision(
            approval_request=approval_request,
            reviewer=request.user,
            decision=decision,
            reason=reason
        )
        return Response(ApprovalDecisionSerializer(dec).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='comment')
    def comment(self, request, pk=None):
        approval_request = self.get_object()
        comment_text = request.data.get('comment')
        if not comment_text:
            return Response({'error': "Field 'comment' is required."}, status=status.HTTP_400_BAD_REQUEST)

        cmt = ApprovalWorkflowService.add_comment(
            approval_request=approval_request,
            author=request.user,
            comment_text=comment_text
        )
        return Response(ApprovalCommentSerializer(cmt).data, status=status.HTTP_201_CREATED)

class WorkspaceActivityFeedViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WorkspaceActivityFeedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return WorkspaceActivityFeed.objects.filter(
            models.Q(user=user) |
            models.Q(workspace__members__user=user, workspace__members__status='ACTIVE') |
            models.Q(workspace__owner=user)
        ).distinct().order_by('-created_at')

class NotificationEventViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationEvent.objects.filter(recipient=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        event = self.get_object()
        event.is_read = True
        event.save()
        return Response({'status': 'marked_as_read'}, status=status.HTTP_200_OK)
