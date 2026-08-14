from enum import Enum
from typing import Dict, List, Any

class SocialCapability(str, Enum):
    PROFILE_READ = "PROFILE_READ"
    CONTENT_READ = "CONTENT_READ"
    CONTENT_PUBLISH = "CONTENT_PUBLISH"
    COMMENTS_READ = "COMMENTS_READ"
    COMMENTS_WRITE = "COMMENTS_WRITE"
    MESSAGING = "MESSAGING"
    ANALYTICS_READ = "ANALYTICS_READ"
    MEDIA_UPLOAD = "MEDIA_UPLOAD"

CAPABILITY_DESCRIPTIONS: Dict[str, str] = {
    SocialCapability.PROFILE_READ.value: "Read your public profile info, handle, display name, and avatar.",
    SocialCapability.CONTENT_READ.value: "View your published posts, feeds, and media library.",
    SocialCapability.CONTENT_PUBLISH.value: "Schedule and publish text, image, and video content directly to your account.",
    SocialCapability.COMMENTS_READ.value: "Fetch comments, replies, and reactions on your published posts.",
    SocialCapability.COMMENTS_WRITE.value: "Reply to user comments and moderate post interactions on your behalf.",
    SocialCapability.MESSAGING.value: "Receive and reply to direct messages and customer inquiries.",
    SocialCapability.ANALYTICS_READ.value: "View post engagement, audience demographics, and performance analytics.",
    SocialCapability.MEDIA_UPLOAD.value: "Upload image and video assets to the platform for scheduled publishing."
}

def get_capability_metadata(capabilities: List[str]) -> List[Dict[str, str]]:
    return [
        {
            "capability": cap,
            "description": CAPABILITY_DESCRIPTIONS.get(cap, "Access provider functionality.")
        }
        for cap in capabilities
    ]
