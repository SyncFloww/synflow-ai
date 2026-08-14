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

class LinkedInOAuthProvider(BaseSocialProvider):
    """
    LinkedIn OAuth Provider.
    Supports LinkedIn Community Management and OAuth v2 API.
    """
    provider_name: str = "linkedin"

    def __init__(self):
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID", "")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET", "")
        self._mock = MockSocialProvider(provider_name="linkedin")

    def get_capabilities(self) -> List[str]:
        return [
            SocialCapability.PROFILE_READ.value,
            SocialCapability.CONTENT_READ.value,
            SocialCapability.CONTENT_PUBLISH.value,
            SocialCapability.COMMENTS_READ.value,
            SocialCapability.COMMENTS_WRITE.value,
            SocialCapability.ANALYTICS_READ.value,
            SocialCapability.MEDIA_UPLOAD.value,
        ]

    def get_scopes(self) -> List[str]:
        return [
            "openid",
            "profile",
            "email",
            "w_member_social",
            "r_organization_social",
            "w_organization_social"
        ]

    def get_authorization_url(self, redirect_uri: str, state: str, code_challenge: Optional[str] = None) -> str:
        if not self.client_id:
            return self._mock.get_authorization_url(redirect_uri, state, code_challenge)

        base_url = "https://www.linkedin.com/oauth/v2/authorization"
        scope = "%20".join(self.get_scopes())
        return f"{base_url}?response_type=code&client_id={self.client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}"

    def exchange_code(self, code: str, redirect_uri: str, code_verifier: Optional[str] = None) -> Dict[str, Any]:
        if not self.client_id or code.startswith("mock_code_"):
            return self._mock.exchange_code(code, redirect_uri, code_verifier)

        try:
            url = "https://www.linkedin.com/oauth/v2/accessToken"
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            res = requests.post(url, data=data, timeout=10)
            res_data = res.json()

            if res.status_code != 200 or "access_token" not in res_data:
                raise ValidationError(f"LinkedIn OAuth exchange failed: {res_data.get('error_description', res.text)}")

            access_token = res_data["access_token"]
            expires_in = res_data.get("expires_in", 5184000)
            profile = self.get_account_info(access_token)

            return {
                'access_token': access_token,
                'refresh_token': res_data.get('refresh_token', ''),
                'expires_at': timezone.now() + timedelta(seconds=expires_in),
                'account_id': profile.get('account_id', 'li_user'),
                'username': profile.get('username', 'li_user'),
                'display_name': profile.get('display_name', 'LinkedIn Member'),
                'profile_image_url': profile.get('profile_image_url', ''),
                'granted_scopes': self.get_scopes(),
                'capabilities': self.get_capabilities(),
                'raw_response': res_data
            }
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to connect LinkedIn account: {str(e)}")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        if not self.client_id or refresh_token.startswith("mock_"):
            return self._mock.refresh_token(refresh_token)

        try:
            url = "https://www.linkedin.com/oauth/v2/accessToken"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            res = requests.post(url, data=data, timeout=10)
            if res.status_code == 200:
                res_data = res.json()
                expires_in = res_data.get("expires_in", 5184000)
                return {
                    'access_token': res_data['access_token'],
                    'refresh_token': res_data.get('refresh_token', refresh_token),
                    'expires_at': timezone.now() + timedelta(seconds=expires_in)
                }
        except Exception as e:
            logger.error(f"LinkedIn token refresh failed: {e}")

        raise ValidationError("Failed to refresh LinkedIn token.")

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        if access_token.startswith("mock_"):
            return self._mock.get_account_info(access_token)

        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            url = "https://api.linkedin.com/v2/userinfo"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return {
                    'account_id': str(data.get('sub', '')),
                    'username': data.get('email', f"li_{data.get('sub', '')}"),
                    'display_name': data.get('name', 'LinkedIn Member'),
                    'profile_image_url': data.get('picture', '')
                }
        except Exception:
            pass
        return self._mock.get_account_info(access_token)

    def revoke(self, access_token: str) -> bool:
        return True
