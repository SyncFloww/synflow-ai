import os
import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from social.capabilities import SocialCapability
from .base import BaseSocialProvider
from .mock import MockSocialProvider

logger = logging.getLogger(__name__)

class TikTokOAuthProvider(BaseSocialProvider):
    """
    TikTok OAuth Provider.
    Supports TikTok Content Posting & Login Kit v2 API.
    """
    provider_name: str = "tiktok"

    def __init__(self):
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY", "")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "")
        self._mock = MockSocialProvider(provider_name="tiktok")

    def get_capabilities(self) -> List[str]:
        return [
            SocialCapability.PROFILE_READ.value,
            SocialCapability.CONTENT_READ.value,
            SocialCapability.CONTENT_PUBLISH.value,
            SocialCapability.ANALYTICS_READ.value,
            SocialCapability.MEDIA_UPLOAD.value,
        ]

    def get_scopes(self) -> List[str]:
        return [
            "user.info.basic",
            "video.list",
            "video.publish",
            "video.upload"
        ]

    def get_authorization_url(self, redirect_uri: str, state: str, code_challenge: Optional[str] = None) -> str:
        if not self.client_key:
            return self._mock.get_authorization_url(redirect_uri, state, code_challenge)

        base_url = "https://www.tiktok.com/v2/auth/authorize/"
        scope = ",".join(self.get_scopes())
        return f"{base_url}?client_key={self.client_key}&scope={scope}&response_type=code&redirect_uri={redirect_uri}&state={state}"

    def exchange_code(self, code: str, redirect_uri: str, code_verifier: Optional[str] = None) -> Dict[str, Any]:
        if not self.client_key or code.startswith("mock_code_"):
            return self._mock.exchange_code(code, redirect_uri, code_verifier)

        try:
            url = "https://open.tiktokapis.com/v2/oauth/token/"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "client_key": self.client_key,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
            res = requests.post(url, headers=headers, data=data, timeout=10)
            res_data = res.json()

            if res.status_code != 200 or "access_token" not in res_data:
                err = res_data.get("error_description", res.text)
                raise ValidationError(f"TikTok OAuth exchange failed: {err}")

            access_token = res_data["access_token"]
            profile = self.get_account_info(access_token)

            return {
                'access_token': access_token,
                'refresh_token': res_data.get('refresh_token', ''),
                'expires_at': timezone.now() + timedelta(seconds=res_data.get('expires_in', 86400)),
                'account_id': profile.get('account_id', res_data.get('open_id', 'tt_user')),
                'username': profile.get('username', 'tt_creator'),
                'display_name': profile.get('display_name', 'TikTok Creator'),
                'profile_image_url': profile.get('profile_image_url', ''),
                'granted_scopes': self.get_scopes(),
                'capabilities': self.get_capabilities(),
                'raw_response': res_data
            }
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to connect TikTok account: {str(e)}")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        if not self.client_key or refresh_token.startswith("mock_"):
            return self._mock.refresh_token(refresh_token)

        try:
            url = "https://open.tiktokapis.com/v2/oauth/token/"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "client_key": self.client_key,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            res = requests.post(url, headers=headers, data=data, timeout=10)
            if res.status_code == 200:
                res_data = res.json()
                return {
                    'access_token': res_data['access_token'],
                    'refresh_token': res_data.get('refresh_token', refresh_token),
                    'expires_at': timezone.now() + timedelta(seconds=res_data.get('expires_in', 86400))
                }
        except Exception as e:
            logger.error(f"TikTok token refresh error: {e}")

        raise ValidationError("Failed to refresh TikTok token.")

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        if access_token.startswith("mock_"):
            return self._mock.get_account_info(access_token)

        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            url = "https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,avatar_url,display_name"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                user_data = res.json().get('data', {}).get('user', {})
                return {
                    'account_id': str(user_data.get('open_id', '')),
                    'username': f"tt_{user_data.get('display_name', '').lower().replace(' ', '_')}",
                    'display_name': user_data.get('display_name', 'TikTok User'),
                    'profile_image_url': user_data.get('avatar_url', '')
                }
        except Exception:
            pass
        return self._mock.get_account_info(access_token)

    def revoke(self, access_token: str) -> bool:
        if access_token.startswith("mock_"):
            return True
        try:
            url = "https://open.tiktokapis.com/v2/oauth/revoke/"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {"client_key": self.client_key, "client_secret": self.client_secret, "token": access_token}
            requests.post(url, headers=headers, data=data, timeout=10)
            return True
        except Exception:
            return False
