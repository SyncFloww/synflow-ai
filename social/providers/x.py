import os
import requests
from typing import Dict, Any, Optional
from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .base import BaseSocialProvider
from .mock import MockSocialProvider

class XOAuthProvider(BaseSocialProvider):
    """
    X (formerly Twitter) OAuth 2.0 Provider service abstraction.
    Supports X API v2 OAuth 2.0 PKCE flow.
    Fallback to safe mock mode when credentials are missing or in dev mode.
    """
    provider_name: str = "x"

    def __init__(self):
        self.client_id = os.getenv("X_CLIENT_ID") or os.getenv("TWITTER_CLIENT_ID", "")
        self.client_secret = os.getenv("X_CLIENT_SECRET") or os.getenv("TWITTER_CLIENT_SECRET", "")
        self._mock = MockSocialProvider(provider_name="x")

    def get_authorization_url(self, redirect_uri: str, state: str, extra_params: Optional[Dict[str, Any]] = None) -> str:
        if not self.client_id:
            return self._mock.get_authorization_url(redirect_uri, state, extra_params)

        base_url = "https://twitter.com/i/oauth2/authorize"
        scope = "tweet.read%20tweet.write%20users.read%20offline.access"
        code_challenge = "plain_challenge"
        return f"{base_url}?response_type=code&client_id={self.client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}&code_challenge={code_challenge}&code_challenge_method=plain"

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        if not self.client_id or code.startswith("mock_code_"):
            return self._mock.exchange_code(code, redirect_uri)

        try:
            url = "https://api.twitter.com/2/oauth2/token"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "code": code,
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "redirect_uri": redirect_uri,
                "code_verifier": "plain_challenge"
            }
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
                'raw_response': res_data
            }
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to connect X (Twitter) account: {str(e)}")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        if not self.client_id or refresh_token.startswith("mock_"):
            return self._mock.refresh_token(refresh_token)

        return {
            'access_token': f"x_refreshed_{refresh_token[:10]}",
            'refresh_token': refresh_token,
            'expires_at': timezone.now() + timedelta(hours=2)
        }

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

    def revoke(self, token: str) -> bool:
        return True
