from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import MarketplaceApp, PromptPack, PluginExtension
from .serializers import MarketplaceAppSerializer, PromptPackSerializer, PluginExtensionSerializer

class MarketplaceAppViewSet(viewsets.ModelViewSet):
    serializer_class = MarketplaceAppSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return all marketplace apps, but scope custom ones if needed
        return MarketplaceApp.objects.all().order_by('category')

    @action(detail=True, methods=['post'], url_path='toggle-install')
    def toggle_install(self, request, pk=None):
        app = self.get_object()
        app.is_installed = not app.is_installed
        app.save()
        return Response(MarketplaceAppSerializer(app).data, status=status.HTTP_200_OK)

class PromptPackViewSet(viewsets.ModelViewSet):
    serializer_class = PromptPackSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = PromptPack.objects.all()

    @action(detail=True, methods=['post'], url_path='install')
    def install(self, request, pk=None):
        pack = self.get_object()
        pack.is_installed = True
        pack.save()
        return Response(PromptPackSerializer(pack).data, status=status.HTTP_200_OK)

class PluginExtensionViewSet(viewsets.ModelViewSet):
    serializer_class = PluginExtensionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = PluginExtension.objects.all()

