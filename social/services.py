from typing import Dict, Any, Optional
from datetime import datetime
from django.utils import timezone
from social.models import SocialAccount, OAuthToken

class OAuthTokenService:
    """
    Secure backend service abstraction for managing OAuth credentials and tokens.
    
    Key Security & Abstraction Guarantee:
    - Encapsulates token creation, retrieval, refresh, and revocation operations.
    - Isolates raw access and refresh tokens from API serializers and frontend HTTP responses.
    - Frontend serializers only receive connection status and expiration metadata.
    """

    @staticmethod
    def store_tokens(
        social_account: SocialAccount,
        access_token: str,
        refresh_token: str = '',
        expires_at: Optional[datetime] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> OAuthToken:
        """
        Stores or updates OAuth tokens securely for a SocialAccount.
        """
        token_obj, _ = OAuthToken.objects.get_or_create(social_account=social_account)
        token_obj.access_token = access_token
        if refresh_token:
            token_obj.refresh_token = refresh_token
        if expires_at is not None:
            token_obj.expires_at = expires_at
        token_obj.save()
        return token_obj

    @staticmethod
    def get_tokens(social_account: SocialAccount) -> Optional[Dict[str, Any]]:
        """
        Internal backend method to retrieve raw tokens for platform operations.
        CRITICAL: NEVER expose output of this method in API responses or serializers.
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
        Retrieves a valid access_token, refreshing it if expired and a refresh token exists.
        """
        tokens = OAuthTokenService.get_tokens(social_account)
        if not tokens or not tokens['access_token']:
            return None

        if tokens['is_expired'] and tokens['refresh_token']:
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
            except Exception:
                return None

        return tokens['access_token']

    @staticmethod
    def is_token_valid(social_account: SocialAccount) -> bool:
        """
        Checks if the account has an active and unexpired OAuth token.
        """
        tokens = OAuthTokenService.get_tokens(social_account)
        if not tokens or not tokens['access_token']:
            return False
        return not tokens['is_expired']

    @staticmethod
    def revoke_and_delete_tokens(social_account: SocialAccount) -> bool:
        """
        Revokes token with platform provider and removes token record.
        """
        try:
            tokens = OAuthTokenService.get_tokens(social_account)
            if tokens and tokens['access_token']:
                from social.providers.registry import get_provider
                provider = get_provider(social_account.platform)
                provider.revoke(tokens['access_token'])
        except Exception:
            pass

        OAuthToken.objects.filter(social_account=social_account).delete()
        return True
