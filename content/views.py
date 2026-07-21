from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from workspaces.models import Workspace
from .models import Content, ContentVersion, MediaAsset
from .serializers import ContentSerializer, MediaAssetSerializer
import mimetypes

class MediaAssetViewSet(viewsets.ModelViewSet):
    serializer_class = MediaAssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MediaAsset.objects.filter(workspace_id=self.kwargs['workspace_id'])

    def perform_create(self, serializer):
        workspace = get_object_or_404(Workspace, id=self.kwargs['workspace_id'])
        file_obj = self.request.FILES.get('file')
        
        file_type = 'application/octet-stream'
        size_bytes = 0
        if file_obj:
            size_bytes = file_obj.size
            file_type = file_obj.content_type or mimetypes.guess_type(file_obj.name)[0] or 'application/octet-stream'

        serializer.save(
            workspace=workspace,
            uploaded_by=self.request.user,
            file_type=file_type,
            size_bytes=size_bytes
        )

class ContentViewSet(viewsets.ModelViewSet):
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Content.objects.filter(workspace_id=self.kwargs['workspace_id'])

    def perform_create(self, serializer):
        workspace = get_object_or_404(Workspace, id=self.kwargs['workspace_id'])
        content = serializer.save(workspace=workspace, author=self.request.user)
        # Create initial version
        if content.text_content:
            ContentVersion.objects.create(
                content=content,
                text_content=content.text_content,
                edited_by=self.request.user
            )

    def perform_update(self, serializer):
        # Store original to see if text changed
        instance = self.get_object()
        old_text = instance.text_content
        
        content = serializer.save()
        
        if content.text_content != old_text:
            ContentVersion.objects.create(
                content=content,
                text_content=content.text_content,
                edited_by=self.request.user
            )

    @action(detail=True, methods=['post'])
    def attach_media(self, request, workspace_id=None, pk=None):
        content = self.get_object()
        media_id = request.data.get('media_id')
        if not media_id:
            return Response({"error": "media_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        media = get_object_or_404(MediaAsset, id=media_id, workspace_id=workspace_id)
        content.media_assets.add(media)
        return Response({"message": "Media attached successfully."}, status=status.HTTP_200_OK)
