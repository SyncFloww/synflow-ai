from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import models

from .models import Post, PostPlatform, PublishJob, PublishLog
from .serializers import PostSerializer, PostPlatformSerializer, PublishJobSerializer, PublishLogSerializer
from .services import PublishingService
from workspaces.permissions import get_user_workspace_role

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Post.objects.filter(
            models.Q(user=user) |
            models.Q(workspace__members__user=user, workspace__members__status='ACTIVE') |
            models.Q(brand__workspace__members__user=user, brand__workspace__members__status='ACTIVE')
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        brand = serializer.validated_data.get('brand')
        workspace = serializer.validated_data.get('workspace')
        if not workspace and brand:
            workspace = brand.workspace
        serializer.save(user=self.request.user, workspace=workspace)

    @action(detail=True, methods=['post'], url_path='publish-now')
    def publish_now(self, request, pk=None):
        post = self.get_object()
        platforms_list = request.data.get('platforms')
        result = PublishingService.publish_now(post, platforms_list)
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='submit-review')
    def submit_review(self, request, pk=None):
        post = self.get_object()
        post = PublishingService.submit_for_review(post)
        return Response(PostSerializer(post).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        post = self.get_object()
        if post.workspace:
            role = get_user_workspace_role(request.user, post.workspace)
            if role not in ['OWNER', 'ADMIN', 'MANAGER']:
                return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        post = PublishingService.approve_post(post)
        return Response(PostSerializer(post).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='schedule')
    def schedule(self, request, pk=None):
        post = self.get_object()
        scheduled_at = request.data.get('scheduled_at') or request.data.get('scheduled_time')
        tz_str = request.data.get('timezone', 'UTC')
        if not scheduled_at:
            return Response({'error': 'scheduled_at is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        post = PublishingService.schedule_post(post, scheduled_at, tz_str)
        return Response(PostSerializer(post).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        post = self.get_object()
        post = PublishingService.cancel_post(post)
        return Response(PostSerializer(post).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reschedule')
    def reschedule(self, request, pk=None):
        post = self.get_object()
        new_time = request.data.get('scheduled_at') or request.data.get('scheduled_time')
        tz_str = request.data.get('timezone', 'UTC')
        if not new_time:
            return Response({'error': 'scheduled_at is required.'}, status=status.HTTP_400_BAD_REQUEST)

        post = PublishingService.reschedule_post(post, new_time, tz_str)
        return Response(PostSerializer(post).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='logs')
    def logs(self, request, pk=None):
        post = self.get_object()
        logs = PublishLog.objects.filter(job__post=post).order_by('-created_at')
        return Response(PublishLogSerializer(logs, many=True).data, status=status.HTTP_200_OK)

class PostPlatformViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PostPlatformSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return PostPlatform.objects.filter(
            models.Q(post__user=user) |
            models.Q(post__workspace__members__user=user, post__workspace__members__status='ACTIVE')
        ).distinct()

class PublishJobViewSet(viewsets.ModelViewSet):
    serializer_class = PublishJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return PublishJob.objects.filter(
            models.Q(post__user=user) |
            models.Q(post__workspace__members__user=user, post__workspace__members__status='ACTIVE')
        ).distinct().order_by('-scheduled_time')

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_job(self, request, pk=None):
        job = self.get_object()
        job.status = 'cancelled'
        job.save()
        job.post.status = 'draft'
        job.post.save()
        return Response(PublishJobSerializer(job).data, status=status.HTTP_200_OK)
