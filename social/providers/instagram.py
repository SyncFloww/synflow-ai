import os
import requests
from typing import Dict, Any, List, Optional
from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from social.capabilities import SocialCapability
from .base import BaseSocialProvider
from .mock import MockSocialProvider

class InstagramOAuthProvider(BaseSocialProvider):
    """
    Instagram OAuth Provider.
    Supports Meta Graph API / Basic Display / Instagram Business API.
    """
    provider_name: str = "instagram"

    def __init__(self):
        self.client_id = os.getenv("INSTAGRAM_CLIENT_ID", "")
        self.client_secret = os.getenv("INSTAGRAM_CLIENT_SECRET", "")
        self._mock = MockSocialProvider(provider_name="instagram")

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
            "instagram_basic",
            "instagram_content_publish",
            "instagram_manage_comments",
            "instagram_manage_insights",
            "pages_show_list",
            "pages_read_engagement"
        ]

    def get_authorization_url(self, redirect_uri: str, state: str, code_challenge: Optional[str] = None) -> str:
        if not self.client_id:
            return self._mock.get_authorization_url(redirect_uri, state, code_challenge)

        base_url = "https://www.facebook.com/v19.0/dialog/oauth"
        scope = ",".join(self.get_scopes())
        return f"{base_url}?client_id={self.client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type=code&state={state}"

    def exchange_code(self, code: str, redirect_uri: str, code_verifier: Optional[str] = None) -> Dict[str, Any]:
        if not self.client_id or code.startswith("mock_code_"):
            return self._mock.exchange_code(code, redirect_uri, code_verifier)

        try:
            url = "https://graph.facebook.com/v19.0/oauth/access_token"
            params = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": redirect_uri,
                "code": code
            }
            res = requests.get(url, params=params, timeout=10)
            res_data = res.json()

            if res.status_code != 200 or "access_token" not in res_data:
                raise ValidationError(f"Instagram OAuth exchange failed: {res_data.get('error', {}).get('message', res.text)}")

            access_token = res_data["access_token"]
            profile = self.get_account_info(access_token)

            return {
                'access_token': access_token,
                'refresh_token': res_data.get('refresh_token', ''),
                'expires_at': timezone.now() + timedelta(days=60),
                'account_id': profile.get('account_id', ''),
                'username': profile.get('username', ''),
                'display_name': profile.get('display_name', ''),
                'profile_image_url': profile.get('profile_image_url', ''),
                'granted_scopes': self.get_scopes(),
                'capabilities': self.get_capabilities(),
                'raw_response': res_data
            }
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to connect Instagram account: {str(e)}")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        if not self.client_id or refresh_token.startswith("mock_"):
            return self._mock.refresh_token(refresh_token)

        try:
            url = f"https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id={self.client_id}&client_secret={self.client_secret}&fb_exchange_token={refresh_token}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return {
                    'access_token': data['access_token'],
                    'refresh_token': data.get('access_token', refresh_token),
                    'expires_at': timezone.now() + timedelta(days=60)
                }
        except Exception as e:
            logger.error(f"Instagram token refresh failed: {e}")

        raise ValidationError("Failed to refresh Instagram token.")

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        if access_token.startswith("mock_"):
            return self._mock.get_account_info(access_token)

        try:
            url = f"https://graph.facebook.com/v19.0/me/accounts?fields=id,name,picture,instagram_business_account{{id,username,name,profile_picture_url}}&access_token={access_token}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                accounts = data.get('data', [])
                for page in accounts:
                    ig_acc = page.get('instagram_business_account')
                    if ig_acc:
                        return {
                            'account_id': str(ig_acc.get('id', '')),
                            'username': ig_acc.get('username', ''),
                            'display_name': ig_acc.get('name') or ig_acc.get('username', ''),
                            'profile_image_url': ig_acc.get('profile_picture_url', '')
                        }
        except Exception:
            pass
        return self._mock.get_account_info(access_token)

    def revoke(self, access_token: str) -> bool:
        if access_token.startswith("mock_"):
            return True
        try:
            url = f"https://graph.facebook.com/v19.0/me/permissions?access_token={access_token}"
            requests.delete(url, timeout=10)
            return True
        except Exception:
            return False
