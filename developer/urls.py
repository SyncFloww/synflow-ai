from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import APIKeyViewSet, WebhookEndpointViewSet

router = DefaultRouter()
router.register('keys', APIKeyViewSet, basename='api-key')
router.register('webhooks', WebhookEndpointViewSet, basename='webhook')

urlpatterns = [
    path('', include(router.urls)),
]
