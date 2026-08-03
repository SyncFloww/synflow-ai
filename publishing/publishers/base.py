from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

class BasePublisher(ABC):
    """
    Abstract base class for all social media post publishers.
    Publishing operations must go through publisher abstractions.
    """
    platform_name: str = "base"

    @abstractmethod
    def publish(self, caption: str, media_urls: List[str], access_token: Optional[str] = None, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Publishes content to the platform.
        Expected return dict:
        {
            'success': bool,
            'platform_post_id': str,
            'url': str,
            'error_message': str,
            'raw_response': dict
        }
        """
        pass
