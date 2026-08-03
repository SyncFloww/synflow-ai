from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ContentFolder, Content, ContentVersion, ContentTag
from .serializers import ContentFolderSerializer, ContentSerializer, ContentVersionSerializer, ContentTagSerializer

class ContentFolderViewSet(viewsets.ModelViewSet):
    serializer_class = ContentFolderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ContentFolder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ContentViewSet(viewsets.ModelViewSet):
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Content.objects.filter(
            models.Q(user=user) |
            models.Q(workspace__members__user=user, workspace__members__status='ACTIVE') |
            models.Q(brand__workspace__members__user=user, brand__workspace__members__status='ACTIVE')
        ).filter(is_archived=False).distinct().order_by('-updated_at')

    def perform_create(self, serializer):
        content = serializer.save(user=self.request.user)
        # Save initial version
        ContentVersion.objects.create(
            content=content,
            text_content=content.text_content,
            version_number=1
        )

    def perform_update(self, serializer):
        content = serializer.save()
        # Find next version number
        last_version = content.versions.order_by('-version_number').first()
        next_ver = (last_version.version_number + 1) if last_version else 1
        
        # Save new version
        ContentVersion.objects.create(
            content=content,
            text_content=content.text_content,
            version_number=next_ver
        )

    @action(detail=True, methods=['post'], url_path='archive')
    def archive(self, request, pk=None):
        content = self.get_object()
        content.is_archived = True
        content.save()
        return Response({'status': 'content archived'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='favorite')
    def favorite(self, request, pk=None):
        content = self.get_object()
        content.is_favorite = not content.is_favorite
        content.save()
        return Response({'status': f'content favorite set to {content.is_favorite}'}, status=status.HTTP_200_OK)

class ContentVersionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ContentVersionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ContentVersion.objects.filter(content__user=self.request.user)

class ContentTagViewSet(viewsets.ModelViewSet):
    serializer_class = ContentTagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ContentTag.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
