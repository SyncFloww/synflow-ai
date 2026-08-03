from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BrandViewSet, BrandProfileViewSet, BrandKnowledgeViewSet,
    BrandAssetViewSet, BrandVoiceViewSet, BrandGuidelineViewSet,
    SocialAccountViewSet, PlatformCredentialViewSet,
    OAuthProvidersView, OAuthAuthorizeView, OAuthCallbackView,
    ConnectSocialAccountView, DisconnectSocialAccountView
)

router = DefaultRouter()
router.register('brands', BrandViewSet, basename='brand')
router.register('brand-profiles', BrandProfileViewSet, basename='brandprofile')
router.register('knowledge', BrandKnowledgeViewSet, basename='brandknowledge')
router.register('assets', BrandAssetViewSet, basename='brandasset')
router.register('voices', BrandVoiceViewSet, basename='brandvoice')
router.register('guidelines', BrandGuidelineViewSet, basename='brandguideline')
router.register('accounts', SocialAccountViewSet, basename='socialaccount')
router.register('credentials', PlatformCredentialViewSet, basename='platformcredential')

urlpatterns = [
    path('oauth/providers/', OAuthProvidersView.as_view(), name='oauth_providers'),
    path('oauth/authorize/', OAuthAuthorizeView.as_view(), name='oauth_authorize'),
    path('oauth/callback/', OAuthCallbackView.as_view(), name='oauth_callback'),
    path('connect/<str:platform>/', ConnectSocialAccountView.as_view(), name='connect_social'),
    path('<int:pk>/disconnect/', DisconnectSocialAccountView.as_view(), name='disconnect_social'),
    path('', include(router.urls)),
]
