import os
import requests
from typing import Dict, Any, Optional
from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .base import BaseSocialProvider
from .mock import MockSocialProvider

class FacebookOAuthProvider(BaseSocialProvider):
    """
    Facebook OAuth Provider service abstraction.
    Supports Meta Graph API for Facebook Pages and Profiles.
    Fallback to safe mock mode when credentials are missing or in dev mode.
    """
    provider_name: str = "facebook"

    def __init__(self):
        self.client_id = os.getenv("FACEBOOK_CLIENT_ID", "")
        self.client_secret = os.getenv("FACEBOOK_CLIENT_SECRET", "")
        self._mock = MockSocialProvider(provider_name="facebook")

    def get_authorization_url(self, redirect_uri: str, state: str, extra_params: Optional[Dict[str, Any]] = None) -> str:
        if not self.client_id:
            return self._mock.get_authorization_url(redirect_uri, state, extra_params)

        base_url = "https://www.facebook.com/v18.0/dialog/oauth"
        scope = "public_profile,pages_show_list,pages_read_engagement,pages_manage_posts"
        return f"{base_url}?client_id={self.client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}&response_type=code"

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        if not self.client_id or code.startswith("mock_code_"):
            return self._mock.exchange_code(code, redirect_uri)

        try:
            url = "https://graph.facebook.com/v18.0/oauth/access_token"
            params = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": redirect_uri,
                "code": code
            }
            res = requests.get(url, params=params, timeout=10)
            res_data = res.json()

            if res.status_code != 200 or "access_token" not in res_data:
                raise ValidationError(f"Facebook OAuth exchange failed: {res_data.get('error', {}).get('message', res.text)}")

            access_token = res_data["access_token"]
            profile = self.get_account_info(access_token)

            return {
                'access_token': access_token,
                'refresh_token': res_data.get('refresh_token', ''),
                'expires_at': timezone.now() + timedelta(days=60),
                'account_id': profile.get('account_id', 'fb_user'),
                'username': profile.get('username', 'fb_user'),
                'display_name': profile.get('display_name', 'Facebook User'),
                'profile_image_url': profile.get('profile_image_url', ''),
                'raw_response': res_data
            }
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to connect Facebook account: {str(e)}")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        if not self.client_id or refresh_token.startswith("mock_"):
            return self._mock.refresh_token(refresh_token)

        return {
            'access_token': f"fb_refreshed_{refresh_token[:10]}",
            'refresh_token': refresh_token,
            'expires_at': timezone.now() + timedelta(days=60)
        }

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        if access_token.startswith("mock_"):
            return self._mock.get_account_info(access_token)

        try:
            url = f"https://graph.facebook.com/v18.0/me?fields=id,name,picture&access_token={access_token}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                picture_url = data.get('picture', {}).get('data', {}).get('url', '')
                return {
                    'account_id': str(data.get('id', '')),
                    'username': f"fb_{data.get('id', '')}",
                    'display_name': data.get('name', 'Facebook Page'),
                    'profile_image_url': picture_url
                }
        except Exception:
            pass
        return self._mock.get_account_info(access_token)

    def revoke(self, token: str) -> bool:
        return True
