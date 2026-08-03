from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models, transaction
from datetime import timedelta
import uuid

from workspaces.models import Workspace, WorkspaceMember
from workspaces.permissions import get_user_workspace_role
from users.models import PersonalSpace
from .models import Brand, BrandProfile, BrandKnowledge, BrandAsset, BrandVoice, BrandGuideline, SocialAccount, PlatformCredential, OAuthToken
from .serializers import (
    BrandSerializer, BrandProfileSerializer, BrandKnowledgeSerializer,
    BrandAssetSerializer, BrandVoiceSerializer, BrandGuidelineSerializer,
    SocialAccountSerializer, PlatformCredentialSerializer, OAuthTokenSerializer
)
from .providers import get_provider, list_providers
from .services import OAuthTokenService

class BrandViewSet(viewsets.ModelViewSet):
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Brand.objects.filter(
            workspace__members__user=self.request.user,
            workspace__members__status='ACTIVE',
            is_active=True
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        workspace_id = self.request.data.get('workspace') or self.request.data.get('workspace_id')
        if not workspace_id:
            user_ws = Workspace.objects.filter(members__user=self.request.user, members__status='ACTIVE').first()
            if not user_ws:
                raise ValidationError({'workspace': 'Active workspace is required to create a brand.'})
            workspace = user_ws
        else:
            workspace = get_object_or_404(Workspace, id=workspace_id)
            role = get_user_workspace_role(self.request.user, workspace)
            if not role:
                raise PermissionDenied('You are not a member of this workspace.')

        brand = serializer.save(
            workspace=workspace,
            created_by=self.request.user
        )
        BrandProfile.objects.get_or_create(
            brand=brand,
            defaults={
                'industry': brand.industry or '',
                'brand_voice': brand.voice or '',
                'target_audience': brand.target_audience or ''
            }
        )
        BrandVoice.objects.get_or_create(brand=brand, defaults={'tone': 'Professional'})
        BrandGuideline.objects.get_or_create(brand=brand)

    def update(self, request, *args, **kwargs):
        brand = self.get_object()
        role = get_user_workspace_role(request.user, brand.workspace)
        if role not in ['OWNER', 'ADMIN', 'MANAGER']:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        brand = self.get_object()
        role = get_user_workspace_role(request.user, brand.workspace)
        if role not in ['OWNER', 'ADMIN']:
            return Response({'error': 'Only workspace owners and admins can delete brands.'}, status=status.HTTP_403_FORBIDDEN)
        brand.is_active = False
        brand.save()
        return Response({'message': 'Brand deleted successfully.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'post', 'put', 'patch'], url_path='profile')
    def profile(self, request, pk=None):
        brand = self.get_object()
        role = get_user_workspace_role(request.user, brand.workspace)
        if not role:
            return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        profile, created = BrandProfile.objects.get_or_create(brand=brand)
        if request.method == 'GET':
            return Response(BrandProfileSerializer(profile).data)

        if role not in ['OWNER', 'ADMIN', 'MANAGER']:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = BrandProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='knowledge')
    def knowledge(self, request, pk=None):
        brand = self.get_object()
        role = get_user_workspace_role(request.user, brand.workspace)
        if not role:
            return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            items = BrandKnowledge.objects.filter(brand=brand, is_active=True)
            return Response(BrandKnowledgeSerializer(items, many=True).data)

        if role not in ['OWNER', 'ADMIN', 'MANAGER']:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = BrandKnowledgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(brand=brand, is_active=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='social-accounts')
    def social_accounts(self, request, pk=None):
        brand = self.get_object()
        accounts = SocialAccount.objects.filter(brand=brand)
        serializer = SocialAccountSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'post', 'put', 'patch'], url_path='voice')
    def voice(self, request, pk=None):
        brand = self.get_object()
        voice, created = BrandVoice.objects.get_or_create(brand=brand, defaults={'tone': 'Professional'})
        if request.method == 'GET':
            return Response(BrandVoiceSerializer(voice).data)
        
        serializer = BrandVoiceSerializer(voice, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post', 'put', 'patch'], url_path='guidelines')
    def guidelines(self, request, pk=None):
        brand = self.get_object()
        guideline, created = BrandGuideline.objects.get_or_create(brand=brand)
        if request.method == 'GET':
            return Response(BrandGuidelineSerializer(guideline).data)
        
        serializer = BrandGuidelineSerializer(guideline, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='assets')
    def assets(self, request, pk=None):
        brand = self.get_object()
        if request.method == 'GET':
            assets = BrandAsset.objects.filter(brand=brand)
            return Response(BrandAssetSerializer(assets, many=True).data)
        
        serializer = BrandAssetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(brand=brand)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class BrandProfileViewSet(viewsets.ModelViewSet):
    serializer_class = BrandProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BrandProfile.objects.filter(
            brand__workspace__members__user=self.request.user,
            brand__workspace__members__status='ACTIVE'
        ).distinct()

class BrandKnowledgeViewSet(viewsets.ModelViewSet):
    serializer_class = BrandKnowledgeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BrandKnowledge.objects.filter(
            brand__workspace__members__user=self.request.user,
            brand__workspace__members__status='ACTIVE',
            is_active=True
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        brand_id = self.request.data.get('brand')
        brand = get_object_or_404(Brand, id=brand_id)
        role = get_user_workspace_role(self.request.user, brand.workspace)
        if not role:
            raise PermissionDenied('You are not a member of this workspace.')
        serializer.save(brand=brand)

class BrandAssetViewSet(viewsets.ModelViewSet):
    serializer_class = BrandAssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BrandAsset.objects.filter(
            brand__workspace__members__user=self.request.user,
            brand__workspace__members__status='ACTIVE'
        ).distinct()

class BrandVoiceViewSet(viewsets.ModelViewSet):
    serializer_class = BrandVoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BrandVoice.objects.filter(
            brand__workspace__members__user=self.request.user,
            brand__workspace__members__status='ACTIVE'
        ).distinct()

class BrandGuidelineViewSet(viewsets.ModelViewSet):
    serializer_class = BrandGuidelineSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BrandGuideline.objects.filter(
            brand__workspace__members__user=self.request.user,
            brand__workspace__members__status='ACTIVE'
        ).distinct()

class SocialAccountViewSet(viewsets.ModelViewSet):
    serializer_class = SocialAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return SocialAccount.objects.filter(
            models.Q(personal_space__user=user) |
            models.Q(user=user) |
            models.Q(
                brand__workspace__members__user=user,
                brand__workspace__members__status='ACTIVE'
            )
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(connected_by=self.request.user, user=self.request.user)

    @action(detail=True, methods=['post'], url_path='disconnect')
    def disconnect(self, request, pk=None):
        account = self.get_object()
        if account.personal_space:
            if account.personal_space.user != request.user:
                return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        elif account.brand:
            role = get_user_workspace_role(request.user, account.brand.workspace)
            if role not in ['OWNER', 'ADMIN', 'MANAGER']:
                return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        OAuthTokenService.revoke_and_delete_tokens(account)
        account.delete()
        return Response({'message': 'Social account disconnected successfully.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='refresh')
    def refresh(self, request, pk=None):
        account = self.get_object()
        if account.personal_space:
            if account.personal_space.user != request.user:
                return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        elif account.brand:
            role = get_user_workspace_role(request.user, account.brand.workspace)
            if role not in ['OWNER', 'ADMIN', 'MANAGER']:
                return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        tokens = OAuthTokenService.get_tokens(account)
        if not tokens or not tokens.get('refresh_token'):
            return Response({'error': 'No refresh token available.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            provider = get_provider(account.platform)
            refreshed = provider.refresh_token(tokens['refresh_token'])
            
            token_obj = OAuthTokenService.store_tokens(
                social_account=account,
                access_token=refreshed['access_token'],
                refresh_token=refreshed.get('refresh_token', tokens['refresh_token']),
                expires_at=refreshed.get('expires_at')
            )

            return Response(OAuthTokenSerializer(token_obj).data, status=status.HTTP_200_OK)
        except (ValueError, ValidationError) as e:
            err_msg = e.detail if hasattr(e, 'detail') else str(e)
            return Response({'error': err_msg}, status=status.HTTP_400_BAD_REQUEST)

class PlatformCredentialViewSet(viewsets.ModelViewSet):
    serializer_class = PlatformCredentialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PlatformCredential.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OAuthTokenViewSet(viewsets.ModelViewSet):
    serializer_class = OAuthTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return OAuthToken.objects.filter(
            models.Q(social_account__personal_space__user=user) |
            models.Q(social_account__user=user) |
            models.Q(
                social_account__brand__workspace__members__user=user,
                social_account__brand__workspace__members__status='ACTIVE'
            )
        ).distinct()

class OAuthProvidersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(list_providers(), status=status.HTTP_200_OK)

class OAuthAuthorizeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        provider_name = request.query_params.get('provider')
        account_type = request.query_params.get('account_type', 'personal').lower()
        brand_id = request.query_params.get('brand_id')
        redirect_uri = request.query_params.get('redirect_uri', 'https://app.syncflowai.com/oauth/callback')

        if not provider_name:
            return Response({'error': 'provider parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if account_type == 'brand':
            if not brand_id:
                return Response({'error': 'brand_id is required for brand social accounts.'}, status=status.HTTP_400_BAD_REQUEST)
            brand = get_object_or_404(Brand, id=brand_id)
            role = get_user_workspace_role(request.user, brand.workspace)
            if role not in ['OWNER', 'ADMIN', 'MANAGER']:
                return Response({'error': 'You do not have permission to connect social accounts to this brand.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            provider = get_provider(provider_name)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        state = f"state_{uuid.uuid4().hex}"
        auth_url = provider.get_authorization_url(redirect_uri, state)

        return Response({
            'authorization_url': auth_url,
            'provider': provider_name,
            'state': state,
            'account_type': account_type,
            'brand_id': brand_id
        }, status=status.HTTP_200_OK)

class OAuthCallbackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        provider_name = request.data.get('provider')
        code = request.data.get('code')
        account_type = str(request.data.get('account_type', 'personal')).lower()
        brand_id = request.data.get('brand_id')
        redirect_uri = request.data.get('redirect_uri', 'https://app.syncflowai.com/oauth/callback')

        if not provider_name or not code:
            return Response({'error': 'provider and code are required.'}, status=status.HTTP_400_BAD_REQUEST)

        brand = None
        personal_space = None

        if account_type == 'brand':
            if not brand_id:
                return Response({'error': 'brand_id is required for brand social accounts.'}, status=status.HTTP_400_BAD_REQUEST)
            brand = get_object_or_404(Brand, id=brand_id)
            role = get_user_workspace_role(request.user, brand.workspace)
            if role not in ['OWNER', 'ADMIN', 'MANAGER']:
                return Response({'error': 'Permission denied for this brand workspace.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            personal_space, _ = PersonalSpace.objects.get_or_create(user=request.user)

        try:
            provider = get_provider(provider_name)
            token_data = provider.exchange_code(code, redirect_uri)
        except (ValueError, ValidationError) as e:
            err_msg = e.detail if hasattr(e, 'detail') else str(e)
            return Response({'error': err_msg}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if account_type == 'brand':
                account, created = SocialAccount.objects.get_or_create(
                    brand=brand,
                    platform=provider_name.lower(),
                    username=token_data['username'],
                    defaults={
                        'display_name': token_data.get('display_name', ''),
                        'profile_image_url': token_data.get('profile_image_url', ''),
                        'account_id': token_data.get('account_id', ''),
                        'connected_by': request.user,
                        'is_active': True
                    }
                )
            else:
                account, created = SocialAccount.objects.get_or_create(
                    personal_space=personal_space,
                    platform=provider_name.lower(),
                    username=token_data['username'],
                    defaults={
                        'display_name': token_data.get('display_name', ''),
                        'profile_image_url': token_data.get('profile_image_url', ''),
                        'account_id': token_data.get('account_id', ''),
                        'connected_by': request.user,
                        'user': request.user,
                        'is_active': True
                    }
                )

            if not created:
                account.display_name = token_data.get('display_name', account.display_name)
                account.profile_image_url = token_data.get('profile_image_url', account.profile_image_url)
                account.is_active = True
                account.connected_by = request.user
                account.save()

            OAuthTokenService.store_tokens(
                social_account=account,
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', ''),
                expires_at=token_data.get('expires_at')
            )

        serializer = SocialAccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ConnectSocialAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, platform):
        username = request.data.get('username', 'marvel_creator')
        brand_id = request.data.get('brand_id')
        
        brand = None
        personal_space = None
        if brand_id:
            try:
                brand = Brand.objects.get(
                    id=brand_id,
                    workspace__members__user=request.user,
                    workspace__members__status='ACTIVE'
                )
            except Brand.DoesNotExist:
                return Response({'error': 'Brand not found or permission denied'}, status=status.HTTP_404_NOT_FOUND)
        else:
            personal_space, _ = PersonalSpace.objects.get_or_create(user=request.user)

        avatar_map = {
            'youtube': 'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=150&q=80',
            'tiktok': 'https://images.unsplash.com/photo-1598128558393-70ff21433be0?auto=format&fit=crop&w=150&q=80',
            'instagram': 'https://images.unsplash.com/photo-1611224885990-ab7363d1f2a9?auto=format&fit=crop&w=150&q=80',
            'facebook': 'https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=150&q=80',
            'linkedin': 'https://images.unsplash.com/photo-1560179707-f14e90ef3623?auto=format&fit=crop&w=150&q=80',
            'twitter': 'https://images.unsplash.com/photo-1611605698335-8b15d27e03f2?auto=format&fit=crop&w=150&q=80',
            'x': 'https://images.unsplash.com/photo-1611605698335-8b15d27e03f2?auto=format&fit=crop&w=150&q=80'
        }
        
        profile_image = avatar_map.get(platform.lower(), 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80')
        display_name = f"{username.capitalize()} on {platform.capitalize()}"

        account = SocialAccount.objects.create(
            user=request.user,
            personal_space=personal_space,
            brand=brand,
            connected_by=request.user,
            platform=platform,
            username=username,
            display_name=display_name,
            profile_image_url=profile_image,
            is_active=True
        )

        OAuthTokenService.store_tokens(
            social_account=account,
            access_token=f"access_tok_{uuid.uuid4()}",
            refresh_token=f"refresh_tok_{uuid.uuid4()}",
            expires_at=timezone.now() + timedelta(days=30)
        )

        serializer = SocialAccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class DisconnectSocialAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            account = SocialAccount.objects.get(id=pk)
            if account.personal_space and account.personal_space.user != request.user:
                return Response({'error': 'Social account not found'}, status=status.HTTP_404_NOT_FOUND)
            elif account.brand and get_user_workspace_role(request.user, account.brand.workspace) not in ['OWNER', 'ADMIN', 'MANAGER']:
                return Response({'error': 'Social account not found'}, status=status.HTTP_404_NOT_FOUND)

            account.delete()
            return Response({'message': 'Social account disconnected successfully'}, status=status.HTTP_200_OK)
        except SocialAccount.DoesNotExist:
            return Response({'error': 'Social account not found'}, status=status.HTTP_404_NOT_FOUND)
