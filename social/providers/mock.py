import uuid
from datetime import timedelta
from typing import Dict, Any, Optional
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .base import BaseSocialProvider

# Global memory registry to track used codes in Mock provider (prevent code reuse attack tests)
_used_mock_codes = set()

class MockSocialProvider(BaseSocialProvider):
    """
    Safe Mock Social Provider for testing and local development.
    Simulates complete OAuth lifecycle without external API calls.
    """

    def __init__(self, provider_name: str = "mock"):
        self.provider_name = provider_name.lower()

    def get_capabilities(self) -> list:
        return [
            "PROFILE_READ",
            "CONTENT_READ",
            "CONTENT_PUBLISH",
            "COMMENTS_READ",
            "COMMENTS_WRITE",
            "ANALYTICS_READ",
            "MEDIA_UPLOAD"
        ]

    def get_scopes(self) -> list:
        return ["read_profile", "publish_content", "read_analytics"]

    def get_authorization_url(self, redirect_uri: str, state: str, code_challenge: Optional[str] = None, extra_params: Optional[Dict[str, Any]] = None) -> str:
        mock_code = f"mock_code_{self.provider_name}_{uuid.uuid4().hex[:8]}"
        base_url = redirect_uri or "https://app.syncfloww.com/oauth/callback"
        query_delimiter = "&" if "?" in base_url else "?"
        return f"{base_url}{query_delimiter}code={mock_code}&state={state}&provider={self.provider_name}"

    def exchange_code(self, code: str, redirect_uri: str, code_verifier: Optional[str] = None) -> Dict[str, Any]:
        if not code or not isinstance(code, str):
            raise ValidationError("Invalid authorization code.")

        if code in _used_mock_codes:
            raise ValidationError("Authorization code has already been used.")

        if "invalid" in code.lower() or "fail" in code.lower():
            raise ValidationError("Authorization code is invalid or expired.")

        _used_mock_codes.add(code)

        mock_id = code.split('_')[-1] if '_' in code else uuid.uuid4().hex[:8]
        username = f"{self.provider_name}_creator_{mock_id}"
        display_name = f"{username.capitalize()} ({self.provider_name.capitalize()})"

        avatar_map = {
            'youtube': 'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=150&q=80',
            'tiktok': 'https://images.unsplash.com/photo-1598128558393-70ff21433be0?auto=format&fit=crop&w=150&q=80',
            'instagram': 'https://images.unsplash.com/photo-1611224885990-ab7363d1f2a9?auto=format&fit=crop&w=150&q=80',
            'facebook': 'https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=150&q=80',
            'linkedin': 'https://images.unsplash.com/photo-1560179707-f14e90ef3623?auto=format&fit=crop&w=150&q=80',
            'twitter': 'https://images.unsplash.com/photo-1611605698335-8b15d27e03f2?auto=format&fit=crop&w=150&q=80'
        }
        profile_image = avatar_map.get(self.provider_name, 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80')

        return {
            'access_token': f"mock_access_tok_{self.provider_name}_{uuid.uuid4().hex}",
            'refresh_token': f"mock_refresh_tok_{self.provider_name}_{uuid.uuid4().hex}",
            'expires_at': timezone.now() + timedelta(days=30),
            'account_id': f"acc_{self.provider_name}_{mock_id}",
            'username': username,
            'display_name': display_name,
            'profile_image_url': profile_image,
            'granted_scopes': self.get_scopes(),
            'capabilities': self.get_capabilities(),
            'raw_response': {'provider': self.provider_name, 'mock': True, 'code_used': code}
        }

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        if not refresh_token or "invalid" in refresh_token.lower() or "fail" in refresh_token.lower():
            raise ValidationError("Invalid or expired refresh token.")

        return {
            'access_token': f"mock_access_tok_refreshed_{self.provider_name}_{uuid.uuid4().hex}",
            'refresh_token': f"mock_refresh_tok_refreshed_{self.provider_name}_{uuid.uuid4().hex}",
            'expires_at': timezone.now() + timedelta(days=30)
        }

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        if not access_token or "invalid" in access_token.lower():
            raise ValidationError("Invalid access token.")

        return {
            'account_id': f"acc_{self.provider_name}_info",
            'username': f"{self.provider_name}_user",
            'display_name': f"User on {self.provider_name.capitalize()}",
            'profile_image_url': 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80'
        }

    def revoke(self, token: str) -> bool:
        return True
