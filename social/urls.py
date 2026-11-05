from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BrandViewSet, BrandProfileViewSet, BrandKnowledgeViewSet,
    BrandAssetViewSet, BrandVoiceViewSet, BrandGuidelineViewSet,
    SocialAccountViewSet, PlatformCredentialViewSet,
    OAuthProvidersView, OAuthAuthorizeView, OAuthCallbackView,
    ConnectSocialAccountView, VerifySocialAccountView, DisconnectSocialAccountView
)

from .meta_automation import MetaAutomation, MetaCancelPost, MetaCron
from .meta_api import MetaAccounts, MetaCallback, MetaAccount, MetaPosts, MetaComments

from .tiktok_api import TikTokAccounts, TikTokCallback, TikTokCreator, TikTokDisconnect, TikTokPosts, TikTokStatus, TikTokWorker
from .inbox_api import FacebookInbox
from .readiness import SocialReadiness

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
    path('readiness/', SocialReadiness.as_view()),
    path('meta/accounts/<int:account_id>/inbox/', FacebookInbox.as_view()),
    path('tiktok/brands/<int:brand_id>/accounts/', TikTokAccounts.as_view()),
    path('tiktok/callback/', TikTokCallback.as_view()),
    path('tiktok/accounts/<int:account_id>/worker/', TikTokWorker.as_view()),
    path('tiktok/accounts/<int:account_id>/creator/', TikTokCreator.as_view()),
    path('tiktok/accounts/<int:account_id>/', TikTokDisconnect.as_view()),
    path('tiktok/accounts/<int:account_id>/posts/', TikTokPosts.as_view()),
    path('tiktok/posts/<int:post_id>/status/', TikTokStatus.as_view()),
    path('meta/cron/', MetaCron.as_view()),
    path('meta/accounts/<int:account_id>/automation/', MetaAutomation.as_view()),
    path('meta/posts/<int:post_id>/cancel/', MetaCancelPost.as_view()),
    path('meta/brands/<int:brand_id>/accounts/', MetaAccounts.as_view()),
    path('meta/callback/', MetaCallback.as_view()),
    path('meta/accounts/<int:account_id>/', MetaAccount.as_view()),
    path('meta/accounts/<int:account_id>/posts/', MetaPosts.as_view()),
    path('meta/posts/<int:post_id>/comments/', MetaComments.as_view()),
    path('oauth/providers/', OAuthProvidersView.as_view(), name='oauth_providers'),
    path('oauth/authorize/', OAuthAuthorizeView.as_view(), name='oauth_authorize'),
    path('oauth/<str:provider>/authorize/', OAuthAuthorizeView.as_view(), name='oauth_provider_authorize'),
    path('oauth/callback/', OAuthCallbackView.as_view(), name='oauth_callback'),
    path('oauth/<str:provider>/callback/', OAuthCallbackView.as_view(), name='oauth_provider_callback'),
    path('accounts/<int:pk>/verify/', VerifySocialAccountView.as_view(), name='verify_social_account'),
    path('accounts/<int:pk>/disconnect/', DisconnectSocialAccountView.as_view(), name='disconnect_social_account'),
    path('connect/<str:platform>/', ConnectSocialAccountView.as_view(), name='connect_social'),
    path('<int:pk>/disconnect/', DisconnectSocialAccountView.as_view(), name='disconnect_social_deprecated'),
    path('', include(router.urls)),
]
