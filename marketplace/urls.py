from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MarketplaceAppViewSet, PromptPackViewSet, PluginExtensionViewSet

router = DefaultRouter()
router.register('apps', MarketplaceAppViewSet, basename='marketplace-app')
router.register('items', MarketplaceAppViewSet, basename='marketplace-item')
router.register('prompt-packs', PromptPackViewSet, basename='prompt-pack')
router.register('plugins', PluginExtensionViewSet, basename='plugin-extension')

urlpatterns = [
    path('', include(router.urls)),
]

