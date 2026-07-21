import uuid
from datetime import timedelta
from django.utils import timezone

class OAuthProviderInterface:
    """
    Interface for OAuth providers to support connecting and fetching social account info.
    """
    def get_authorization_url(self, callback_url: str) -> str:
        raise NotImplementedError

    def exchange_code_for_token(self, code: str, callback_url: str) -> dict:
        raise NotImplementedError

    def fetch_user_profile(self, access_token: str) -> dict:
        raise NotImplementedError


class MockOAuthProvider(OAuthProviderInterface):
    """
    Mock provider for Phase 1 to simulate social connection workflows.
    """
    def __init__(self, platform_name="mock"):
        self.platform_name = platform_name

    def get_authorization_url(self, callback_url: str) -> str:
        # Simulate returning a URL to redirect the user to the provider
        return f"https://mockprovider.com/oauth/authorize?redirect_uri={callback_url}&response_type=code"

    def exchange_code_for_token(self, code: str, callback_url: str) -> dict:
        # Simulate exchanging auth code for tokens
        if code == "invalid_code":
            raise ValueError("Invalid authorization code")
            
        return {
            "access_token": f"mock_access_token_{uuid.uuid4()}",
            "refresh_token": f"mock_refresh_token_{uuid.uuid4()}",
            "expires_in": 3600,  # 1 hour
            "scopes": ["read_profile", "publish_content"]
        }

    def fetch_user_profile(self, access_token: str) -> dict:
        # Simulate fetching user profile
        if not access_token.startswith("mock_access_token"):
            raise ValueError("Invalid access token")
            
        return {
            "id": f"mock_user_{uuid.uuid4().hex[:8]}",
            "username": "mock_user",
            "profile_url": "https://mockprovider.com/mock_user",
            "metadata": {
                "followers": 1500,
                "avatar": "https://mockprovider.com/mock_user/avatar.jpg"
            }
        }
