import time
from typing import Dict, Any, List, Optional
from .base import BasePublisher

class TikTokPublisher(BasePublisher):
    platform_name: str = "tiktok"

    def publish(self, caption: str, media_urls: List[str], access_token: Optional[str] = None, account_id: Optional[str] = None) -> Dict[str, Any]:
        timestamp = int(time.time())
        return {
            'success': True,
            'platform_post_id': f"tiktok_v_{timestamp}",
            'url': f"https://tiktok.com/@user/video/{timestamp}",
            'error_message': '',
            'raw_response': {'publish_id': f"tiktok_v_{timestamp}"}
        }
