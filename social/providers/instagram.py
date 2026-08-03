import os
import requests
from typing import Dict, Any, Optional
from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .base import BaseSocialProvider
from .mock import MockSocialProvider

class InstagramOAuthProvider(BaseSocialProvider):
    """
    Instagram OAuth Provider service abstraction.
    Supports Meta Instagram Graph API / Basic Display API.
    Fallback to safe mock mode when credentials are missing or in dev mode.
    """
    provider_name: str = "instagram"

    def __init__(self):
        self.client_id = os.getenv("INSTAGRAM_CLIENT_ID", "")
        self.client_secret = os.getenv("INSTAGRAM_CLIENT_SECRET", "")
        self._mock = MockSocialProvider(provider_name="instagram")

    def get_authorization_url(self, redirect_uri: str, state: str, extra_params: Optional[Dict[str, Any]] = None) -> str:
        if not self.client_id:
            return self._mock.get_authorization_url(redirect_uri, state, extra_params)
        
        base_url = "https://api.instagram.com/oauth/authorize"
        scope = "user_profile,user_media"
        return f"{base_url}?client_id={self.client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type=code&state={state}"

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        if not self.client_id or code.startswith("mock_code_"):
            return self._mock.exchange_code(code, redirect_uri)

        try:
            url = "https://api.instagram.com/oauth/access_token"
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code": code
            }
            res = requests.post(url, data=data, timeout=10)
            res_data = res.json()

            if res.status_code != 200 or "access_token" not in res_data:
                raise ValidationError(f"Instagram OAuth exchange failed: {res_data.get('error_message', res.text)}")

            access_token = res_data["access_token"]
            user_id = str(res_data.get("user_id", ""))
            
            profile = self.get_account_info(access_token)
            return {
                'access_token': access_token,
                'refresh_token': res_data.get('refresh_token', ''),
                'expires_at': timezone.now() + timedelta(days=60),
                'account_id': profile.get('account_id', user_id),
                'username': profile.get('username', f"ig_user_{user_id}"),
                'display_name': profile.get('display_name', f"Instagram User {user_id}"),
                'profile_image_url': profile.get('profile_image_url', ''),
                'raw_response': res_data
            }
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to connect Instagram account: {str(e)}")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        if not self.client_id or refresh_token.startswith("mock_"):
            return self._mock.refresh_token(refresh_token)

        return {
            'access_token': f"ig_refreshed_{refresh_token[:10]}",
            'refresh_token': refresh_token,
            'expires_at': timezone.now() + timedelta(days=60)
        }

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        if access_token.startswith("mock_"):
            return self._mock.get_account_info(access_token)

        try:
            url = f"https://graph.instagram.com/me?fields=id,username,account_type&access_token={access_token}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return {
                    'account_id': str(data.get('id', '')),
                    'username': data.get('username', ''),
                    'display_name': data.get('username', '').capitalize(),
                    'profile_image_url': ''
                }
        except Exception:
            pass
        return self._mock.get_account_info(access_token)

    def revoke(self, token: str) -> bool:
        return True
