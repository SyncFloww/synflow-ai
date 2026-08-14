from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from social.capabilities import SocialCapability

class BaseSocialProvider(ABC):
    """
    Abstract Base Class for Social Media OAuth Providers.
    All provider implementations (Instagram, Facebook, LinkedIn, TikTok, X, YouTube)
    inherit from this interface.
    """
    provider_name: str = "base"

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Returns list of SocialCapability strings supported by this provider."""
        pass

    @abstractmethod
    def get_scopes(self) -> List[str]:
        """Returns list of native provider OAuth scope strings requested for default permissions."""
        pass

    @abstractmethod
    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        code_challenge: Optional[str] = None
    ) -> str:
        """Generates the provider OAuth consent screen URL."""
        pass

    @abstractmethod
    def exchange_code(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchanges authorization code for tokens and profile information.
        Must return dict with:
        {
            'access_token': str,
            'refresh_token': str,
            'expires_at': datetime or None,
            'account_id': str,
            'username': str,
            'display_name': str,
            'profile_image_url': str,
            'granted_scopes': List[str],
            'capabilities': List[str],
            'raw_response': dict
        }
        """
        pass

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refreshes expired access token using refresh_token."""
        pass

    @abstractmethod
    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        """Retrieves profile info from provider API using access token."""
        pass

    @abstractmethod
    def revoke(self, access_token: str) -> bool:
        """Revokes token access with the platform."""
        pass
