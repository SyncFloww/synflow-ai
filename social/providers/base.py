from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone

class BaseSocialProvider(ABC):
    """
    Abstract base class for all social media OAuth providers.
    All social OAuth interactions must go through provider abstractions,
    never directly in Django views.
    """
    provider_name: str = "base"

    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str, extra_params: Optional[Dict[str, Any]] = None) -> str:
        """Generates the OAuth authorization URL for user consent."""
        pass

    @abstractmethod
    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchanges authorization code for access & refresh tokens and account info.
        Expected return dict structure:
        {
            'access_token': str,
            'refresh_token': str,
            'expires_at': datetime,
            'account_id': str,
            'username': str,
            'display_name': str,
            'profile_image_url': str,
            'raw_response': dict
        }
        """
        pass

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refreshes an expired access token using refresh_token.
        Expected return dict structure:
        {
            'access_token': str,
            'refresh_token': str,
            'expires_at': datetime
        }
        """
        pass

    @abstractmethod
    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        """
        Retrieves user account profile using access token.
        """
        pass

    @abstractmethod
    def revoke(self, token: str) -> bool:
        """
        Revokes token access with the social platform.
        """
        pass
