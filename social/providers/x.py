import os
import requests
import hashlib
import base64
import logging
from typing import Dict, Any, List, Optional
from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from social.capabilities import SocialCapability
from .base import BaseSocialProvider
from .mock import MockSocialProvider

logger = logging.getLogger(__name__)

def _generate_pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').replace('=', '')

class XOAuthProvider(BaseSocialProvider):
    """
    X (formerly Twitter) OAuth 2.0 Provider.
    Supports X API v2 OAuth 2.0 PKCE flow.
    """
    provider_name: str = "x"

    def __init__(self):
        self.client_id = os.getenv("X_CLIENT_ID") or os.getenv("TWITTER_CLIENT_ID", "")
        self.client_secret = os.getenv("X_CLIENT_SECRET") or os.getenv("TWITTER_CLIENT_SECRET", "")
        self._mock = MockSocialProvider(provider_name="x")

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
            "tweet.read",
            "tweet.write",
            "users.read",
            "offline.access"
        ]

    def get_authorization_url(self, redirect_uri: str, state: str, code_challenge: Optional[str] = None) -> str:
        if not self.client_id:
            return self._mock.get_authorization_url(redirect_uri, state, code_challenge)

        base_url = "https://twitter.com/i/oauth2/authorize"
        scope = "%20".join(self.get_scopes())
        
        challenge_param = ""
        if code_challenge:
            challenge_param = f"&code_challenge={code_challenge}&code_challenge_method=S256"
        else:
            challenge_param = "&code_challenge=plain_challenge&code_challenge_method=plain"

        return f"{base_url}?response_type=code&client_id={self.client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}{challenge_param}"

    def exchange_code(self, code: str, redirect_uri: str, code_verifier: Optional[str] = None) -> Dict[str, Any]:
        if not self.client_id or code.startswith("mock_code_"):
            return self._mock.exchange_code(code, redirect_uri, code_verifier)

        try:
            url = "https://api.twitter.com/2/oauth2/token"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "code": code,
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier or "plain_challenge"
            }
            if self.client_secret:
                data["client_secret"] = self.client_secret

            res = requests.post(url, headers=headers, data=data, timeout=10)
            res_data = res.json()

            if res.status_code != 200 or "access_token" not in res_data:
                err = res_data.get("error_description", res.text)
                raise ValidationError(f"X OAuth exchange failed: {err}")

            access_token = res_data["access_token"]
            profile = self.get_account_info(access_token)

            return {
                'access_token': access_token,
                'refresh_token': res_data.get('refresh_token', ''),
                'expires_at': timezone.now() + timedelta(seconds=res_data.get('expires_in', 7200)),
                'account_id': profile.get('account_id', 'x_user'),
                'username': profile.get('username', 'x_user'),
                'display_name': profile.get('display_name', 'X User'),
                'profile_image_url': profile.get('profile_image_url', ''),
                'granted_scopes': self.get_scopes(),
                'capabilities': self.get_capabilities(),
                'raw_response': res_data
            }
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to connect X (Twitter) account: {str(e)}")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        if not self.client_id or refresh_token.startswith("mock_"):
            return self._mock.refresh_token(refresh_token)

        try:
            url = "https://api.twitter.com/2/oauth2/token"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id
            }
            res = requests.post(url, headers=headers, data=data, timeout=10)
            if res.status_code == 200:
                res_data = res.json()
                return {
                    'access_token': res_data['access_token'],
                    'refresh_token': res_data.get('refresh_token', refresh_token),
                    'expires_at': timezone.now() + timedelta(seconds=res_data.get('expires_in', 7200))
                }
        except Exception as e:
            logger.error(f"X token refresh error: {e}")

        raise ValidationError("Failed to refresh X token.")

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        if access_token.startswith("mock_"):
            return self._mock.get_account_info(access_token)

        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            url = "https://api.twitter.com/2/users/me?user.fields=profile_image_url,username,name"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                user_data = res.json().get('data', {})
                return {
                    'account_id': str(user_data.get('id', '')),
                    'username': user_data.get('username', ''),
                    'display_name': user_data.get('name', 'X User'),
                    'profile_image_url': user_data.get('profile_image_url', '')
                }
        except Exception:
            pass
        return self._mock.get_account_info(access_token)

    def revoke(self, access_token: str) -> bool:
        if access_token.startswith("mock_"):
            return True
        try:
            url = "https://api.twitter.com/2/oauth2/revoke"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {"token": access_token, "client_id": self.client_id}
            requests.post(url, headers=headers, data=data, timeout=10)
            return True
        except Exception:
            return False
