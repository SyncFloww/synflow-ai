import logging
from typing import Dict, Any, Optional
from datetime import datetime
from django.utils import timezone

from social.models import SocialAccount, OAuthToken, OAuthAuditLog
from social.security import TokenEncryptionService

logger = logging.getLogger(__name__)

class OAuthTokenService:
    """
    Backend service abstraction for managing encrypted OAuth credentials and health.
    
    Security & Architecture Guarantees:
    - Encrypts access and refresh tokens at rest using AES-256 (Fernet).
    - Prevents raw token exposure in API responses and serializers.
    - Manages token refresh, revocation, connection verification, and audit logging.
    """

    @staticmethod
    def store_tokens(
        social_account: SocialAccount,
        access_token: str,
        refresh_token: str = '',
        expires_at: Optional[datetime] = None,
        granted_scopes: Optional[list] = None,
        capabilities: Optional[list] = None
    ) -> OAuthToken:
        """
        Encrypted storage of OAuth tokens for a SocialAccount.
        """
        token_obj, _ = OAuthToken.objects.get_or_create(social_account=social_account)
        token_obj.access_token = access_token
        if refresh_token:
            token_obj.refresh_token = refresh_token
        if expires_at is not None:
            token_obj.expires_at = expires_at
        token_obj.save()

        # Update SocialAccount status and capabilities
        social_account.status = 'ACTIVE'
        social_account.is_active = True
        social_account.last_verified_at = timezone.now()
        social_account.last_error = ''
        if granted_scopes:
            social_account.granted_scopes = granted_scopes
        if capabilities:
            social_account.capabilities = capabilities
        social_account.save()

        return token_obj

    @staticmethod
    def get_tokens(social_account: SocialAccount) -> Optional[Dict[str, Any]]:
        """
        Internal backend method to retrieve decrypted tokens for provider operations.
        NEVER expose output of this method in API serializers or HTTP responses.
        """
        token_obj = OAuthToken.objects.filter(social_account=social_account).first()
        if not token_obj:
            return None
        return {
            'access_token': token_obj.access_token,
            'refresh_token': token_obj.refresh_token,
            'expires_at': token_obj.expires_at,
            'is_expired': token_obj.is_expired
        }

    @staticmethod
    def get_valid_access_token(social_account: SocialAccount) -> Optional[str]:
        """
        Retrieves a valid access_token, refreshing it if expired.
        """
        tokens = OAuthTokenService.get_tokens(social_account)
        if not tokens or not tokens['access_token']:
            social_account.status = 'REAUTH_REQUIRED'
            social_account.save()
            return None

        if tokens['is_expired']:
            if tokens['refresh_token']:
                from social.providers.registry import get_provider
                try:
                    provider = get_provider(social_account.platform)
                    refreshed = provider.refresh_token(tokens['refresh_token'])
                    OAuthTokenService.store_tokens(
                        social_account=social_account,
                        access_token=refreshed['access_token'],
                        refresh_token=refreshed.get('refresh_token', tokens['refresh_token']),
                        expires_at=refreshed.get('expires_at')
                    )
                    return refreshed['access_token']
                except Exception as e:
                    logger.error(f"Token refresh failed for account {social_account.id}: {e}")
                    social_account.status = 'REAUTH_REQUIRED'
                    social_account.last_error = f"Token refresh failed: {str(e)}"
                    social_account.save()
                    return None
            else:
                social_account.status = 'EXPIRED'
                social_account.save()
                return None

        return tokens['access_token']

    @staticmethod
    def verify_connection(social_account: SocialAccount, user=None, ip_address=None) -> Dict[str, Any]:
        """
        Actively checks connection health with provider API.
        """
        from social.providers.registry import get_provider
        
        access_token = OAuthTokenService.get_valid_access_token(social_account)
        if not access_token:
            status_code = social_account.status or 'REAUTH_REQUIRED'
            return {
                'is_valid': False,
                'status': status_code,
                'message': 'Token expired or invalid. Re-authentication required.'
            }

        try:
            provider = get_provider(social_account.platform)
            info = provider.get_account_info(access_token)
            
            social_account.status = 'ACTIVE'
            social_account.last_verified_at = timezone.now()
            social_account.last_error = ''
            if info.get('display_name'):
                social_account.display_name = info['display_name']
            if info.get('profile_image_url'):
                social_account.profile_image_url = info['profile_image_url']
            social_account.save()

            if user:
                OAuthAuditLog.objects.create(
                    workspace=social_account.brand.workspace if social_account.brand else None,
                    brand=social_account.brand,
                    user=user,
                    platform=social_account.platform,
                    action='VERIFIED',
                    status='SUCCESS',
                    details={'account_id': social_account.account_id},
                    ip_address=ip_address
                )

            return {
                'is_valid': True,
                'status': 'ACTIVE',
                'last_verified_at': social_account.last_verified_at.isoformat(),
                'display_name': social_account.display_name,
                'message': 'Social account connection is healthy.'
            }
        except Exception as e:
            social_account.status = 'ERROR'
            social_account.last_error = str(e)
            social_account.save()

            return {
                'is_valid': False,
                'status': 'ERROR',
                'message': f"Connection verification failed: {str(e)}"
            }

    @staticmethod
    def disconnect_account(social_account: SocialAccount, user, ip_address=None) -> bool:
        """
        Revokes token access with provider and securely disconnects account.
        """
        try:
            tokens = OAuthTokenService.get_tokens(social_account)
            if tokens and tokens['access_token']:
                from social.providers.registry import get_provider
                provider = get_provider(social_account.platform)
                provider.revoke(tokens['access_token'])
        except Exception as e:
            logger.warning(f"Provider token revocation failed for account {social_account.id}: {e}")

        # Delete token record
        OAuthToken.objects.filter(social_account=social_account).delete()

        # Update SocialAccount status
        social_account.status = 'DISCONNECTED'
        social_account.is_active = False
        social_account.save()

        # Record Audit Log
        OAuthAuditLog.objects.create(
            workspace=social_account.brand.workspace if social_account.brand else None,
            brand=social_account.brand,
            user=user,
            platform=social_account.platform,
            action='DISCONNECTED',
            status='SUCCESS',
            details={'account_id': social_account.account_id, 'username': social_account.username},
            ip_address=ip_address
        )

        return True
