from rest_framework import viewsets, permissions
from .models import ContentTemplate
from .serializers import ContentTemplateSerializer

class ContentTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = ContentTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ContentTemplate.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
