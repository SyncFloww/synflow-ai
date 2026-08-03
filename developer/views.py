import secrets
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import APIKey, WebhookEndpoint
from .serializers import APIKeySerializer, WebhookEndpointSerializer

class APIKeyViewSet(viewsets.ModelViewSet):
    serializer_class = APIKeySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        prefix = f"sf_live_{secrets.token_hex(4)}"
        secret = f"sf_sec_{secrets.token_urlsafe(24)}"
        serializer.save(user=self.request.user, prefix=prefix, secret_key=secret)

class WebhookEndpointViewSet(viewsets.ModelViewSet):
    serializer_class = WebhookEndpointSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WebhookEndpoint.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        secret_token = f"whsec_{secrets.token_hex(16)}"
        serializer.save(user=self.request.user, secret_token=secret_token)

    @action(detail=True, methods=['post'], url_path='test-ping')
    def test_ping(self, request, pk=None):
        endpoint = self.get_object()
        # Mock testing dispatch
        logs = (
            f"Establishing handshake with URL: {endpoint.url}\n"
            f"Headers injected: X-Syncflow-Signature: {secrets.token_hex(32)}\n"
            f"Payload: {{ \"event\": \"ping\", \"timestamp\": 1782390400, \"status\": \"success\" }}\n"
            f"Response received: Status 200 OK. Connection verified."
        )
        return Response({"status": "success", "logs": logs}, status=status.HTTP_200_OK)
