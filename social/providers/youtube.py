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

class YouTubeOAuthProvider(BaseSocialProvider):
    """
    YouTube (Google) OAuth Provider.
    Supports YouTube Data API v3 OAuth 2.0.
    """
    provider_name: str = "youtube"

    def __init__(self):
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID", "")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "")
        self._mock = MockSocialProvider(provider_name="youtube")

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
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.force-ssl",
            "https://www.googleapis.com/auth/yt-analytics.readonly"
        ]

    def get_authorization_url(self, redirect_uri: str, state: str, code_challenge: Optional[str] = None) -> str:
        if not self.client_id:
            return self._mock.get_authorization_url(redirect_uri, state, code_challenge)

        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        scope = " ".join(self.get_scopes())
        return f"{base_url}?response_type=code&client_id={self.client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}&access_type=offline&prompt=consent"

    def exchange_code(self, code: str, redirect_uri: str, code_verifier: Optional[str] = None) -> Dict[str, Any]:
        if not self.client_id or code.startswith("mock_code_"):
            return self._mock.exchange_code(code, redirect_uri, code_verifier)

        try:
            url = "https://oauth2.googleapis.com/token"
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
                raise ValidationError(f"YouTube OAuth exchange failed: {res_data.get('error_description', res.text)}")

            access_token = res_data["access_token"]
            expires_in = res_data.get("expires_in", 3600)
            profile = self.get_account_info(access_token)

            return {
                'access_token': access_token,
                'refresh_token': res_data.get('refresh_token', ''),
                'expires_at': timezone.now() + timedelta(seconds=expires_in),
                'account_id': profile.get('account_id', 'yt_channel'),
                'username': profile.get('username', 'yt_channel'),
                'display_name': profile.get('display_name', 'YouTube Channel'),
                'profile_image_url': profile.get('profile_image_url', ''),
                'granted_scopes': self.get_scopes(),
                'capabilities': self.get_capabilities(),
                'raw_response': res_data
            }
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to connect YouTube account: {str(e)}")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        if not self.client_id or refresh_token.startswith("mock_"):
            return self._mock.refresh_token(refresh_token)

        try:
            url = "https://oauth2.googleapis.com/token"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            res = requests.post(url, data=data, timeout=10)
            res_data = res.json()
            if res.status_code == 200 and "access_token" in res_data:
                return {
                    'access_token': res_data['access_token'],
                    'refresh_token': res_data.get('refresh_token', refresh_token),
                    'expires_at': timezone.now() + timedelta(seconds=res_data.get('expires_in', 3600))
                }
        except Exception as e:
            logger.error(f"YouTube token refresh error: {e}")

        raise ValidationError("Failed to refresh YouTube token.")

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        if access_token.startswith("mock_"):
            return self._mock.get_account_info(access_token)

        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            url = "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                items = data.get('items', [])
                if items:
                    channel = items[0]
                    snippet = channel.get('snippet', {})
                    return {
                        'account_id': str(channel.get('id', '')),
                        'username': snippet.get('customUrl', f"channel_{channel.get('id')}"),
                        'display_name': snippet.get('title', 'YouTube Channel'),
                        'profile_image_url': snippet.get('thumbnails', {}).get('default', {}).get('url', '')
                    }
        except Exception:
            pass
        return self._mock.get_account_info(access_token)

    def revoke(self, access_token: str) -> bool:
        if access_token and not access_token.startswith("mock_"):
            try:
                url = f"https://oauth2.googleapis.com/revoke?token={access_token}"
                requests.post(url, timeout=5)
            except Exception:
                pass
        return True
