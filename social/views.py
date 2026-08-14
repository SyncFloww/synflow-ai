import os
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
        qs = Brand.objects.filter(
            workspace__members__user=self.request.user,
            workspace__members__status='ACTIVE',
            is_active=True
        ).distinct().order_by('-created_at')

        workspace_id = self.request.query_params.get('workspace')
        if workspace_id:
            qs = qs.filter(workspace_id=workspace_id)

        return qs


    def perform_create(self, serializer):
        from workspaces.models import WorkspaceMember, WorkspaceSetting
        from django.utils.text import slugify

        workspace_id = self.request.data.get('workspace') or self.request.data.get('workspace_id')

        if workspace_id:
            # Caller explicitly chose an existing workspace
            workspace = get_object_or_404(Workspace, id=workspace_id)
            role = get_user_workspace_role(self.request.user, workspace)
            if not role:
                raise PermissionDenied('You are not a member of this workspace.')
        else:
            # Auto-create a workspace named after the brand so that brand ≡ workspace
            brand_name = self.request.data.get('name', 'My Brand')
            base_slug = slugify(brand_name) or 'brand'
            slug = base_slug
            counter = 1
            while Workspace.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1

            with transaction.atomic():
                workspace = Workspace.objects.create(
                    owner=self.request.user,
                    created_by=self.request.user,
                    name=brand_name,
                    slug=slug,
                )
                WorkspaceMember.objects.create(
                    workspace=workspace,
                    user=self.request.user,
                    role='OWNER',
                    status='ACTIVE',
                )
                WorkspaceSetting.objects.get_or_create(workspace=workspace)

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
        BrandVoice.objects.get_or_create(brand=brand, defaults={'tone': brand.voice or 'Professional'})
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

from .security import OAuthStateManager
from .models import OAuthAuditLog
from .capabilities import get_capability_metadata

class OAuthProvidersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(list_providers(), status=status.HTTP_200_OK)

class OAuthAuthorizeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, provider=None):
        provider_name = provider or request.query_params.get('provider')
        account_type = request.query_params.get('account_type', 'brand').lower()
        brand_id = request.query_params.get('brand_id')
        redirect_uri = request.query_params.get('redirect_uri') or os.getenv('OAUTH_REDIRECT_BASE_URL', 'https://app.syncfloww.com/oauth/callback')

        if not provider_name:
            return Response({'error': 'provider parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        brand = None
        workspace_id = None
        if account_type == 'brand' or brand_id:
            if not brand_id or not str(brand_id).isdigit():
                return Response({'error': 'Valid brand_id is required for connecting brand social accounts.'}, status=status.HTTP_400_BAD_REQUEST)
            brand = get_object_or_404(Brand, id=int(brand_id))
            role = get_user_workspace_role(request.user, brand.workspace)
            if role not in ['OWNER', 'ADMIN', 'MANAGER']:
                return Response({'error': 'You do not have permission to connect social accounts to this brand.'}, status=status.HTTP_403_FORBIDDEN)
            workspace_id = brand.workspace.id

        try:
            prov = get_provider(provider_name)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Generate cryptographic signed state bound to user, workspace, brand, and PKCE
        pkce_verifier = str(uuid.uuid4().hex)
        signed_state, code_verifier = OAuthStateManager.generate_state(
            user_id=request.user.id,
            workspace_id=workspace_id or 0,
            brand_id=brand.id if brand else 0,
            provider=provider_name,
            code_verifier=pkce_verifier
        )

        auth_url = prov.get_authorization_url(redirect_uri, signed_state, code_challenge=code_verifier)

        # Audit Log
        OAuthAuditLog.objects.create(
            workspace=brand.workspace if brand else None,
            brand=brand,
            user=request.user,
            platform=provider_name.lower(),
            action='OAUTH_INITIATED',
            status='SUCCESS',
            details={'redirect_uri': redirect_uri},
            ip_address=request.META.get('REMOTE_ADDR')
        )

        capabilities = prov.get_capabilities() if hasattr(prov, 'get_capabilities') else []
        scopes = prov.get_scopes() if hasattr(prov, 'get_scopes') else []

        return Response({
            'authorization_url': auth_url,
            'provider': provider_name.lower(),
            'state': signed_state,
            'account_type': 'brand' if brand else 'personal',
            'brand_id': brand.id if brand else None,
            'brand_name': brand.name if brand else None,
            'capabilities': get_capability_metadata(capabilities),
            'scopes': scopes
        }, status=status.HTTP_200_OK)

class OAuthCallbackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, provider=None):
        provider_name = provider or request.data.get('provider')
        code = request.data.get('code')
        state_str = request.data.get('state')
        redirect_uri = request.data.get('redirect_uri') or os.getenv('OAUTH_REDIRECT_BASE_URL', 'https://app.syncfloww.com/oauth/callback')

        if not provider_name or not code:
            return Response({'error': 'provider and code are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Cryptographic State Security Validation
        try:
            state_data = OAuthStateManager.validate_and_consume_state(state_str, provider_name)
        except ValueError as e:
            OAuthAuditLog.objects.create(
                user=request.user,
                platform=provider_name.lower(),
                action='OAUTH_FAILED',
                status='FAILED',
                details={'error': str(e)},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Enforce user isolation
        if state_data['user_id'] != request.user.id:
            return Response({'error': 'State user mismatch. Re-authentication required.'}, status=status.HTTP_403_FORBIDDEN)

        brand = None
        personal_space = None
        if state_data['brand_id']:
            brand = get_object_or_404(Brand, id=state_data['brand_id'])
            role = get_user_workspace_role(request.user, brand.workspace)
            if role not in ['OWNER', 'ADMIN', 'MANAGER']:
                return Response({'error': 'Permission denied for this brand workspace.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            personal_space, _ = PersonalSpace.objects.get_or_create(user=request.user)

        try:
            prov = get_provider(provider_name)
            code_verifier = state_data.get('code_verifier')
            token_data = prov.exchange_code(code, redirect_uri, code_verifier=code_verifier)
        except (ValueError, ValidationError) as e:
            err_msg = e.detail if hasattr(e, 'detail') else str(e)
            OAuthAuditLog.objects.create(
                workspace=brand.workspace if brand else None,
                brand=brand,
                user=request.user,
                platform=provider_name.lower(),
                action='OAUTH_FAILED',
                status='FAILED',
                details={'error': str(err_msg)},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return Response({'error': str(err_msg)}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            account_id = token_data.get('account_id', '') or token_data.get('username', '')
            if brand:
                account, created = SocialAccount.objects.get_or_create(
                    brand=brand,
                    platform=provider_name.lower(),
                    account_id=account_id,
                    defaults={
                        'username': token_data['username'],
                        'display_name': token_data.get('display_name', ''),
                        'profile_image_url': token_data.get('profile_image_url', ''),
                        'connected_by': request.user,
                        'status': 'ACTIVE',
                        'is_active': True
                    }
                )
            else:
                account, created = SocialAccount.objects.get_or_create(
                    personal_space=personal_space,
                    platform=provider_name.lower(),
                    account_id=account_id,
                    defaults={
                        'username': token_data['username'],
                        'display_name': token_data.get('display_name', ''),
                        'profile_image_url': token_data.get('profile_image_url', ''),
                        'connected_by': request.user,
                        'user': request.user,
                        'status': 'ACTIVE',
                        'is_active': True
                    }
                )

            account.username = token_data.get('username', account.username)
            account.display_name = token_data.get('display_name', account.display_name)
            account.profile_image_url = token_data.get('profile_image_url', account.profile_image_url)
            account.status = 'ACTIVE'
            account.is_active = True
            account.connected_by = request.user
            account.save()

            # Store encrypted tokens
            OAuthTokenService.store_tokens(
                social_account=account,
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', ''),
                expires_at=token_data.get('expires_at'),
                granted_scopes=token_data.get('granted_scopes', []),
                capabilities=token_data.get('capabilities', [])
            )

            OAuthAuditLog.objects.create(
                workspace=brand.workspace if brand else None,
                brand=brand,
                user=request.user,
                platform=provider_name.lower(),
                action='OAUTH_SUCCESS',
                status='SUCCESS',
                details={'account_id': account.account_id, 'username': account.username},
                ip_address=request.META.get('REMOTE_ADDR')
            )

        serializer = SocialAccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ConnectSocialAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, platform):
        # Deprecated: Redirect client to OAuth authorize endpoint
        return Response({
            'message': f"To connect {platform}, please call GET /api/social/oauth/{platform}/authorize/ to initiate standard OAuth consent."
        }, status=status.HTTP_400_BAD_REQUEST)

class VerifySocialAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            account = SocialAccount.objects.get(id=pk)
            if account.brand and get_user_workspace_role(request.user, account.brand.workspace) not in ['OWNER', 'ADMIN', 'MANAGER']:
                return Response({'error': 'Access denied to this brand account.'}, status=status.HTTP_403_FORBIDDEN)
            elif account.personal_space and account.personal_space.user != request.user:
                return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

            res = OAuthTokenService.verify_connection(account, user=request.user, ip_address=request.META.get('REMOTE_ADDR'))
            return Response(res, status=status.HTTP_200_OK)
        except SocialAccount.DoesNotExist:
            return Response({'error': 'Social account not found.'}, status=status.HTTP_404_NOT_FOUND)

class DisconnectSocialAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            account = SocialAccount.objects.get(id=pk)
            if account.brand and get_user_workspace_role(request.user, account.brand.workspace) not in ['OWNER', 'ADMIN', 'MANAGER']:
                return Response({'error': 'Social account not found'}, status=status.HTTP_404_NOT_FOUND)
            elif account.personal_space and account.personal_space.user != request.user:
                return Response({'error': 'Social account not found'}, status=status.HTTP_404_NOT_FOUND)

            OAuthTokenService.disconnect_account(account, user=request.user, ip_address=request.META.get('REMOTE_ADDR'))
            return Response({'message': 'Social account disconnected successfully'}, status=status.HTTP_200_OK)
        except SocialAccount.DoesNotExist:
            return Response({'error': 'Social account not found'}, status=status.HTTP_404_NOT_FOUND)
