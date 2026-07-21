from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from workspaces.models import Workspace
from content.models import Content, MediaAsset
from social_accounts.models import SocialAccount
from .models import Post, PostPlatform, Schedule
from .serializers import PostSerializer, AtomicPostCreateSerializer
from .services import SchedulingService

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Post.objects.filter(workspace_id=self.kwargs['workspace_id']).order_by('-created_at')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        workspace = get_object_or_404(Workspace, id=self.kwargs['workspace_id'])
        
        serializer = AtomicPostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # 1. Validate ownerships
        content = get_object_or_404(Content, id=data['content_id'], workspace=workspace)
        social_account = get_object_or_404(SocialAccount, id=data['social_account_id'], workspace=workspace)
        media_assets = MediaAsset.objects.filter(id__in=data['media_ids'], workspace=workspace)
        
        # 2. Create Post
        post = Post.objects.create(
            workspace=workspace,
            content=content,
            created_by=request.user,
            status=Post.Status.SCHEDULED
        )
        
        # 3. Attach media
        if media_assets.exists():
            post.media_assets.set(media_assets)
            
        # 4. Create platform association
        post_platform = PostPlatform.objects.create(
            post=post,
            social_account=social_account,
            custom_text=data.get('custom_text', '')
        )
        
        # 5. Create Schedule
        schedule = Schedule.objects.create(
            post=post,
            scheduled_time=data['scheduled_for']
        )
        
        # 6. Trigger scheduling service
        SchedulingService.schedule_post(schedule)
        
        # Create Activity Log via our middleware (it will catch this POST request)
        
        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)
