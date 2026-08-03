from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MediaFolder, Media, MediaTag
from .serializers import MediaFolderSerializer, MediaSerializer, MediaTagSerializer

class MediaFolderViewSet(viewsets.ModelViewSet):
    serializer_class = MediaFolderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MediaFolder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MediaViewSet(viewsets.ModelViewSet):
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Media.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='star')
    def star(self, request, pk=None):
        media = self.get_object()
        media.is_starred = not media.is_starred
        media.save()
        return Response({'status': f'media starred state is {media.is_starred}'}, status=status.HTTP_200_OK)

class MediaTagViewSet(viewsets.ModelViewSet):
    serializer_class = MediaTagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MediaTag.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
